"""Expand allowed file types for knowledge_documents

Revision ID: 004
Revises: 003
Create Date: 2026-03-19

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE knowledge_documents "
        "DROP CONSTRAINT IF EXISTS ck_knowledge_documents_file_type"
    )
    op.execute(
        "ALTER TABLE knowledge_documents "
        "ADD CONSTRAINT ck_knowledge_documents_file_type "
        "CHECK (file_type IN ('pdf','docx','txt','xlsx','xls','pptx','csv','md'))"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE knowledge_documents "
        "DROP CONSTRAINT IF EXISTS ck_knowledge_documents_file_type"
    )
    op.execute(
        "ALTER TABLE knowledge_documents "
        "ADD CONSTRAINT ck_knowledge_documents_file_type "
        "CHECK (file_type IN ('pdf','docx','txt'))"
    )
