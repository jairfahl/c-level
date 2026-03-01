import {
  Injectable,
  NotFoundException,
  UnprocessableEntityException,
} from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { LlmService } from '../llm/llm.service';
import { StateMachineService } from './state-machine.service';
import { DecisionState } from '@prisma/client';
import { CreateCaseDto } from './dto/create-case.dto';
import { ClassifyCaseDto } from './dto/classify-case.dto';
import { StructureCaseDto } from './dto/structure-case.dto';
import { AnalyzeCaseDto } from './dto/analyze-case.dto';
import { RecommendCaseDto } from './dto/recommend-case.dto';
import { DecideCaseDto } from './dto/decide-case.dto';
import { ReviewCaseDto } from './dto/review-case.dto';

@Injectable()
export class FinancialDecisionCasesService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly llm: LlmService,
    private readonly stateMachine: StateMachineService,
  ) {}

  async create(dto: CreateCaseDto, userId: string) {
    const caseRecord = await this.prisma.financialDecisionCase.create({
      data: {
        title: dto.title,
        description: dto.description,
        financialDomain: dto.financialDomain,
        decisionType: dto.decisionType,
        impactScore: dto.impactScore,
        externalAgentsPresent: dto.externalAgentsPresent ?? false,
        scenarioAnalysisRequired: dto.scenarioAnalysisRequired ?? false,
        createdById: userId,
      },
    });

    await this.prisma.auditLog.create({
      data: {
        caseId: caseRecord.id,
        action: 'CASE_CREATED',
        performedById: userId,
        metadata: { title: caseRecord.title, domain: caseRecord.financialDomain },
      },
    });

    return caseRecord;
  }

  async findAll() {
    return this.prisma.financialDecisionCase.findMany({
      include: {
        assumptions: true,
        risks: true,
        metricsImpacted: true,
        decisions: true,
        reviews: true,
        stateTransitions: { orderBy: { transitionedAt: 'desc' }, take: 5 },
      },
      orderBy: { createdAt: 'desc' },
    });
  }

  async findOne(id: string) {
    const record = await this.prisma.financialDecisionCase.findUnique({
      where: { id },
      include: {
        assumptions: true,
        risks: true,
        metricsImpacted: true,
        decisions: true,
        reviews: true,
        stateTransitions: { orderBy: { transitionedAt: 'desc' } },
        auditLogs: { orderBy: { performedAt: 'desc' } },
      },
    });

    if (!record) {
      throw new NotFoundException(`Case ${id} not found`);
    }

    return record;
  }

  async classify(id: string, dto: ClassifyCaseDto, userId: string) {
    const record = await this.findOne(id);
    this.stateMachine.validateTransition(record.state, DecisionState.CLASSIFIED);

    return this.prisma.$transaction(async (tx) => {
      const updated = await tx.financialDecisionCase.update({
        where: { id },
        data: {
          financialDomain: dto.financialDomain,
          decisionType: dto.decisionType,
          state: DecisionState.CLASSIFIED,
        },
        include: { assumptions: true, risks: true, metricsImpacted: true, decisions: true },
      });

      await tx.stateTransition.create({
        data: {
          caseId: id,
          fromState: record.state,
          toState: DecisionState.CLASSIFIED,
          triggeredById: userId,
          reason: dto.classificationRationale,
        },
      });

      await tx.auditLog.create({
        data: {
          caseId: id,
          action: 'STATE_TRANSITION',
          performedById: userId,
          metadata: {
            from: record.state,
            to: DecisionState.CLASSIFIED,
            rationale: dto.classificationRationale,
          },
        },
      });

      return updated;
    });
  }

  async structure(id: string, dto: StructureCaseDto, userId: string) {
    const record = await this.findOne(id);
    this.stateMachine.validateTransition(record.state, DecisionState.STRUCTURED);

    if (dto.assumptions.length < 3) {
      throw new UnprocessableEntityException(
        'At least 3 assumptions are required before structuring a case',
      );
    }

    return this.prisma.$transaction(async (tx) => {
      // Replace existing assumptions and risks
      await tx.financialAssumption.deleteMany({ where: { caseId: id } });
      await tx.financialRisk.deleteMany({ where: { caseId: id } });

      await tx.financialAssumption.createMany({
        data: dto.assumptions.map((a) => ({
          caseId: id,
          description: a.description,
          source: a.source,
          confidence: a.confidence,
        })),
      });

      await tx.financialRisk.createMany({
        data: dto.risks.map((r) => ({
          caseId: id,
          description: r.description,
          probability: r.probability,
          impactScore: r.impactScore,
          mitigationPlan: r.mitigationPlan,
          residualRisk: r.residualRisk,
        })),
      });

      const updated = await tx.financialDecisionCase.update({
        where: { id },
        data: { state: DecisionState.STRUCTURED },
        include: { assumptions: true, risks: true, metricsImpacted: true, decisions: true },
      });

      await tx.stateTransition.create({
        data: {
          caseId: id,
          fromState: record.state,
          toState: DecisionState.STRUCTURED,
          triggeredById: userId,
          reason: `Structured with ${dto.assumptions.length} assumptions and ${dto.risks.length} risks`,
        },
      });

      await tx.auditLog.create({
        data: {
          caseId: id,
          action: 'STATE_TRANSITION',
          performedById: userId,
          metadata: {
            from: record.state,
            to: DecisionState.STRUCTURED,
            assumptionsCount: dto.assumptions.length,
            risksCount: dto.risks.length,
          },
        },
      });

      return updated;
    });
  }

  async analyze(id: string, dto: AnalyzeCaseDto, userId: string) {
    const record = await this.findOne(id);
    this.stateMachine.validateTransition(record.state, DecisionState.ANALYZED);

    if (record.risks.length < 3) {
      throw new UnprocessableEntityException(
        'At least 3 risks must be documented before analysing a case',
      );
    }

    if (
      record.impactScore >= 4 &&
      record.scenarioAnalysisRequired &&
      (!dto.metricsImpacted || dto.metricsImpacted.length === 0) &&
      record.metricsImpacted.length === 0
    ) {
      throw new UnprocessableEntityException(
        'High-impact cases with scenario analysis required must have at least one metric impacted',
      );
    }

    // Trigger game theory if external agents present and impact >= 4
    const shouldTriggerGameTheory = record.externalAgentsPresent && record.impactScore >= 4;

    return this.prisma.$transaction(async (tx) => {
      if (dto.metricsImpacted && dto.metricsImpacted.length > 0) {
        await tx.financialMetricImpacted.deleteMany({ where: { caseId: id } });
        await tx.financialMetricImpacted.createMany({
          data: dto.metricsImpacted.map((m) => ({
            caseId: id,
            metricName: m.metricName,
            currentValue: m.currentValue,
            projectedValue: m.projectedValue,
            unit: m.unit,
            timeHorizonMonths: m.timeHorizonMonths,
          })),
        });
      }

      const updated = await tx.financialDecisionCase.update({
        where: { id },
        data: {
          state: DecisionState.ANALYZED,
          gameTheoryTriggered: shouldTriggerGameTheory,
        },
        include: { assumptions: true, risks: true, metricsImpacted: true, decisions: true },
      });

      await tx.stateTransition.create({
        data: {
          caseId: id,
          fromState: record.state,
          toState: DecisionState.ANALYZED,
          triggeredById: userId,
          reason: shouldTriggerGameTheory
            ? 'Analysis complete; game theory triggered due to external agents and high impact'
            : 'Analysis complete',
        },
      });

      await tx.auditLog.create({
        data: {
          caseId: id,
          action: 'STATE_TRANSITION',
          performedById: userId,
          metadata: {
            from: record.state,
            to: DecisionState.ANALYZED,
            gameTheoryTriggered: shouldTriggerGameTheory,
            metricsCount: dto.metricsImpacted?.length ?? 0,
          },
        },
      });

      return updated;
    });
  }

  async recommend(id: string, dto: RecommendCaseDto, userId: string) {
    const record = await this.findOne(id);
    this.stateMachine.validateTransition(record.state, DecisionState.RECOMMENDED);

    if (record.impactScore >= 4) {
      if (!record.scenarioAnalysisRequired) {
        throw new UnprocessableEntityException(
          'Scenario analysis must be marked as required for high-impact cases (impactScore >= 4)',
        );
      }
      if (record.metricsImpacted.length === 0) {
        throw new UnprocessableEntityException(
          'At least one metric must be impacted for high-impact cases (impactScore >= 4)',
        );
      }
    }

    const caseWithRelations = await this.prisma.financialDecisionCase.findUnique({
      where: { id },
      include: { assumptions: true, risks: true, metricsImpacted: true },
    });

    const { recommendation, recommendedOption } = await this.llm.generateRecommendation({
      ...caseWithRelations,
      additionalContext: dto.additionalContext,
    });

    let gameTheoryAnalysis = null;
    if (record.gameTheoryTriggered) {
      gameTheoryAnalysis = await this.llm.generateGameTheoryAnalysis(caseWithRelations);
    }

    return this.prisma.$transaction(async (tx) => {
      await tx.decision.deleteMany({ where: { caseId: id } });

      const decision = await tx.decision.create({
        data: {
          caseId: id,
          recommendation,
          recommendedOption,
          gameTheoryAnalysis: gameTheoryAnalysis ?? undefined,
        },
      });

      const updated = await tx.financialDecisionCase.update({
        where: { id },
        data: { state: DecisionState.RECOMMENDED },
        include: { assumptions: true, risks: true, metricsImpacted: true, decisions: true },
      });

      await tx.stateTransition.create({
        data: {
          caseId: id,
          fromState: record.state,
          toState: DecisionState.RECOMMENDED,
          triggeredById: userId,
          reason: `LLM recommendation generated: ${recommendedOption}`,
        },
      });

      await tx.auditLog.create({
        data: {
          caseId: id,
          action: 'STATE_TRANSITION',
          performedById: userId,
          metadata: {
            from: record.state,
            to: DecisionState.RECOMMENDED,
            recommendedOption,
            decisionId: decision.id,
            gameTheoryIncluded: gameTheoryAnalysis !== null,
          },
        },
      });

      return updated;
    });
  }

  async decide(id: string, dto: DecideCaseDto, userId: string) {
    const record = await this.findOne(id);
    this.stateMachine.validateTransition(record.state, DecisionState.DECIDED);

    if (!record.decisions || record.decisions.length === 0) {
      throw new UnprocessableEntityException(
        'A recommendation must exist before an executive decision can be recorded',
      );
    }

    const latestDecision = record.decisions[record.decisions.length - 1];
    const divergenceFlag = dto.executiveDecision !== latestDecision.recommendedOption;

    if (divergenceFlag && !dto.divergenceJustification) {
      throw new UnprocessableEntityException(
        'A divergence justification is required when the executive decision differs from the recommendation',
      );
    }

    return this.prisma.$transaction(async (tx) => {
      await tx.decision.update({
        where: { id: latestDecision.id },
        data: {
          executiveDecision: dto.executiveDecision,
          divergenceFlag,
          divergenceJustification: divergenceFlag ? dto.divergenceJustification : null,
          decidedAt: new Date(),
          decidedById: userId,
        },
      });

      const updated = await tx.financialDecisionCase.update({
        where: { id },
        data: { state: DecisionState.DECIDED },
        include: { assumptions: true, risks: true, metricsImpacted: true, decisions: true },
      });

      await tx.stateTransition.create({
        data: {
          caseId: id,
          fromState: record.state,
          toState: DecisionState.DECIDED,
          triggeredById: userId,
          reason: divergenceFlag
            ? `Executive divergence from recommendation: ${dto.divergenceJustification}`
            : `Executive decision aligned with recommendation: ${dto.executiveDecision}`,
        },
      });

      await tx.auditLog.create({
        data: {
          caseId: id,
          action: 'STATE_TRANSITION',
          performedById: userId,
          metadata: {
            from: record.state,
            to: DecisionState.DECIDED,
            executiveDecision: dto.executiveDecision,
            recommendedOption: latestDecision.recommendedOption,
            divergenceFlag,
          },
        },
      });

      return updated;
    });
  }

  async review(id: string, dto: ReviewCaseDto, userId: string) {
    const record = await this.findOne(id);
    this.stateMachine.validateTransition(record.state, DecisionState.UNDER_REVIEW);

    return this.prisma.$transaction(async (tx) => {
      await tx.review.create({
        data: {
          caseId: id,
          actualOutcome: dto.actualOutcome,
          varianceAnalysis: dto.varianceAnalysis,
          lessonsLearned: dto.lessonsLearned,
          reviewedAt: new Date(dto.reviewedAt),
          reviewedById: userId,
        },
      });

      const updated = await tx.financialDecisionCase.update({
        where: { id },
        data: { state: DecisionState.UNDER_REVIEW },
        include: { assumptions: true, risks: true, metricsImpacted: true, decisions: true, reviews: true },
      });

      await tx.stateTransition.create({
        data: {
          caseId: id,
          fromState: record.state,
          toState: DecisionState.UNDER_REVIEW,
          triggeredById: userId,
          reason: 'Post-decision review submitted',
        },
      });

      await tx.auditLog.create({
        data: {
          caseId: id,
          action: 'STATE_TRANSITION',
          performedById: userId,
          metadata: {
            from: record.state,
            to: DecisionState.UNDER_REVIEW,
            reviewedAt: dto.reviewedAt,
          },
        },
      });

      return updated;
    });
  }
}
