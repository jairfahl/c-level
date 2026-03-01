"""
Testes unitários — Engine Determinística (P-04)

Cobertura:
- StateMachineController: todas as 7 transições válidas, transições inválidas
  (HTTP 409), estado terminal, payload do audit log.
- FinancialImpactScorer: todos os 5 intervalos, valores de fronteira,
  scenario_required correto.
- FrameworkSelector: todos os 8 tipos de decisão sem external_agents,
  ativação de game_theory para os 3 tipos elegíveis, não ativação para os demais.
- GameTheoryActivator: todos os tipos elegíveis (True/False),
  todos os tipos não-elegíveis com external_agents=True.
- AuditLogger: criação de AuditLog com e sem payload, valores de AuditAction.
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

import pytest

from app.core.audit_logger import AuditAction, AuditLogger
from app.core.exceptions import InvalidStateTransitionError
from app.core.framework_selector import FrameworkSelector, _BASE_FRAMEWORK, _GAME_THEORY_ELIGIBLE
from app.core.game_theory import GAME_THEORY_ELIGIBLE_TYPES, GameTheoryActivator
from app.core.impact_scorer import FinancialImpactScorer, ScoreResult
from app.core.state_machine import VALID_TRANSITIONS, StateMachineController
from app.models.enums import DecisionState, DecisionType, FrameworkType
from app.models.financial_decision_case import AuditLog, StateTransition


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _mock_session() -> MagicMock:
    """Sessão SQLAlchemy simulada para testes unitários puros."""
    session = MagicMock()
    session.add = MagicMock()
    return session


def _mock_case(state: DecisionState = DecisionState.DRAFT) -> MagicMock:
    """Instância ORM FinancialDecisionCase simulada."""
    case = MagicMock()
    case.id = uuid.uuid4()
    case.state = state
    return case


# ─────────────────────────────────────────────────────────────────────────────
#  FinancialImpactScorer
# ─────────────────────────────────────────────────────────────────────────────

class TestFinancialImpactScorer:
    """Verifica os 5 intervalos de scoring e o flag scenario_required."""

    # --- Score 1 (< 100k) ---
    @pytest.mark.parametrize("exposure", [0.01, 1.0, 50_000.0, 99_999.99])
    def test_score_1_low_exposure(self, exposure: float):
        result = FinancialImpactScorer.score(exposure)
        assert result.impact_score == 1
        assert result.scenario_required is False

    def test_score_1_boundary_below_100k(self):
        result = FinancialImpactScorer.score(99_999.99)
        assert result.impact_score == 1

    # --- Score 2 (100k–500k) ---
    @pytest.mark.parametrize("exposure", [100_000.0, 250_000.0, 499_999.99])
    def test_score_2_medium_exposure(self, exposure: float):
        result = FinancialImpactScorer.score(exposure)
        assert result.impact_score == 2
        assert result.scenario_required is False

    def test_score_2_at_lower_boundary(self):
        assert FinancialImpactScorer.score(100_000.0).impact_score == 2

    def test_score_2_below_upper_boundary(self):
        assert FinancialImpactScorer.score(499_999.99).impact_score == 2

    # --- Score 3 (500k–2M) ---
    @pytest.mark.parametrize("exposure", [500_000.0, 1_000_000.0, 1_999_999.99])
    def test_score_3_relevant_exposure(self, exposure: float):
        result = FinancialImpactScorer.score(exposure)
        assert result.impact_score == 3
        assert result.scenario_required is False

    def test_score_3_at_lower_boundary(self):
        assert FinancialImpactScorer.score(500_000.0).impact_score == 3

    # --- Score 4 (2M–10M inclusive) ---
    @pytest.mark.parametrize("exposure", [2_000_000.0, 5_000_000.0, 10_000_000.0])
    def test_score_4_high_exposure(self, exposure: float):
        result = FinancialImpactScorer.score(exposure)
        assert result.impact_score == 4
        assert result.scenario_required is True

    def test_score_4_at_lower_boundary(self):
        assert FinancialImpactScorer.score(2_000_000.0).impact_score == 4

    def test_score_4_at_upper_boundary_inclusive(self):
        """10M deve ser score 4 (inclusive no intervalo 2M–10M)."""
        assert FinancialImpactScorer.score(10_000_000.0).impact_score == 4

    # --- Score 5 (> 10M) ---
    @pytest.mark.parametrize("exposure", [10_000_000.01, 45_000_000.0, 1_000_000_000.0])
    def test_score_5_critical_exposure(self, exposure: float):
        result = FinancialImpactScorer.score(exposure)
        assert result.impact_score == 5
        assert result.scenario_required is True

    def test_score_5_just_above_10M(self):
        assert FinancialImpactScorer.score(10_000_000.01).impact_score == 5

    # --- ScoreResult imutabilidade ---
    def test_score_result_frozen(self):
        result = FinancialImpactScorer.score(500_000.0)
        with pytest.raises((AttributeError, TypeError)):
            result.impact_score = 99  # type: ignore[misc]

    # --- scenario_required consistência ---
    @pytest.mark.parametrize("exposure,expected_required", [
        (50_000.0,      False),
        (300_000.0,     False),
        (1_500_000.0,   False),
        (3_000_000.0,   True),
        (10_000_000.0,  True),
        (15_000_000.0,  True),
    ])
    def test_scenario_required_flag(self, exposure: float, expected_required: bool):
        result = FinancialImpactScorer.score(exposure)
        assert result.scenario_required is expected_required


# ─────────────────────────────────────────────────────────────────────────────
#  FrameworkSelector
# ─────────────────────────────────────────────────────────────────────────────

class TestFrameworkSelector:
    """Verifica o mapeamento determinístico framework para cada decision_type."""

    # --- Mapeamento base (sem external_agents) ---
    @pytest.mark.parametrize("decision_type,expected_framework", [
        (DecisionType.budget_adjustment,    FrameworkType.pdca),
        (DecisionType.forecast_revision,    FrameworkType.scenario_analysis),
        (DecisionType.capital_allocation,   FrameworkType.capital_allocation),
        (DecisionType.debt_structuring,     FrameworkType.trade_off),
        (DecisionType.liquidity_management, FrameworkType.risk_matrix),
        (DecisionType.risk_hedging,         FrameworkType.risk_matrix),
        (DecisionType.cost_reduction,       FrameworkType.trade_off),
        (DecisionType.investment_evaluation, FrameworkType.scenario_analysis),
    ])
    def test_base_mapping_without_external_agents(
        self, decision_type: DecisionType, expected_framework: FrameworkType
    ):
        result = FrameworkSelector.select(decision_type, external_agents_present=False)
        assert result == expected_framework

    # --- Game Theory ativada para tipos elegíveis ---
    @pytest.mark.parametrize("decision_type", [
        DecisionType.debt_structuring,
        DecisionType.investment_evaluation,
        DecisionType.capital_allocation,
    ])
    def test_game_theory_activated_for_eligible_types(self, decision_type: DecisionType):
        result = FrameworkSelector.select(decision_type, external_agents_present=True)
        assert result == FrameworkType.game_theory

    # --- Game Theory NÃO ativada para tipos não elegíveis ---
    @pytest.mark.parametrize("decision_type", [
        DecisionType.budget_adjustment,
        DecisionType.forecast_revision,
        DecisionType.liquidity_management,
        DecisionType.risk_hedging,
        DecisionType.cost_reduction,
    ])
    def test_game_theory_not_activated_for_ineligible_types(self, decision_type: DecisionType):
        result = FrameworkSelector.select(decision_type, external_agents_present=True)
        assert result != FrameworkType.game_theory

    # --- Cobertura completa de todos os tipos COM external_agents=True ---
    @pytest.mark.parametrize("decision_type,expected", [
        (DecisionType.budget_adjustment,    FrameworkType.pdca),
        (DecisionType.forecast_revision,    FrameworkType.scenario_analysis),
        (DecisionType.capital_allocation,   FrameworkType.game_theory),   # elegível
        (DecisionType.debt_structuring,     FrameworkType.game_theory),   # elegível
        (DecisionType.liquidity_management, FrameworkType.risk_matrix),
        (DecisionType.risk_hedging,         FrameworkType.risk_matrix),
        (DecisionType.cost_reduction,       FrameworkType.trade_off),
        (DecisionType.investment_evaluation, FrameworkType.game_theory),  # elegível
    ])
    def test_all_types_with_external_agents(
        self, decision_type: DecisionType, expected: FrameworkType
    ):
        result = FrameworkSelector.select(decision_type, external_agents_present=True)
        assert result == expected

    def test_base_framework_covers_all_decision_types(self):
        """Garante que _BASE_FRAMEWORK cobre todos os DecisionType definidos."""
        for dt in DecisionType:
            assert dt in _BASE_FRAMEWORK, f"DecisionType.{dt.value} não mapeado em _BASE_FRAMEWORK"

    def test_game_theory_eligible_is_subset_of_decision_types(self):
        all_types = set(DecisionType)
        assert _GAME_THEORY_ELIGIBLE.issubset(all_types)


# ─────────────────────────────────────────────────────────────────────────────
#  GameTheoryActivator
# ─────────────────────────────────────────────────────────────────────────────

class TestGameTheoryActivator:
    """Verifica o critério de ativação do módulo de Teoria dos Jogos."""

    # --- Ativação: tipos elegíveis + external_agents=True ---
    @pytest.mark.parametrize("decision_type", [
        DecisionType.debt_structuring,
        DecisionType.investment_evaluation,
        DecisionType.capital_allocation,
    ])
    def test_active_for_eligible_types_with_external_agents(self, decision_type: DecisionType):
        assert GameTheoryActivator.is_active(decision_type, external_agents_present=True) is True

    # --- Não ativado: tipos elegíveis SEM external_agents ---
    @pytest.mark.parametrize("decision_type", [
        DecisionType.debt_structuring,
        DecisionType.investment_evaluation,
        DecisionType.capital_allocation,
    ])
    def test_inactive_for_eligible_types_without_external_agents(self, decision_type: DecisionType):
        assert GameTheoryActivator.is_active(decision_type, external_agents_present=False) is False

    # --- Não ativado: tipos não elegíveis (mesmo com external_agents=True) ---
    @pytest.mark.parametrize("decision_type", [
        DecisionType.budget_adjustment,
        DecisionType.forecast_revision,
        DecisionType.liquidity_management,
        DecisionType.risk_hedging,
        DecisionType.cost_reduction,
    ])
    def test_inactive_for_ineligible_types_with_external_agents(self, decision_type: DecisionType):
        assert GameTheoryActivator.is_active(decision_type, external_agents_present=True) is False

    # --- Não ativado: tipos não elegíveis sem external_agents ---
    @pytest.mark.parametrize("decision_type", [
        DecisionType.budget_adjustment,
        DecisionType.forecast_revision,
    ])
    def test_inactive_for_ineligible_types_without_external_agents(self, decision_type: DecisionType):
        assert GameTheoryActivator.is_active(decision_type, external_agents_present=False) is False

    def test_eligible_types_constant_has_exactly_three_members(self):
        assert len(GAME_THEORY_ELIGIBLE_TYPES) == 3

    def test_eligible_types_are_frozenset(self):
        assert isinstance(GAME_THEORY_ELIGIBLE_TYPES, frozenset)


# ─────────────────────────────────────────────────────────────────────────────
#  AuditLogger
# ─────────────────────────────────────────────────────────────────────────────

class TestAuditLogger:
    """Verifica a criação correta de registros de auditoria."""

    def test_log_creates_audit_log_and_adds_to_session(self):
        session = _mock_session()
        case_id = uuid.uuid4()

        result = AuditLogger.log(
            session=session,
            action=AuditAction.CASE_CREATED,
            decision_case_id=case_id,
            payload={"title": "Test"},
        )

        assert isinstance(result, AuditLog)
        assert result.action == AuditAction.CASE_CREATED
        assert result.decision_case_id == case_id
        assert result.payload == {"title": "Test"}
        session.add.assert_called_once_with(result)

    def test_log_without_payload(self):
        session = _mock_session()
        result = AuditLogger.log(session=session, action=AuditAction.LLM_FALLBACK)
        assert result.payload is None
        assert result.decision_case_id is None

    def test_log_without_decision_case_id(self):
        session = _mock_session()
        result = AuditLogger.log(session=session, action=AuditAction.LLM_CALLED)
        assert result.decision_case_id is None

    @pytest.mark.parametrize("action", [
        AuditAction.CASE_CREATED,
        AuditAction.STATE_TRANSITION,
        AuditAction.LLM_CALLED,
        AuditAction.LLM_FALLBACK,
        AuditAction.DIVERGENCE_RECORDED,
    ])
    def test_all_audit_action_constants_are_strings(self, action: str):
        assert isinstance(action, str)
        assert len(action) > 0

    def test_all_action_constants_are_uppercase(self):
        actions = [
            AuditAction.CASE_CREATED,
            AuditAction.STATE_TRANSITION,
            AuditAction.LLM_CALLED,
            AuditAction.LLM_FALLBACK,
            AuditAction.DIVERGENCE_RECORDED,
        ]
        for action in actions:
            assert action == action.upper(), f"AuditAction '{action}' não está em maiúsculas"


# ─────────────────────────────────────────────────────────────────────────────
#  StateMachineController
# ─────────────────────────────────────────────────────────────────────────────

class TestStateMachineController:
    """Verifica todas as transições válidas, inválidas, e o estado terminal."""

    # --- Todas as 7 transições válidas do protocolo ---
    @pytest.mark.asyncio
    @pytest.mark.parametrize("from_state,to_state", [
        (DecisionState.DRAFT,        DecisionState.CLASSIFIED),
        (DecisionState.CLASSIFIED,   DecisionState.STRUCTURED),
        (DecisionState.STRUCTURED,   DecisionState.ANALYZED),
        (DecisionState.ANALYZED,     DecisionState.RECOMMENDED),
        (DecisionState.RECOMMENDED,  DecisionState.DECIDED),
        (DecisionState.DECIDED,      DecisionState.UNDER_REVIEW),
        (DecisionState.UNDER_REVIEW, DecisionState.CLOSED),
    ])
    async def test_valid_transitions(self, from_state: DecisionState, to_state: DecisionState):
        session = _mock_session()
        case = _mock_case(from_state)

        controller = StateMachineController()
        result = await controller.transition(case, to_state, session, triggered_by="test")

        assert case.state == to_state
        assert isinstance(result, StateTransition)
        assert result.from_state == from_state
        assert result.to_state == to_state
        assert result.decision_case_id == case.id

    @pytest.mark.asyncio
    async def test_transition_persists_state_transition_and_audit_log(self):
        """session.add() deve ser chamado 2x: StateTransition + AuditLog."""
        session = _mock_session()
        case = _mock_case(DecisionState.DRAFT)

        controller = StateMachineController()
        await controller.transition(case, DecisionState.CLASSIFIED, session)

        assert session.add.call_count == 2

        added_objects = [c.args[0] for c in session.add.call_args_list]
        types = {type(obj) for obj in added_objects}
        assert StateTransition in types
        assert AuditLog in types

    @pytest.mark.asyncio
    async def test_transition_sets_triggered_by(self):
        session = _mock_session()
        case = _mock_case(DecisionState.DRAFT)

        controller = StateMachineController()
        result = await controller.transition(
            case, DecisionState.CLASSIFIED, session, triggered_by="user:abc-123"
        )

        assert result.triggered_by == "user:abc-123"

    @pytest.mark.asyncio
    async def test_transition_without_triggered_by(self):
        session = _mock_session()
        case = _mock_case(DecisionState.DRAFT)

        controller = StateMachineController()
        result = await controller.transition(case, DecisionState.CLASSIFIED, session)

        assert result.triggered_by is None

    @pytest.mark.asyncio
    async def test_audit_log_payload_contains_transition_info(self):
        session = _mock_session()
        case = _mock_case(DecisionState.DRAFT)

        controller = StateMachineController()
        await controller.transition(
            case, DecisionState.CLASSIFIED, session, triggered_by="svc"
        )

        added_objects = [c.args[0] for c in session.add.call_args_list]
        audit_log = next(obj for obj in added_objects if isinstance(obj, AuditLog))

        assert audit_log.action == AuditAction.STATE_TRANSITION
        assert audit_log.payload["from_state"] == DecisionState.DRAFT.value
        assert audit_log.payload["to_state"] == DecisionState.CLASSIFIED.value
        assert audit_log.payload["triggered_by"] == "svc"

    # --- Transições inválidas → HTTP 409 ---
    @pytest.mark.asyncio
    @pytest.mark.parametrize("from_state,to_state", [
        (DecisionState.DRAFT,        DecisionState.ANALYZED),      # pula estado
        (DecisionState.DRAFT,        DecisionState.RECOMMENDED),   # pula vários estados
        (DecisionState.DRAFT,        DecisionState.DECIDED),       # pula vários estados
        (DecisionState.CLASSIFIED,   DecisionState.DRAFT),         # retrocesso proibido
        (DecisionState.STRUCTURED,   DecisionState.CLASSIFIED),    # retrocesso proibido
        (DecisionState.RECOMMENDED,  DecisionState.STRUCTURED),    # retrocesso proibido
        (DecisionState.DECIDED,      DecisionState.RECOMMENDED),   # retrocesso proibido
        (DecisionState.CLOSED,       DecisionState.DRAFT),         # estado terminal
        (DecisionState.CLOSED,       DecisionState.CLASSIFIED),    # estado terminal
    ])
    async def test_invalid_transitions_raise_error(
        self, from_state: DecisionState, to_state: DecisionState
    ):
        session = _mock_session()
        case = _mock_case(from_state)
        original_state = case.state

        controller = StateMachineController()
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            await controller.transition(case, to_state, session)

        exc = exc_info.value
        assert exc.status_code == 409
        assert exc.error == "INVALID_STATE_TRANSITION"
        assert from_state.value in exc.message
        assert to_state.value in exc.message
        # Estado NÃO deve ter mudado
        assert case.state == original_state

    @pytest.mark.asyncio
    async def test_invalid_transition_does_not_call_session_add(self):
        """Nenhum registro deve ser persistido quando a transição é inválida."""
        session = _mock_session()
        case = _mock_case(DecisionState.DRAFT)

        controller = StateMachineController()
        with pytest.raises(InvalidStateTransitionError):
            await controller.transition(case, DecisionState.DECIDED, session)

        session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_closed_is_terminal_state(self):
        """Estado CLOSED não permite nenhuma transição."""
        session = _mock_session()
        case = _mock_case(DecisionState.CLOSED)

        controller = StateMachineController()
        for target in DecisionState:
            if target == DecisionState.CLOSED:
                continue
            with pytest.raises(InvalidStateTransitionError):
                await controller.transition(case, target, session)

    @pytest.mark.asyncio
    async def test_same_state_transition_is_invalid(self):
        """Transição para o mesmo estado atual é inválida."""
        session = _mock_session()
        case = _mock_case(DecisionState.DRAFT)

        controller = StateMachineController()
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            await controller.transition(case, DecisionState.DRAFT, session)

        assert exc_info.value.status_code == 409

    # --- VALID_TRANSITIONS cobertura estrutural ---
    def test_valid_transitions_covers_all_states(self):
        """Todos os DecisionState devem aparecer como chave em VALID_TRANSITIONS."""
        for state in DecisionState:
            assert state in VALID_TRANSITIONS, (
                f"DecisionState.{state.value} não tem entrada em VALID_TRANSITIONS"
            )

    def test_valid_transitions_values_are_frozensets(self):
        for state, allowed in VALID_TRANSITIONS.items():
            assert isinstance(allowed, frozenset), (
                f"VALID_TRANSITIONS[{state.value}] deve ser frozenset"
            )

    def test_closed_has_empty_transitions(self):
        assert VALID_TRANSITIONS[DecisionState.CLOSED] == frozenset()

    def test_each_state_has_at_most_one_valid_successor(self):
        """O protocolo CFO é um grafo linear — cada estado tem no máximo 1 successor."""
        for state, allowed in VALID_TRANSITIONS.items():
            assert len(allowed) <= 1, (
                f"DecisionState.{state.value} tem múltiplos sucessores: {allowed}"
            )

    # --- Integração entre componentes ---
    @pytest.mark.asyncio
    async def test_double_transition_analyzed_to_recommended(self):
        """Simula o PUT /analyze que faz duas transições consecutivas:
        STRUCTURED → ANALYZED → RECOMMENDED."""
        session = _mock_session()
        case = _mock_case(DecisionState.STRUCTURED)

        controller = StateMachineController()

        # Fase 1: STRUCTURED → ANALYZED
        await controller.transition(case, DecisionState.ANALYZED, session)
        assert case.state == DecisionState.ANALYZED

        # Fase 2: ANALYZED → RECOMMENDED (automático)
        await controller.transition(case, DecisionState.RECOMMENDED, session)
        assert case.state == DecisionState.RECOMMENDED

        # 2 transições × 2 objetos (StateTransition + AuditLog) = 4 chamadas
        assert session.add.call_count == 4
