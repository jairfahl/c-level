"""
Router: Audit — Trilha de Auditoria

GET /financial-decision-cases/{case_id}/state-transitions
  → Histórico completo de transições de estado (ordenado por transitioned_at)
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.exceptions import CaseNotFoundError
from app.models.financial_decision_case import FinancialDecisionCase, StateTransition
from app.schemas import StateTransitionResponse, StateTransitionsListResponse

router = APIRouter(
    prefix="/financial-decision-cases",
    tags=["Audit"],
)


# curl example:
# curl "https://api.mentor-cfo.internal/v1/financial-decision-cases/{id}/state-transitions" \
#   -H "Authorization: Bearer $TOKEN"

@router.get("/{case_id}/state-transitions", response_model=StateTransitionsListResponse)
async def list_state_transitions(
    case_id: UUID,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> StateTransitionsListResponse:
    """Retorna a trilha completa de transições de estado do caso (auditoria)."""
    # Verify case exists
    case_exists = (
        await session.execute(
            select(FinancialDecisionCase.id).where(FinancialDecisionCase.id == case_id)
        )
    ).scalar_one_or_none()
    if case_exists is None:
        raise CaseNotFoundError()

    # Load transitions ordered chronologically
    result = await session.execute(
        select(StateTransition)
        .where(StateTransition.decision_case_id == case_id)
        .order_by(StateTransition.transitioned_at.asc())
    )
    transitions = result.scalars().all()

    return StateTransitionsListResponse(
        decision_case_id=case_id,
        transitions=[StateTransitionResponse.model_validate(t) for t in transitions],
    )
