import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Numeric, Boolean, DateTime,
    ForeignKey, Text, Enum as SAEnum, func, Computed
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.enums import (
    FinancialDomain, DecisionState, DecisionType, TimeHorizon, FrameworkType
)


class FinancialDecisionCase(Base):
    __tablename__ = "financial_decision_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    financial_domain = Column(SAEnum(FinancialDomain, name="financial_domain"), nullable=False)
    impact_score = Column(Integer)
    financial_exposure = Column(Numeric(18, 2), nullable=False)
    time_horizon = Column(SAEnum(TimeHorizon, name="time_horizon_type"), nullable=True)
    external_agents_present = Column(Boolean, nullable=False, default=False)
    decision_type = Column(SAEnum(DecisionType, name="decision_type"), nullable=False)
    framework_selected = Column(SAEnum(FrameworkType, name="framework_type"), nullable=True)
    state = Column(SAEnum(DecisionState, name="decision_state"), nullable=False, default=DecisionState.DRAFT)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assumptions = relationship("FinancialAssumption", back_populates="case", cascade="all, delete-orphan")
    risks = relationship("FinancialRisk", back_populates="case", cascade="all, delete-orphan")
    metrics_impacted = relationship("FinancialMetricImpacted", back_populates="case", cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="case", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="case", cascade="all, delete-orphan")
    state_transitions = relationship("StateTransition", back_populates="case", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="case", cascade="all, delete-orphan")

    @property
    def scenario_required(self) -> bool:
        return self.impact_score is not None and self.impact_score >= 4


class FinancialAssumption(Base):
    __tablename__ = "financial_assumptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_case_id = Column(UUID(as_uuid=True), ForeignKey("financial_decision_cases.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    is_implicit = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    case = relationship("FinancialDecisionCase", back_populates="assumptions")


class FinancialRisk(Base):
    __tablename__ = "financial_risks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_case_id = Column(UUID(as_uuid=True), ForeignKey("financial_decision_cases.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    materialized = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    case = relationship("FinancialDecisionCase", back_populates="risks")


class FinancialMetricImpacted(Base):
    __tablename__ = "financial_metrics_impacted"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_case_id = Column(UUID(as_uuid=True), ForeignKey("financial_decision_cases.id", ondelete="CASCADE"), nullable=False)
    metric_name = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    case = relationship("FinancialDecisionCase", back_populates="metrics_impacted")


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_case_id = Column(UUID(as_uuid=True), ForeignKey("financial_decision_cases.id", ondelete="CASCADE"), nullable=False)
    recommendation = Column(Text, nullable=False)
    executive_decision = Column(Text, nullable=True)
    divergence_flag = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    case = relationship("FinancialDecisionCase", back_populates="decisions")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_case_id = Column(UUID(as_uuid=True), ForeignKey("financial_decision_cases.id", ondelete="CASCADE"), nullable=False)
    outcome_summary = Column(Text, nullable=True)
    forecast_accuracy_score = Column(Integer, nullable=True)
    risk_realization_rate = Column(Numeric(5, 2), nullable=True)
    capital_allocation_efficiency_score = Column(Numeric(5, 2), nullable=True)
    divergence_outcome_flag = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    case = relationship("FinancialDecisionCase", back_populates="reviews")


class StateTransition(Base):
    __tablename__ = "state_transitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_case_id = Column(UUID(as_uuid=True), ForeignKey("financial_decision_cases.id", ondelete="CASCADE"), nullable=False)
    from_state = Column(SAEnum(DecisionState, name="decision_state"), nullable=True)
    to_state = Column(SAEnum(DecisionState, name="decision_state"), nullable=False)
    transitioned_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    triggered_by = Column(Text, nullable=True)

    case = relationship("FinancialDecisionCase", back_populates="state_transitions")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_case_id = Column(UUID(as_uuid=True), ForeignKey("financial_decision_cases.id", ondelete="CASCADE"), nullable=True)
    action = Column(Text, nullable=False)
    payload = Column(JSONB, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    case = relationship("FinancialDecisionCase", back_populates="audit_logs")


class FinancialHeuristic(Base):
    __tablename__ = "financial_heuristics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_type = Column(SAEnum(DecisionType, name="decision_type"), nullable=False)
    financial_domain = Column(SAEnum(FinancialDomain, name="financial_domain"), nullable=False)
    heuristic_key = Column(Text, nullable=False)
    heuristic_value = Column(JSONB, nullable=False)
    source_case_id = Column(UUID(as_uuid=True), ForeignKey("financial_decision_cases.id", ondelete="SET NULL"), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
