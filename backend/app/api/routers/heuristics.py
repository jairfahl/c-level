"""
Router: Heuristics — Registro de Heurísticas Financeiras (P-10)

POST /heuristics               → criar heurística manual (201)
GET  /heuristics               → listar ativas (filtros: decision_type, domain)
PUT  /heuristics/{id}/deactivate → desativar (200)

Princípio: INSERT/UPDATE only — nunca DELETE.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.auth import get_current_user
from app.core.database import get_db
from app.api.routers.state_machine import get_llm_service
from app.llm.service import LLMService
from app.models.enums import DecisionType, FinancialDomain
from app.schemas import (
    HeuristicCreate,
    HeuristicListResponse,
    HeuristicResponse,
    LearningSummaryResponse,
)
from app.services.heuristics_service import HeuristicsService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/heuristics",
    tags=["Learning — Heuristics"],
)


# ---------------------------------------------------------------------------
# GET /heuristics/learning-summary  (ANTES das rotas com path params)
# ---------------------------------------------------------------------------

@router.get("/learning-summary", response_model=LearningSummaryResponse)
async def get_learning_summary(
    session: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    user: dict = Depends(get_current_user),
) -> LearningSummaryResponse:
    """Retorna resumo executivo consolidado dos aprendizados (heurísticas ativas)."""
    cache = llm_service._cache
    return await HeuristicsService.build_learning_summary(
        session=session,
        llm_service=llm_service,
        cache=cache,
    )


# ---------------------------------------------------------------------------
# POST /heuristics
# ---------------------------------------------------------------------------

@router.post("", response_model=HeuristicResponse, status_code=201)
async def create_heuristic(
    body: HeuristicCreate,
    session: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    user: dict = Depends(get_current_user),
) -> HeuristicResponse:
    """Cria uma heurística financeira manualmente (apenas pelo Arquiteto no MVP).

    A heurística é INSERT-only: nunca pode ser deletada, apenas desativada.
    """
    heuristic = await HeuristicsService.create_heuristic(
        session=session,
        decision_type=body.decision_type,
        financial_domain=body.financial_domain,
        heuristic_key=body.heuristic_key,
        heuristic_value=body.heuristic_value,
        source_case_id=body.source_case_id,
    )
    await session.flush()
    # Invalidar cache de learning summary
    await HeuristicsService._invalidate_learning_summary_cache(llm_service._cache)
    return HeuristicResponse.model_validate(heuristic)


# ---------------------------------------------------------------------------
# GET /heuristics
# ---------------------------------------------------------------------------

@router.get("", response_model=HeuristicListResponse)
async def list_heuristics(
    decision_type: Optional[DecisionType] = Query(default=None),
    domain: Optional[FinancialDomain] = Query(default=None),
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> HeuristicListResponse:
    """Lista heurísticas ativas com filtros opcionais.

    Query params:
      - decision_type: filtra por tipo de decisão
      - domain:        filtra por domínio financeiro
    """
    heuristics = await HeuristicsService.list_heuristics(
        session=session,
        decision_type=decision_type,
        financial_domain=domain,
    )
    return HeuristicListResponse(
        heuristics=[HeuristicResponse.model_validate(h) for h in heuristics],
        total=len(heuristics),
    )


# ---------------------------------------------------------------------------
# PUT /heuristics/{id}/deactivate
# ---------------------------------------------------------------------------

@router.put("/{heuristic_id}/deactivate", response_model=HeuristicResponse)
async def deactivate_heuristic(
    heuristic_id: UUID,
    session: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    user: dict = Depends(get_current_user),
) -> HeuristicResponse:
    """Desativa uma heurística (active=False). Nunca deleta — preserva histórico."""
    heuristic = await HeuristicsService.deactivate_heuristic(
        session=session,
        heuristic_id=heuristic_id,
    )
    # Invalidar cache de learning summary
    await HeuristicsService._invalidate_learning_summary_cache(llm_service._cache)
    return HeuristicResponse.model_validate(heuristic)
