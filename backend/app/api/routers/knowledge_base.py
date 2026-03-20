"""
Router: Knowledge Base — Upload e consulta de documentos organizacionais

POST   /knowledge-base/upload              Upload multipart/form-data → 201
POST   /knowledge-base/validate-relevance  Validação de relevância (stateless)
GET    /knowledge-base                     Listagem com filtros (domain, decision_type)
GET    /knowledge-base/{id}                Detalhe com texto extraído (preview)
DELETE /knowledge-base/{id}                Soft-delete
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.exceptions import (
    DocumentIrrelevantError,
    DocumentRelevanceBorderlineError,
)
from app.models.enums import DecisionType, FinancialDomain
from app.schemas import (
    KnowledgeDocumentListResponse,
    KnowledgeDocumentResponse,
    KnowledgeDocumentSummaryResponse,
    KnowledgeDocumentUploadResponse,
    RelevanceCheckResponse,
)
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.relevance_validator import RelevanceValidator, RelevanceVerdict

router = APIRouter(
    prefix="/knowledge-base",
    tags=["Knowledge Base"],
)


# ---------------------------------------------------------------------------
# POST /knowledge-base/upload
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=KnowledgeDocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    financial_domain: FinancialDomain = Form(...),
    decision_type: Optional[DecisionType] = Form(None),
    description: Optional[str] = Form(None),
    confirm_relevance: Optional[bool] = Form(False),
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> KnowledgeDocumentUploadResponse:
    """Upload de documento organizacional (máximo 10 MB).
    Tipos aceitos: PDF, DOCX, TXT, XLSX, XLS, PPTX, CSV, MD.
    O texto é extraído automaticamente e armazenado para consulta futura.
    Se confirm_relevance=false, valida relevância antes do upload."""
    uploaded_by = user.get("sub", "system")

    if not confirm_relevance:
        content_peek = await file.read()
        await file.seek(0)

        file_type = KnowledgeBaseService._detect_file_type(file.filename or "")
        try:
            extracted = KnowledgeBaseService._extract_text(content_peek, file_type)
        except Exception:
            extracted = ""

        if extracted:
            result = RelevanceValidator.validate(extracted, financial_domain.value)
            if result.verdict == RelevanceVerdict.IRRELEVANT:
                raise DocumentIrrelevantError(result.reason)
            if result.verdict == RelevanceVerdict.BORDERLINE:
                raise DocumentRelevanceBorderlineError(result.reason)

    doc = await KnowledgeBaseService.upload_document(
        session=session,
        file=file,
        title=title,
        financial_domain=financial_domain,
        decision_type=decision_type,
        description=description,
        uploaded_by=uploaded_by,
    )
    await session.flush()
    return KnowledgeDocumentUploadResponse.model_validate(doc)


# ---------------------------------------------------------------------------
# POST /knowledge-base/validate-relevance
# ---------------------------------------------------------------------------

@router.post("/validate-relevance", response_model=RelevanceCheckResponse)
async def validate_relevance(
    file: UploadFile = File(...),
    financial_domain: FinancialDomain = Form(...),
    user: dict = Depends(get_current_user),
) -> RelevanceCheckResponse:
    """Valida se um documento é relevante para o domínio financeiro selecionado.
    Stateless — não armazena nada."""
    content = await file.read()
    size = len(content)

    if size > KnowledgeBaseService.MAX_FILE_SIZE:
        from app.core.exceptions import DocumentTooLargeError
        raise DocumentTooLargeError(size)

    file_type = KnowledgeBaseService._detect_file_type(file.filename or "")
    extracted = KnowledgeBaseService._extract_text(content, file_type)

    result = RelevanceValidator.validate(extracted, financial_domain.value)

    return RelevanceCheckResponse(
        verdict=result.verdict.value,
        confidence=result.confidence,
        reason=result.reason,
        domain_keywords_found=result.domain_keywords_found,
        off_topic_keywords_found=result.off_topic_keywords_found,
    )


# ---------------------------------------------------------------------------
# GET /knowledge-base
# ---------------------------------------------------------------------------

@router.get("", response_model=KnowledgeDocumentListResponse)
async def list_documents(
    domain: Optional[FinancialDomain] = None,
    decision_type: Optional[DecisionType] = None,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> KnowledgeDocumentListResponse:
    """Lista documentos da base de conhecimento com filtros opcionais."""
    docs = await KnowledgeBaseService.list_documents(
        session=session,
        domain=domain,
        decision_type=decision_type,
    )
    return KnowledgeDocumentListResponse(
        documents=[KnowledgeDocumentSummaryResponse.model_validate(d) for d in docs],
        total=len(docs),
    )


# ---------------------------------------------------------------------------
# GET /knowledge-base/{id}
# ---------------------------------------------------------------------------

@router.get("/{document_id}", response_model=KnowledgeDocumentResponse)
async def get_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> KnowledgeDocumentResponse:
    """Retorna documento completo com texto extraído (para preview)."""
    doc = await KnowledgeBaseService.get_document(session, document_id)
    return KnowledgeDocumentResponse.model_validate(doc)


# ---------------------------------------------------------------------------
# DELETE /knowledge-base/{id}
# ---------------------------------------------------------------------------

@router.delete("/{document_id}", status_code=204, response_class=Response)
async def delete_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Soft-delete: marca o documento como inativo."""
    await KnowledgeBaseService.delete_document(session, document_id)
