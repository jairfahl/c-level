"""Add knowledge_documents table

Revision ID: 002
Revises: 001
Create Date: 2026-03-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Reuse existing enums — do NOT recreate
    financial_domain = postgresql.ENUM(
        "planning", "reporting", "treasury", "funding", "risk",
        name="financial_domain", create_type=False,
    )
    decision_type = postgresql.ENUM(
        "budget_adjustment", "forecast_revision", "capital_allocation",
        "debt_structuring", "liquidity_management", "risk_hedging",
        "cost_reduction", "investment_evaluation",
        name="decision_type", create_type=False,
    )

    op.create_table(
        "knowledge_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("file_type", sa.String(10), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("text_length", sa.Integer(), nullable=False),
        sa.Column("financial_domain", financial_domain, nullable=False),
        sa.Column("decision_type", decision_type, nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("uploaded_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "file_size_bytes > 0 AND file_size_bytes <= 10485760",
            name="ck_knowledge_documents_file_size",
        ),
        sa.CheckConstraint(
            "file_type IN ('pdf', 'docx', 'txt')",
            name="ck_knowledge_documents_file_type",
        ),
    )

    op.create_index(
        "idx_kd_domain_type_active",
        "knowledge_documents",
        ["financial_domain", "decision_type", "active"],
    )


def downgrade() -> None:
    op.drop_index("idx_kd_domain_type_active", table_name="knowledge_documents")
    op.drop_table("knowledge_documents")
