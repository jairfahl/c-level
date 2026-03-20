"""
Router: Admin — Operações de Administração Interna (P-10)

GET /admin/pending-reviews       → casos DECIDED há >90 dias sem revisão pós-decisão
GET /admin/api-balance           → saldo estimado de créditos da API Anthropic

MVP: notificação manual — sem envio automático de e-mail ou webhook.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.llm.service import LLMService
from app.schemas import ApiBalanceResponse, DecisionIntelligenceResponse, PendingReviewCaseResponse, PendingReviewsResponse
from app.services.intelligence_service import IntelligenceService
from app.services.review_trigger import REVIEW_THRESHOLD_DAYS, ReviewTrigger

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


# ---------------------------------------------------------------------------
# GET /admin/pending-reviews
# ---------------------------------------------------------------------------

@router.get("/pending-reviews", response_model=PendingReviewsResponse)
async def get_pending_reviews(
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> PendingReviewsResponse:
    """Retorna casos em estado DECIDED sem revisão há mais de 90 dias.

    Use este endpoint para identificar casos que necessitam de acompanhamento
    pós-decisão. MVP: notificação manual pelo Arquiteto.
    """
    pending_raw = await ReviewTrigger.get_cases_pending_review(session)
    pending = [PendingReviewCaseResponse(**p) for p in pending_raw]
    return PendingReviewsResponse(
        pending=pending,
        total=len(pending),
        threshold_days=REVIEW_THRESHOLD_DAYS,
    )


# ---------------------------------------------------------------------------
# GET /admin/decision-intelligence
# ---------------------------------------------------------------------------

@router.get("/api-balance", response_model=ApiBalanceResponse)
async def get_api_balance(
    user: dict = Depends(get_current_user),
) -> ApiBalanceResponse:
    """Retorna saldo estimado de créditos da API Anthropic baseado no uso acumulado de tokens."""
    from app.api.routers.state_machine import get_llm_service
    service = get_llm_service()
    data = await service.get_api_balance()
    return ApiBalanceResponse(**data)


@router.get("/decision-intelligence", response_model=DecisionIntelligenceResponse)
async def get_decision_intelligence(
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> DecisionIntelligenceResponse:
    """Retorna KPIs agregados para o dashboard de inteligência decisória."""
    data = await IntelligenceService.get_dashboard_data(session)
    return DecisionIntelligenceResponse(**data)
