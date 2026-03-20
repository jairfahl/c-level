"""
Router: Financial Decision Cases — CRUD

POST   /financial-decision-cases           → create case (state=DRAFT)
GET    /financial-decision-cases           → list (paginado, filtros)
GET    /financial-decision-cases/{case_id} → full case with all relations
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit_logger import AuditAction, AuditLogger
from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.exceptions import CaseNotFoundError, InvalidStateTransitionError
from app.models.enums import DecisionState, DecisionType, FinancialDomain
from app.models.financial_decision_case import FinancialDecisionCase
from app.schemas import (
    AssumptionResponse,
    CaseCreatedResponse,
    FinancialDecisionCaseCreate,
    FinancialDecisionCaseFullResponse,
    FinancialDecisionCaseResponse,
    PaginatedCasesResponse,
    ReclassifyRequest,
    RiskResponse,
)

router = APIRouter(
    prefix="/financial-decision-cases",
    tags=["Financial Decision Cases"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _load_case_full(case_id: UUID, session: AsyncSession) -> FinancialDecisionCase:
    """Load a case with all relationships eager-loaded. Raises CaseNotFoundError on miss."""
    result = await session.execute(
        select(FinancialDecisionCase)
        .options(
            selectinload(FinancialDecisionCase.assumptions),
            selectinload(FinancialDecisionCase.risks),
            selectinload(FinancialDecisionCase.metrics_impacted),
            selectinload(FinancialDecisionCase.decisions),
        )
        .where(FinancialDecisionCase.id == case_id)
    )
    case = result.scalar_one_or_none()
    if case is None:
        raise CaseNotFoundError()
    return case


def _build_full_response(case: FinancialDecisionCase) -> FinancialDecisionCaseFullResponse:
    """Map ORM case (with loaded relations) to the full response schema."""
    latest_decision = case.decisions[-1] if case.decisions else None
    return FinancialDecisionCaseFullResponse(
        id=case.id,
        title=case.title,
        description=case.description,
        financial_domain=case.financial_domain,
        impact_score=case.impact_score,
        financial_exposure=float(case.financial_exposure),
        time_horizon=case.time_horizon,
        external_agents_present=case.external_agents_present,
        decision_type=case.decision_type,
        framework_selected=case.framework_selected,
        scenario_required=case.scenario_required,
        state=case.state,
        created_at=case.created_at,
        updated_at=case.updated_at,
        assumptions=[AssumptionResponse.model_validate(a) for a in case.assumptions],
        risks=[RiskResponse.model_validate(r) for r in case.risks],
        financial_metrics_impacted=[m.metric_name for m in case.metrics_impacted],
        recommendation=latest_decision.recommendation if latest_decision else None,
        initial_hypothesis=latest_decision.initial_hypothesis if latest_decision else None,
        executive_decision=latest_decision.executive_decision if latest_decision else None,
        divergence_flag=latest_decision.divergence_flag if latest_decision else None,
    )


# ---------------------------------------------------------------------------
# POST /financial-decision-cases
# ---------------------------------------------------------------------------

# curl example:
# curl -X POST https://api.mentor-cfo.internal/v1/financial-decision-cases \
#   -H "Authorization: Bearer $TOKEN" \
#   -H "Content-Type: application/json" \
#   -d '{"title":"Reestruturação da dívida bancária","description":"Caso sobre dívida de longo prazo com bancos credores","financial_domain":"funding","financial_exposure":45000000.00,"decision_type":"debt_structuring","external_agents_present":true}'

@router.post("", status_code=201, response_model=CaseCreatedResponse)
async def create_financial_decision_case(
    body: FinancialDecisionCaseCreate,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> CaseCreatedResponse:
    """Cria um novo caso decisório financeiro. Estado inicial: DRAFT."""
    user_id = user.get("sub", "system")

    case = FinancialDecisionCase(
        title=body.title,
        description=body.description,
        financial_domain=body.financial_domain,
        financial_exposure=body.financial_exposure,
        time_horizon=body.time_horizon,
        external_agents_present=body.external_agents_present,
        decision_type=body.decision_type,
    )
    session.add(case)
    await session.flush()  # aplica defaults (uuid4 + DRAFT) antes de ler os atributos

    AuditLogger.log(
        session=session,
        action=AuditAction.CASE_CREATED,
        decision_case_id=case.id,
        payload={"title": body.title, "created_by": user_id},
    )

    return CaseCreatedResponse(id=case.id, state=case.state)


# ---------------------------------------------------------------------------
# GET /financial-decision-cases
# ---------------------------------------------------------------------------

# curl example:
# curl "https://api.mentor-cfo.internal/v1/financial-decision-cases?domain=funding&state=DRAFT&page=1&limit=20" \
#   -H "Authorization: Bearer $TOKEN"

@router.get("", response_model=PaginatedCasesResponse)
async def list_financial_decision_cases(
    domain: Optional[FinancialDomain] = Query(default=None, description="Filtrar por domínio financeiro"),
    state: Optional[DecisionState] = Query(default=None, description="Filtrar por estado"),
    decision_type: Optional[DecisionType] = Query(default=None, description="Filtrar por tipo de decisão"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> PaginatedCasesResponse:
    """Retorna lista paginada de casos com filtros opcionais."""
    filters = []
    if domain is not None:
        filters.append(FinancialDecisionCase.financial_domain == domain)
    if state is not None:
        filters.append(FinancialDecisionCase.state == state)
    if decision_type is not None:
        filters.append(FinancialDecisionCase.decision_type == decision_type)

    # Count
    count_stmt = select(func.count(FinancialDecisionCase.id))
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = (await session.execute(count_stmt)).scalar() or 0

    # Paginated items
    items_stmt = select(FinancialDecisionCase)
    if filters:
        items_stmt = items_stmt.where(*filters)
    items_stmt = (
        items_stmt
        .order_by(FinancialDecisionCase.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    cases = (await session.execute(items_stmt)).scalars().all()

    items = [
        FinancialDecisionCaseResponse(
            id=c.id,
            title=c.title,
            description=c.description,
            financial_domain=c.financial_domain,
            impact_score=c.impact_score,
            financial_exposure=float(c.financial_exposure),
            time_horizon=c.time_horizon,
            external_agents_present=c.external_agents_present,
            decision_type=c.decision_type,
            framework_selected=c.framework_selected,
            scenario_required=c.scenario_required,
            state=c.state,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in cases
    ]

    return PaginatedCasesResponse(items=items, total=total, page=page, limit=limit)


# ---------------------------------------------------------------------------
# GET /financial-decision-cases/{case_id}
# ---------------------------------------------------------------------------

# curl example:
# curl "https://api.mentor-cfo.internal/v1/financial-decision-cases/{id}" \
#   -H "Authorization: Bearer $TOKEN"

@router.get("/{case_id}", response_model=FinancialDecisionCaseFullResponse)
async def get_financial_decision_case(
    case_id: UUID,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> FinancialDecisionCaseFullResponse:
    """Retorna o caso completo com premissas, riscos, métricas, recomendação e decisão executiva."""
    case = await _load_case_full(case_id, session)
    return _build_full_response(case)


# ---------------------------------------------------------------------------
# Helpers (simple load)
# ---------------------------------------------------------------------------

async def _get_case_or_404(case_id: UUID, session: AsyncSession) -> FinancialDecisionCase:
    """Load case without relationships. Raises CaseNotFoundError on miss."""
    result = await session.execute(
        select(FinancialDecisionCase).where(FinancialDecisionCase.id == case_id)
    )
    case = result.scalar_one_or_none()
    if case is None:
        raise CaseNotFoundError()
    return case


# ---------------------------------------------------------------------------
# PATCH /financial-decision-cases/{case_id}/reclassify
# ---------------------------------------------------------------------------

@router.patch("/{case_id}/reclassify", response_model=FinancialDecisionCaseResponse)
async def reclassify_case(
    case_id: UUID,
    body: ReclassifyRequest,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Atualiza domínio e tipo de decisão. Permitido apenas em estado DRAFT."""
    case = await _get_case_or_404(case_id, session)
    if case.state != DecisionState.DRAFT:
        raise InvalidStateTransitionError(
            message="Reclassificação disponível apenas em estado DRAFT."
        )
    case.financial_domain = body.financial_domain
    case.decision_type    = body.decision_type
    await session.flush()
    return FinancialDecisionCaseResponse.model_validate(case)
