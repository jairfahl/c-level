"""Initial CFO Mentor schema v2

Revision ID: 001
Revises: 
Create Date: 2026-03-01

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── ENUMs ──────────────────────────────────────────────────────────────
    op.execute("CREATE TYPE financial_domain AS ENUM ('planning','reporting','treasury','funding','risk')")
    op.execute("CREATE TYPE decision_state AS ENUM ('DRAFT','CLASSIFIED','STRUCTURED','ANALYZED','RECOMMENDED','DECIDED','UNDER_REVIEW','CLOSED')")
    op.execute("CREATE TYPE decision_type AS ENUM ('budget_adjustment','forecast_revision','capital_allocation','debt_structuring','liquidity_management','risk_hedging','cost_reduction','investment_evaluation')")
    op.execute("CREATE TYPE time_horizon_type AS ENUM ('short','medium','long')")
    op.execute("CREATE TYPE framework_type AS ENUM ('pdca','scenario_analysis','game_theory','trade_off','risk_matrix','capital_allocation')")

    # ── financial_decision_cases ───────────────────────────────────────────
    op.create_table(
        "financial_decision_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("financial_domain", sa.Enum("planning","reporting","treasury","funding","risk", name="financial_domain", create_type=False), nullable=False),
        sa.Column("impact_score", sa.Integer, sa.CheckConstraint("impact_score BETWEEN 1 AND 5")),
        sa.Column("financial_exposure", sa.Numeric(18,2), nullable=False),
        sa.Column("time_horizon", sa.Enum("short","medium","long", name="time_horizon_type", create_type=False), nullable=True),
        sa.Column("external_agents_present", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("decision_type", sa.Enum("budget_adjustment","forecast_revision","capital_allocation","debt_structuring","liquidity_management","risk_hedging","cost_reduction","investment_evaluation", name="decision_type", create_type=False), nullable=False),
        sa.Column("framework_selected", sa.Enum("pdca","scenario_analysis","game_theory","trade_off","risk_matrix","capital_allocation", name="framework_type", create_type=False), nullable=True),
        sa.Column("state", sa.Enum("DRAFT","CLASSIFIED","STRUCTURED","ANALYZED","RECOMMENDED","DECIDED","UNDER_REVIEW","CLOSED", name="decision_state", create_type=False), nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # ── financial_assumptions ──────────────────────────────────────────────
    op.create_table(
        "financial_assumptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("decision_case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("financial_decision_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("is_implicit", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # ── financial_risks ────────────────────────────────────────────────────
    op.create_table(
        "financial_risks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("decision_case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("financial_decision_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("materialized", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # ── financial_metrics_impacted ─────────────────────────────────────────
    op.create_table(
        "financial_metrics_impacted",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("decision_case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("financial_decision_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("metric_name", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # ── decisions ─────────────────────────────────────────────────────────
    op.create_table(
        "decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("decision_case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("financial_decision_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recommendation", sa.Text, nullable=False),
        sa.Column("executive_decision", sa.Text, nullable=True),
        sa.Column("divergence_flag", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # ── reviews ───────────────────────────────────────────────────────────
    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("decision_case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("financial_decision_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("outcome_summary", sa.Text, nullable=True),
        sa.Column("forecast_accuracy_score", sa.Integer, sa.CheckConstraint("forecast_accuracy_score BETWEEN 1 AND 10")),
        sa.Column("risk_realization_rate", sa.Numeric(5,2), sa.CheckConstraint("risk_realization_rate BETWEEN 0 AND 100")),
        sa.Column("capital_allocation_efficiency_score", sa.Numeric(5,2), sa.CheckConstraint("capital_allocation_efficiency_score BETWEEN 0 AND 100")),
        sa.Column("divergence_outcome_flag", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # ── state_transitions ─────────────────────────────────────────────────
    op.create_table(
        "state_transitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("decision_case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("financial_decision_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_state", sa.Enum("DRAFT","CLASSIFIED","STRUCTURED","ANALYZED","RECOMMENDED","DECIDED","UNDER_REVIEW","CLOSED", name="decision_state", create_type=False), nullable=True),
        sa.Column("to_state", sa.Enum("DRAFT","CLASSIFIED","STRUCTURED","ANALYZED","RECOMMENDED","DECIDED","UNDER_REVIEW","CLOSED", name="decision_state", create_type=False), nullable=False),
        sa.Column("transitioned_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("triggered_by", sa.Text, nullable=True),
    )

    # ── audit_logs ────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("decision_case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("financial_decision_cases.id", ondelete="CASCADE"), nullable=True),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # ── financial_heuristics ──────────────────────────────────────────────
    op.create_table(
        "financial_heuristics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("decision_type", sa.Enum("budget_adjustment","forecast_revision","capital_allocation","debt_structuring","liquidity_management","risk_hedging","cost_reduction","investment_evaluation", name="decision_type", create_type=False), nullable=False),
        sa.Column("financial_domain", sa.Enum("planning","reporting","treasury","funding","risk", name="financial_domain", create_type=False), nullable=False),
        sa.Column("heuristic_key", sa.Text, nullable=False),
        sa.Column("heuristic_value", postgresql.JSONB, nullable=False),
        sa.Column("source_case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("financial_decision_cases.id", ondelete="SET NULL"), nullable=True),
        sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("decision_type", "financial_domain", "heuristic_key", name="uq_heuristics_key"),
    )

    # ── Triggers ──────────────────────────────────────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
          NEW.updated_at = NOW();
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("CREATE TRIGGER trg_fdc_updated_at BEFORE UPDATE ON financial_decision_cases FOR EACH ROW EXECUTE FUNCTION update_updated_at()")
    op.execute("CREATE TRIGGER trg_heuristics_updated_at BEFORE UPDATE ON financial_heuristics FOR EACH ROW EXECUTE FUNCTION update_updated_at()")

    # ── Indices ───────────────────────────────────────────────────────────
    op.create_index("idx_fdc_domain",    "financial_decision_cases", ["financial_domain"])
    op.create_index("idx_fdc_state",     "financial_decision_cases", ["state"])
    op.create_index("idx_fdc_type",      "financial_decision_cases", ["decision_type"])
    op.create_index("idx_assump_case",   "financial_assumptions",    ["decision_case_id"])
    op.create_index("idx_risks_case",    "financial_risks",          ["decision_case_id"])
    op.create_index("idx_metrics_case",  "financial_metrics_impacted", ["decision_case_id"])
    op.create_index("idx_decisions_case","decisions",                ["decision_case_id"])
    op.create_index("idx_reviews_case",  "reviews",                  ["decision_case_id"])
    op.create_index("idx_st_case",       "state_transitions",        ["decision_case_id"])
    op.create_index("idx_al_case",       "audit_logs",               ["decision_case_id"])
    op.create_index("idx_al_action",     "audit_logs",               ["action"])
    op.create_index("idx_heur_type",     "financial_heuristics",     ["decision_type", "financial_domain"])


def downgrade() -> None:
    # Drop indexes
    for idx in ["idx_heur_type","idx_al_action","idx_al_case","idx_st_case","idx_reviews_case",
                "idx_decisions_case","idx_metrics_case","idx_risks_case","idx_assump_case",
                "idx_fdc_type","idx_fdc_state","idx_fdc_domain"]:
        op.drop_index(idx, if_exists=True)

    # Drop triggers and function
    op.execute("DROP TRIGGER IF EXISTS trg_heuristics_updated_at ON financial_heuristics")
    op.execute("DROP TRIGGER IF EXISTS trg_fdc_updated_at ON financial_decision_cases")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at()")

    # Drop tables
    for table in ["financial_heuristics","audit_logs","state_transitions","reviews",
                  "decisions","financial_metrics_impacted","financial_risks",
                  "financial_assumptions","financial_decision_cases"]:
        op.drop_table(table)

    # Drop ENUMs
    for enum in ["framework_type","time_horizon_type","decision_type","decision_state","financial_domain"]:
        op.execute(f"DROP TYPE IF EXISTS {enum}")
