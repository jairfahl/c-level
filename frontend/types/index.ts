export type FinancialDomain =
  | 'CAPEX'
  | 'OPEX'
  | 'REVENUE'
  | 'TREASURY'
  | 'RISK_MANAGEMENT'
  | 'COMPLIANCE'
  | 'STRATEGY'
  | 'M_AND_A';

export type DecisionType =
  | 'INVESTMENT'
  | 'DIVESTMENT'
  | 'FINANCING'
  | 'OPERATIONAL_CHANGE'
  | 'RISK_MITIGATION'
  | 'STRATEGIC_PARTNERSHIP'
  | 'ACQUISITION'
  | 'RESTRUCTURING';

export type DecisionState =
  | 'DRAFT'
  | 'CLASSIFIED'
  | 'STRUCTURED'
  | 'ANALYZED'
  | 'RECOMMENDED'
  | 'DECIDED'
  | 'UNDER_REVIEW'
  | 'CLOSED';

export interface FinancialAssumption {
  id: string;
  description: string;
  source: string;
  confidence: number;
  validatedAt?: string;
}

export interface FinancialRisk {
  id: string;
  description: string;
  probability: number;
  impactScore: number;
  mitigationPlan?: string;
  residualRisk?: number;
}

export interface FinancialMetricImpacted {
  id: string;
  metricName: string;
  currentValue: number;
  projectedValue: number;
  unit: string;
  timeHorizonMonths: number;
}

export interface Decision {
  id: string;
  recommendation: string;
  recommendedOption: string;
  executiveDecision?: string;
  divergenceFlag: boolean;
  divergenceJustification?: string;
  gameTheoryAnalysis?: GameTheoryAnalysis;
  decidedAt?: string;
}

export interface GameTheoryAnalysis {
  players?: string[];
  strategySpace?: Record<string, string[]>;
  payoffMatrix?: Record<string, unknown>;
  equilibriumEstimation?: string;
  strategicRiskExposure?: string;
}

export interface Review {
  id: string;
  actualOutcome: string;
  varianceAnalysis: string;
  lessonsLearned: string;
  reviewedAt: string;
}

export interface StateTransition {
  id: string;
  fromState: DecisionState;
  toState: DecisionState;
  triggeredById: string;
  reason?: string;
  transitionedAt: string;
}

export interface AuditLog {
  id: string;
  action: string;
  performedById: string;
  metadata?: Record<string, unknown>;
  performedAt: string;
}

export interface FinancialDecisionCase {
  id: string;
  title: string;
  description: string;
  financialDomain: FinancialDomain;
  decisionType: DecisionType;
  state: DecisionState;
  impactScore: number;
  externalAgentsPresent: boolean;
  scenarioAnalysisRequired: boolean;
  gameTheoryTriggered: boolean;
  createdById: string;
  createdAt: string;
  updatedAt: string;
  assumptions?: FinancialAssumption[];
  risks?: FinancialRisk[];
  metricsImpacted?: FinancialMetricImpacted[];
  decisions?: Decision[];
  reviews?: Review[];
  stateTransitions?: StateTransition[];
  auditLogs?: AuditLog[];
}
