"""
Router: State Machine — Transições do Protocolo Decisório

PUT /financial-decision-cases/{id}/classify   → DRAFT → CLASSIFIED
PUT /financial-decision-cases/{id}/structure  → CLASSIFIED → STRUCTURED
PUT /financial-decision-cases/{id}/analyze    → STRUCTURED → ANALYZED → RECOMMENDED
PUT /financial-decision-cases/{id}/decide     → RECOMMENDED → DECIDED
PUT /financial-decision-cases/{id}/review     → DECIDED/UNDER_REVIEW → CLOSED

Cada endpoint valida a transição via StateMachineController (HTTP 409 se inválida)
e persiste StateTransition + AuditLog atomicamente na mesma sessão.

O endpoint /analyze chama a engine determinística (P-04) ANTES do LLM (P-05).
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit_logger import AuditAction, AuditLogger
from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.exceptions import CaseNotFoundError, InvalidStateTransitionError
from app.core.framework_selector import FRAMEWORK_CATALOG, FRAMEWORK_RATIONALE, FrameworkSelector
from app.core.game_theory import GameTheoryActivator
from app.core.state_machine import StateMachineController
from app.llm.prompt_builder import PromptContext
from app.llm.service import LLMService
from app.models.enums import DecisionState
from app.models.financial_decision_case import (
    Decision,
    FinancialAssumption,
    FinancialDecisionCase,
    FinancialMetricImpacted,
    FinancialRisk,
    Review,
)
from app.schemas import (
    AnalysisResponse,
    ClassificationSuggestionResponse,
    ClassifyRequest,
    ClassifyResponse,
    DecideRequest,
    DecideResponse,
    DecisionBenchmark,
    FrameworkCatalogEntry,
    FrameworkCatalogResponse,
    FrameworkSuggestionDetail,
    HeuristicAlertItem,
    HeuristicAlertsResponse,
    HypothesisRequest,
    MethodSelectionRequest,
    MethodSuggestionResponse,
    ReviewRequest,
    ReviewResponse,
    StructureRequest,
    StructureResponse,
)
from app.services.heuristics_service import HeuristicsService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.review_service import ReviewService

router = APIRouter(
    prefix="/financial-decision-cases",
    tags=["State Machine"],
)


# ---------------------------------------------------------------------------
# Dependency: LLMService (injectable for testing)
# ---------------------------------------------------------------------------

def get_llm_service() -> LLMService:
    """Dependency factory — override in tests to inject a mock LLMService."""
    return LLMService()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _load_case(case_id: UUID, session: AsyncSession) -> FinancialDecisionCase:
    """Load the case without relationships. Raises CaseNotFoundError on miss."""
    result = await session.execute(
        select(FinancialDecisionCase).where(FinancialDecisionCase.id == case_id)
    )
    case = result.scalar_one_or_none()
    if case is None:
        raise CaseNotFoundError()
    return case


async def _load_case_with(
    case_id: UUID,
    session: AsyncSession,
    *load_options,
) -> FinancialDecisionCase:
    """Load case with specified selectinload options. Raises CaseNotFoundError on miss."""
    stmt = select(FinancialDecisionCase).where(FinancialDecisionCase.id == case_id)
    for opt in load_options:
        stmt = stmt.options(opt)
    case = (await session.execute(stmt)).scalar_one_or_none()
    if case is None:
        raise CaseNotFoundError()
    return case


# ---------------------------------------------------------------------------
# GET /financial-decision-cases/framework-catalog
# ---------------------------------------------------------------------------

@router.get("/framework-catalog", response_model=FrameworkCatalogResponse)
async def get_framework_catalog(
    user: dict = Depends(get_current_user),
) -> FrameworkCatalogResponse:
    """Retorna catálogo completo dos 11 frameworks com metadata rica."""
    entries = [FrameworkCatalogEntry(**e) for e in FrameworkSelector.catalog()]
    return FrameworkCatalogResponse(frameworks=entries)


# ---------------------------------------------------------------------------
# GET /financial-decision-cases/{id}/suggest-reclassification
# ---------------------------------------------------------------------------

@router.get("/{case_id}/suggest-reclassification", response_model=ClassificationSuggestionResponse)
async def suggest_reclassification(
    case_id: UUID,
    session: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    user: dict = Depends(get_current_user),
):
    """Analisa título/descrição vs domínio/tipo e sugere reclassificação. Apenas em DRAFT."""
    case = await _load_case_with(case_id, session)
    if case.state != DecisionState.DRAFT:
        return ClassificationSuggestionResponse(reclassification_needed=False)
    result = await llm_service.validate_classification(
        title=case.title,
        description=case.description or "",
        domain=case.financial_domain,
        decision_type=case.decision_type,
    )
    if result is None or result.confidence < 0.7:
        return ClassificationSuggestionResponse(reclassification_needed=False)
    return result


# ---------------------------------------------------------------------------
# PUT /financial-decision-cases/{id}/classify
# ---------------------------------------------------------------------------

# curl example:
# curl -X PUT "https://api.mentor-cfo.internal/v1/financial-decision-cases/{id}/classify" \
#   -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
#   -d '{"impact_score": 4}'

@router.put("/{case_id}/classify", response_model=ClassifyResponse)
async def classify_decision_case(
    case_id: UUID,
    body: ClassifyRequest,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> ClassifyResponse:
    """Classifica o caso: define impact_score, seleciona framework analítico e
    calcula scenario_required. Transição: DRAFT → CLASSIFIED."""
    user_id = user.get("sub", "system")
    case = await _load_case(case_id, session)

    # Engine determinística: seleciona framework
    framework = FrameworkSelector.select(case.decision_type, case.external_agents_present)
    case.impact_score = body.impact_score
    case.framework_selected = framework

    # State transition (validates + persists StateTransition + AuditLog)
    await StateMachineController().transition(
        case, DecisionState.CLASSIFIED, session, triggered_by=user_id
    )

    return ClassifyResponse(
        state=case.state,
        framework_selected=framework,
        scenario_required=case.scenario_required,
    )


# ---------------------------------------------------------------------------
# PUT /financial-decision-cases/{id}/structure
# ---------------------------------------------------------------------------

# curl example:
# curl -X PUT "https://api.mentor-cfo.internal/v1/financial-decision-cases/{id}/structure" \
#   -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
#   -d '{"assumptions":["Selic estável","Receita +8%","Crédito disponível"],"risks":["Alta de juros","Downgrade","Concentração de vencimentos"]}'

@router.put("/{case_id}/structure", response_model=StructureResponse)
async def structure_decision_case(
    case_id: UUID,
    body: StructureRequest,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> StructureResponse:
    """Registra premissas e riscos financeiros (mínimo 3 cada).
    Transição: CLASSIFIED → STRUCTURED."""
    user_id = user.get("sub", "system")
    case = await _load_case(case_id, session)

    # Persist assumptions
    for text in body.assumptions:
        session.add(FinancialAssumption(
            decision_case_id=case.id,
            text=text,
            is_implicit=False,
        ))

    # Persist risks
    for text in body.risks:
        session.add(FinancialRisk(
            decision_case_id=case.id,
            text=text,
        ))

    await StateMachineController().transition(
        case, DecisionState.STRUCTURED, session, triggered_by=user_id
    )

    return StructureResponse(
        state=case.state,
        assumptions_count=len(body.assumptions),
        risks_count=len(body.risks),
    )


# ---------------------------------------------------------------------------
# PUT /financial-decision-cases/{id}/analyze
# ---------------------------------------------------------------------------

# curl example:
# curl -X PUT "https://api.mentor-cfo.internal/v1/financial-decision-cases/{id}/analyze" \
#   -H "Authorization: Bearer $TOKEN"

@router.get("/{case_id}/suggest-methods", response_model=MethodSuggestionResponse)
async def suggest_methods(
    case_id: UUID,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> MethodSuggestionResponse:
    """Retorna frameworks sugeridos para o case.
    Deve ser chamado após estado STRUCTURED, antes de /analyze.
    O executivo pode customizar a seleção antes de confirmar a análise."""
    case = await _load_case_with(case_id, session)

    if case.state != DecisionState.STRUCTURED:
        raise InvalidStateTransitionError(
            message=f"Sugestão de métodos disponível apenas em estado STRUCTURED. Estado atual: {case.state}"
        )

    suggested = FrameworkSelector.suggest(
        case.decision_type,
        case.external_agents_present,
        impact_score=case.impact_score,
        financial_exposure=float(case.financial_exposure),
    )

    details_raw = FrameworkSelector.suggest_detailed(
        case.decision_type,
        case.external_agents_present,
        impact_score=case.impact_score,
        financial_exposure=float(case.financial_exposure),
    )
    suggestion_details = [FrameworkSuggestionDetail(**d) for d in details_raw]
    available_catalog = [FrameworkCatalogEntry(**e) for e in FrameworkSelector.catalog()]

    return MethodSuggestionResponse(
        primary_framework=suggested[0],
        suggested_frameworks=suggested,
        suggestions_rationale={fw.value: FRAMEWORK_RATIONALE.get(fw, "") for fw in suggested},
        available_frameworks=FrameworkSelector.available(),
        suggestion_details=suggestion_details,
        available_catalog=available_catalog,
    )


@router.put("/{case_id}/analyze", response_model=AnalysisResponse)
async def analyze_decision_case(
    case_id: UUID,
    body: MethodSelectionRequest | None = None,
    session: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    user: dict = Depends(get_current_user),
) -> AnalysisResponse:
    """Aciona a análise LLM com o framework selecionado.
    Transição: STRUCTURED → ANALYZED → RECOMMENDED (dupla transição automática).
    Fallback determinístico quando LLM indisponível (llm_unavailable=True)."""
    user_id = user.get("sub", "system")

    # Load with relations needed for PromptContext
    case = await _load_case_with(
        case_id, session,
        selectinload(FinancialDecisionCase.assumptions),
        selectinload(FinancialDecisionCase.risks),
    )

    smc = StateMachineController()

    # Phase 1: STRUCTURED → ANALYZED
    await smc.transition(case, DecisionState.ANALYZED, session, triggered_by=user_id)

    # Build PromptContext from deterministic engine (P-04) inputs
    game_theory_active = GameTheoryActivator.is_active(
        case.decision_type, case.external_agents_present
    )
    knowledge_snippets = await KnowledgeBaseService.query_relevant_snippets(
        session, case.financial_domain, case.decision_type
    )
    heuristics_context = await HeuristicsService.query_all_for_analysis(session)
    frameworks = body.frameworks_selected if body else [case.framework_selected]

    ctx = PromptContext(
        case_id=case.id,
        decision_type=case.decision_type,
        financial_domain=case.financial_domain,
        financial_exposure=float(case.financial_exposure),
        time_horizon=case.time_horizon,
        framework_selected=case.framework_selected,
        scenario_required=case.scenario_required,
        game_theory_active=game_theory_active,
        assumptions=[a.text for a in case.assumptions],
        risks=[r.text for r in case.risks],
        knowledge_snippets=knowledge_snippets,
        heuristics_context=heuristics_context,
        frameworks_selected=frameworks,
    )

    # Call LLM layer (with cache + fallback)
    llm_result = await llm_service.analyze(ctx, session, triggered_by=user_id)

    # Persist financial metrics
    for metric_name in llm_result.financial_metrics_impacted:
        session.add(FinancialMetricImpacted(
            decision_case_id=case.id,
            metric_name=metric_name,
        ))

    # Persist implicit assumptions found by the LLM
    for implicit_text in llm_result.implicit_assumptions_found:
        session.add(FinancialAssumption(
            decision_case_id=case.id,
            text=implicit_text,
            is_implicit=True,
        ))

    # Create Decision record with the LLM recommendation
    session.add(Decision(
        decision_case_id=case.id,
        recommendation=llm_result.recommendation,
    ))

    # Phase 2: ANALYZED → RECOMMENDED (automatic)
    await smc.transition(case, DecisionState.RECOMMENDED, session, triggered_by=user_id)

    return AnalysisResponse(
        state=case.state,
        recommendation=llm_result.recommendation,
        framework_selected=case.framework_selected,
        primary_framework=frameworks[0],
        frameworks_selected=frameworks,
        financial_metrics_impacted=llm_result.financial_metrics_impacted,
        scenario_summary=llm_result.scenario_summary,
        implicit_assumptions_found=llm_result.implicit_assumptions_found,
        game_theory_model=llm_result.game_theory_model,
        llm_unavailable=llm_result.llm_unavailable,
    )


# ---------------------------------------------------------------------------
# PUT /financial-decision-cases/{id}/reanalyze
# ---------------------------------------------------------------------------


@router.put("/{case_id}/reanalyze", response_model=AnalysisResponse)
async def reanalyze_decision_case(
    case_id: UUID,
    session: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    user: dict = Depends(get_current_user),
) -> AnalysisResponse:
    """Re-executa a análise LLM sem alterar o estado.
    Permitido apenas em estado RECOMMENDED.
    Útil quando a análise anterior usou o fallback determinístico."""
    user_id = user.get("sub", "system")

    case = await _load_case_with(
        case_id, session,
        selectinload(FinancialDecisionCase.assumptions),
        selectinload(FinancialDecisionCase.risks),
    )

    if case.state != DecisionState.RECOMMENDED:
        raise InvalidStateTransitionError(
            message=f"Reanálise disponível apenas em estado RECOMMENDED. Estado atual: {case.state}"
        )

    game_theory_active = GameTheoryActivator.is_active(
        case.decision_type, case.external_agents_present
    )
    knowledge_snippets = await KnowledgeBaseService.query_relevant_snippets(
        session, case.financial_domain, case.decision_type
    )
    heuristics_context = await HeuristicsService.query_all_for_analysis(session)
    ctx = PromptContext(
        case_id=case.id,
        decision_type=case.decision_type,
        financial_domain=case.financial_domain,
        financial_exposure=float(case.financial_exposure),
        time_horizon=case.time_horizon,
        framework_selected=case.framework_selected,
        scenario_required=case.scenario_required,
        game_theory_active=game_theory_active,
        assumptions=[a.text for a in case.assumptions if not a.is_implicit],
        risks=[r.text for r in case.risks],
        knowledge_snippets=knowledge_snippets,
        heuristics_context=heuristics_context,
    )

    llm_result = await llm_service.analyze(ctx, session, triggered_by=user_id)

    # Limpa métricas antigas e recria com resultado atualizado
    await session.execute(
        delete(FinancialMetricImpacted).where(
            FinancialMetricImpacted.decision_case_id == case.id
        )
    )
    for metric_name in llm_result.financial_metrics_impacted:
        session.add(FinancialMetricImpacted(
            decision_case_id=case.id,
            metric_name=metric_name,
        ))

    # Limpa premissas implícitas antigas e recria
    await session.execute(
        delete(FinancialAssumption).where(
            FinancialAssumption.decision_case_id == case.id,
            FinancialAssumption.is_implicit == True,
        )
    )
    for implicit_text in llm_result.implicit_assumptions_found:
        session.add(FinancialAssumption(
            decision_case_id=case.id,
            text=implicit_text,
            is_implicit=True,
        ))

    # Atualiza o registro Decision existente (não cria um novo)
    result_q = await session.execute(
        select(Decision)
        .where(Decision.decision_case_id == case.id)
        .order_by(Decision.created_at.desc())
        .limit(1)
    )
    decision = result_q.scalar_one_or_none()
    if decision:
        decision.recommendation = llm_result.recommendation
    else:
        session.add(Decision(
            decision_case_id=case.id,
            recommendation=llm_result.recommendation,
        ))

    return AnalysisResponse(
        state=case.state,
        recommendation=llm_result.recommendation,
        framework_selected=case.framework_selected,
        financial_metrics_impacted=llm_result.financial_metrics_impacted,
        scenario_summary=llm_result.scenario_summary,
        implicit_assumptions_found=llm_result.implicit_assumptions_found,
        game_theory_model=llm_result.game_theory_model,
        llm_unavailable=llm_result.llm_unavailable,
    )


# ---------------------------------------------------------------------------
# GET /financial-decision-cases/{id}/heuristic-alerts
# ---------------------------------------------------------------------------

@router.get("/{case_id}/heuristic-alerts", response_model=HeuristicAlertsResponse)
async def get_heuristic_alerts(
    case_id: UUID,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> HeuristicAlertsResponse:
    """Retorna alertas proativos e benchmark para o caso, baseados em heurísticas históricas."""
    case = await _load_case(case_id, session)
    alerts_raw = await HeuristicsService.generate_alerts_for_case(session, case)
    alerts = [HeuristicAlertItem(**a) for a in alerts_raw]
    benchmark_raw = await HeuristicsService.compute_benchmark(session, case)
    benchmark = DecisionBenchmark(**benchmark_raw) if benchmark_raw else None
    return HeuristicAlertsResponse(alerts=alerts, total=len(alerts), benchmark=benchmark)


# ---------------------------------------------------------------------------
# PUT /financial-decision-cases/{id}/hypothesis
# ---------------------------------------------------------------------------

@router.put("/{case_id}/hypothesis")
async def record_hypothesis(
    case_id: UUID,
    body: HypothesisRequest,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Registra a hipótese inicial do CFO antes de revelar a recomendação da IA.
    Permitido apenas em estado RECOMMENDED (Decision já existe). Não altera o estado."""
    case = await _load_case_with(
        case_id, session,
        selectinload(FinancialDecisionCase.decisions),
    )

    if case.state != DecisionState.RECOMMENDED:
        raise InvalidStateTransitionError(
            message=f"Registro de hipótese disponível apenas em estado RECOMMENDED. Estado atual: {case.state}"
        )

    if case.decisions:
        latest = case.decisions[-1]
        latest.initial_hypothesis = body.initial_hypothesis

    return {"status": "recorded"}


# ---------------------------------------------------------------------------
# PUT /financial-decision-cases/{id}/decide
# ---------------------------------------------------------------------------

# curl example (without divergence):
# curl -X PUT "https://api.mentor-cfo.internal/v1/financial-decision-cases/{id}/decide" \
#   -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
#   -d '{"executive_decision":"Aprovamos a reestruturação completa conforme recomendado."}'
#
# curl example (with divergence):
# curl -X PUT "https://api.mentor-cfo.internal/v1/financial-decision-cases/{id}/decide" \
#   -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
#   -d '{"executive_decision":"Optamos por apenas 60% da reestruturação.","divergence_justification":"Contexto geopolítico exige postura conservadora.","monitoring_criteria":["DRE trimestral","Covenants bancários"]}'

@router.put("/{case_id}/decide", response_model=DecideResponse)
async def record_executive_decision(
    case_id: UUID,
    body: DecideRequest,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> DecideResponse:
    """Registra a decisão executiva do CFO. Se divergir da recomendação do Mentor,
    divergence_flag=True é registrado automaticamente.
    Transição: RECOMMENDED → DECIDED."""
    user_id = user.get("sub", "system")

    # Load case with decisions to update the latest Decision record
    case = await _load_case_with(
        case_id, session,
        selectinload(FinancialDecisionCase.decisions),
    )

    # Divergence is signalled by providing a justification
    divergence_flag = body.divergence_justification is not None

    # Update the latest Decision record with executive input
    if case.decisions:
        latest = case.decisions[-1]
        latest.executive_decision = body.executive_decision
        latest.divergence_flag = divergence_flag

    # Log divergence event if applicable
    if divergence_flag:
        AuditLogger.log(
            session=session,
            action=AuditAction.DIVERGENCE_RECORDED,
            decision_case_id=case.id,
            payload={
                "justification": body.divergence_justification,
                "monitoring_criteria": body.monitoring_criteria,
            },
        )

    await StateMachineController().transition(
        case, DecisionState.DECIDED, session, triggered_by=user_id
    )

    return DecideResponse(state=case.state, divergence_flag=divergence_flag)


# ---------------------------------------------------------------------------
# PUT /financial-decision-cases/{id}/review
# ---------------------------------------------------------------------------

# curl example:
# curl -X PUT "https://api.mentor-cfo.internal/v1/financial-decision-cases/{id}/review" \
#   -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
#   -d '{"outcome_summary":"Reestruturação reduziu custo da dívida em 15% conforme projetado.","forecast_accuracy_score":8,"risk_realization_rate":20.0,"capital_allocation_efficiency_score":90.0}'

@router.put("/{case_id}/review", response_model=ReviewResponse)
async def review_decision_case(
    case_id: UUID,
    body: ReviewRequest,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> ReviewResponse:
    """Captura o resultado real da decisão para aprendizado e calibração.
    Aceita caso em DECIDED ou UNDER_REVIEW. Transição final: → CLOSED."""
    user_id = user.get("sub", "system")
    case = await _load_case(case_id, session)

    smc = StateMachineController()

    # If still in DECIDED state, move through UNDER_REVIEW first
    if case.state == DecisionState.DECIDED:
        await smc.transition(case, DecisionState.UNDER_REVIEW, session, triggered_by=user_id)

    # UNDER_REVIEW → CLOSED (raises InvalidStateTransitionError for any other state)
    await smc.transition(case, DecisionState.CLOSED, session, triggered_by=user_id)

    # P-10: Auto-calculate divergence_outcome_flag from historical divergence
    # Rule: True when Decision.divergence_flag=True AND forecast_accuracy_score < 5
    divergence_outcome = await ReviewService.compute_divergence_outcome(
        case, body.forecast_accuracy_score, session
    )

    # P-10: Mark risks as materialized when risk_realization_rate > 50 %
    await ReviewService.update_risk_materialization(
        case, body.risk_realization_rate, session
    )

    # Persist review outcome
    session.add(Review(
        decision_case_id=case.id,
        outcome_summary=body.outcome_summary,
        forecast_accuracy_score=body.forecast_accuracy_score,
        risk_realization_rate=body.risk_realization_rate,
        capital_allocation_efficiency_score=body.capital_allocation_efficiency_score,
        divergence_outcome_flag=divergence_outcome,
    ))

    # Auto-generate heuristics from review data (deterministic rules)
    generated = await HeuristicsService.generate_from_review(
        session,
        case,
        body.forecast_accuracy_score,
        body.risk_realization_rate,
        body.capital_allocation_efficiency_score,
        divergence_outcome,
    )

    return ReviewResponse(
        state=case.state,
        divergence_outcome_flag=divergence_outcome,
        heuristics_generated=len(generated),
    )
