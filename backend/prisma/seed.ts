import { PrismaClient, FinancialDomain, DecisionType, DecisionState } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  console.log('Seeding database...');

  const decisionCase = await prisma.financialDecisionCase.create({
    data: {
      title: 'Cloud Infrastructure Migration – CapEx to OpEx Conversion',
      description:
        'Evaluate migrating on-premise data center to cloud infrastructure, converting a CapEx-heavy model to an OpEx subscription model. This impacts balance sheet depreciation, cash flow timing, and IT operational agility.',
      financialDomain: FinancialDomain.CAPEX,
      decisionType: DecisionType.INVESTMENT,
      state: DecisionState.DRAFT,
      impactScore: 4,
      externalAgentsPresent: true,
      scenarioAnalysisRequired: true,
      gameTheoryTriggered: false,
      createdById: 'admin',
      assumptions: {
        create: [
          {
            description: 'Cloud costs will grow at 8% per annum in line with usage growth',
            source: 'AWS pricing model Q4 2024',
            confidence: 0.8,
            validatedAt: new Date('2024-11-01'),
          },
          {
            description: 'On-premise hardware refresh cycle would require $4.2M CapEx in Year 1',
            source: 'IT Asset Management Report',
            confidence: 0.9,
            validatedAt: new Date('2024-10-15'),
          },
          {
            description: 'Migration can be completed within 18 months with minimal service disruption',
            source: 'Cloud Migration Feasibility Study',
            confidence: 0.7,
            validatedAt: new Date('2024-11-10'),
          },
          {
            description: 'Tax treatment of cloud OpEx provides 30% immediate deduction versus 5-year depreciation for CapEx',
            source: 'Tax Advisory Memorandum',
            confidence: 0.95,
            validatedAt: new Date('2024-10-20'),
          },
        ],
      },
      risks: {
        create: [
          {
            description: 'Vendor lock-in with primary cloud provider limiting future negotiation leverage',
            probability: 0.6,
            impactScore: 4,
            mitigationPlan: 'Adopt multi-cloud architecture and containerization to enable portability',
            residualRisk: 0.2,
          },
          {
            description: 'Cost overrun during migration phase due to underestimated complexity',
            probability: 0.45,
            impactScore: 3,
            mitigationPlan: 'Fixed-price migration contract with SLA penalties; phased rollout',
            residualRisk: 0.15,
          },
          {
            description: 'Data sovereignty and compliance risk for EU-regulated data',
            probability: 0.3,
            impactScore: 5,
            mitigationPlan: 'Select EU-region cloud zones and implement data residency controls',
            residualRisk: 0.1,
          },
          {
            description: 'Internal resistance from IT staff fearing role elimination',
            probability: 0.5,
            impactScore: 2,
            mitigationPlan: 'Change management program and upskilling investment for cloud-native roles',
            residualRisk: 0.2,
          },
        ],
      },
      metricsImpacted: {
        create: [
          {
            metricName: 'Capital Expenditure',
            currentValue: 4200000,
            projectedValue: 0,
            unit: 'USD',
            timeHorizonMonths: 12,
          },
          {
            metricName: 'Operating Expenditure (IT)',
            currentValue: 800000,
            projectedValue: 2100000,
            unit: 'USD',
            timeHorizonMonths: 12,
          },
          {
            metricName: 'EBITDA Impact',
            currentValue: 0,
            projectedValue: -1300000,
            unit: 'USD',
            timeHorizonMonths: 12,
          },
          {
            metricName: 'Net Present Value (5-Year)',
            currentValue: 0,
            projectedValue: 3800000,
            unit: 'USD',
            timeHorizonMonths: 60,
          },
          {
            metricName: 'IT Agility Index',
            currentValue: 42,
            projectedValue: 78,
            unit: 'Score (0-100)',
            timeHorizonMonths: 18,
          },
        ],
      },
    },
  });

  console.log(`Created case: ${decisionCase.id} - ${decisionCase.title}`);

  await prisma.decision.create({
    data: {
      caseId: decisionCase.id,
      recommendation: `**RECOMMENDATION: PROCEED WITH PHASED CLOUD MIGRATION**

**Situation:** The organisation faces a $4.2M hardware refresh decision at a time when cloud infrastructure maturity and favourable tax treatment make the OpEx conversion strategically advantageous.

**Complication:** While the 5-year NPV is positive at $3.8M, the near-term EBITDA impact of -$1.3M in Year 1 requires board-level framing and covenant review. Additionally, vendor lock-in and data sovereignty risks require deliberate architectural guardrails.

**Resolution:** Approve the phased cloud migration programme under the following conditions:
1. Multi-cloud architecture mandate to preserve negotiation leverage
2. EU data residency controls implemented before data migration commences
3. Fixed-price migration contract with SLA penalties
4. CFO quarterly review gates at 6, 12, and 18 months
5. Change management budget of $150K allocated for IT staff reskilling

**Financial Rationale:** The 30% immediate OpEx tax deduction generates $630K in Year 1 tax benefit, partially offsetting the EBITDA impact. By Year 3, total cost of ownership is 22% lower than the on-premise alternative. The balance sheet improvement (removal of $4.2M asset and associated depreciation) strengthens the company's asset-light positioning for potential future M&A activity.`,
      recommendedOption: 'PROCEED_PHASED_MIGRATION',
      executiveDecision: 'PROCEED_PHASED_MIGRATION',
      divergenceFlag: false,
      gameTheoryAnalysis: {
        players: ['CFO / Finance', 'CTO / IT', 'Cloud Vendor (AWS)', 'Regulator (GDPR Authority)'],
        strategySpace: {
          'CFO / Finance': ['Approve Full Migration', 'Approve Phased Migration', 'Defer Decision'],
          'CTO / IT': ['Multi-cloud Architecture', 'Single-vendor Architecture', 'Hybrid Retain On-Prem'],
          'Cloud Vendor (AWS)': ['Competitive Pricing', 'Lock-in Incentives', 'Neutral'],
          'Regulator (GDPR Authority)': ['Enforce Data Residency', 'Issue Guidance Only', 'No Action'],
        },
        payoffMatrix: {
          description: 'Payoff scores (0-10) under dominant strategy combination',
          dominantStrategyCombination: {
            'CFO / Finance': 'Approve Phased Migration',
            'CTO / IT': 'Multi-cloud Architecture',
            'Cloud Vendor (AWS)': 'Lock-in Incentives',
            'Regulator (GDPR Authority)': 'Enforce Data Residency',
          },
          payoffs: {
            'CFO / Finance': 7,
            'CTO / IT': 8,
            'Cloud Vendor (AWS)': 6,
            'Regulator (GDPR Authority)': 9,
          },
        },
        equilibrium: 'Nash Equilibrium at (Phased Migration, Multi-cloud, Lock-in Incentives, Enforce Data Residency). No player has unilateral incentive to deviate.',
        strategicRiskExposure: 'Moderate. Primary risk is vendor attempting to shift equilibrium through aggressive lock-in pricing post-migration. Counter-strategy: contractual portability clauses and annual competitive tender.',
      },
      decidedAt: new Date(),
      decidedById: 'admin',
    },
  });

  await prisma.stateTransition.create({
    data: {
      caseId: decisionCase.id,
      fromState: DecisionState.DRAFT,
      toState: DecisionState.DRAFT,
      triggeredById: 'admin',
      reason: 'Initial case creation',
    },
  });

  await prisma.auditLog.create({
    data: {
      caseId: decisionCase.id,
      action: 'CASE_CREATED',
      performedById: 'admin',
      metadata: { title: decisionCase.title, domain: decisionCase.financialDomain },
    },
  });

  console.log('Seeding complete.');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
