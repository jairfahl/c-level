import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base
from app.models.enums import DecisionType, FinancialDomain


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    original_filename = Column(Text, nullable=False)
    file_type = Column(String(10), nullable=False)  # "pdf", "docx", "txt"
    file_size_bytes = Column(Integer, nullable=False)
    extracted_text = Column(Text, nullable=False)
    text_length = Column(Integer, nullable=False)
    financial_domain = Column(
        SAEnum(FinancialDomain, name="financial_domain", create_constraint=False),
        nullable=False,
    )
    decision_type = Column(
        SAEnum(DecisionType, name="decision_type", create_constraint=False),
        nullable=True,
    )
    active = Column(Boolean, nullable=False, default=True)
    uploaded_by = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
