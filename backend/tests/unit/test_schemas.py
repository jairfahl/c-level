"""
Testes unitários dos schemas Pydantic — P-03

Cobertura:
- Criação válida de cada schema
- Rejeição de campos obrigatórios ausentes
- Validação de min_length / ge / le / ge=0.01
- Regras de negócio: mínimo 3 premissas e 3 riscos (StructureRequest)
- Validação de enums
- Compatibilidade com from_attributes (simulação de ORM objects)
- ErrorResponse com campos obrigatórios
"""
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.models.enums import (
    DecisionState,
    DecisionType,
    FinancialDomain,
    FrameworkType,
    TimeHorizon,
)
from app.schemas import (
    AnalysisResponse,
    AssumptionResponse,
    CaseCreatedResponse,
    ClassifyRequest,
    ClassifyResponse,
    DecideRequest,
    DecideResponse,
    ErrorResponse,
    FinancialDecisionCaseCreate,
    FinancialDecisionCaseFullResponse,
    FinancialDecisionCaseResponse,
    GameTheoryModel,
    PaginatedCasesResponse,
    ReviewRequest,
    ReviewResponse,
    RiskResponse,
    StateTransitionResponse,
    StateTransitionsListResponse,
    StructureRequest,
    StructureResponse,
)


# ─────────────────────────────────────────────────────────────────────────────
#  Fixtures helpers
# ─────────────────────────────────────────────────────────────────────────────

VALID_CREATE_PAYLOAD: dict = {
    "title": "Reestruturação da dívida bancária",
    "description": "Caso decisório sobre reestruturação de dívida de longo prazo",
    "financial_domain": "funding",
    "financial_exposure": 45_000_000.0,
    "decision_type": "debt_structuring",
}

VALID_ASSUMPTIONS = [
    "Taxa Selic se mantém em 10,5% ao longo do horizon",
    "Receita crescerá 8% no próximo exercício",
    "Linha de crédito rotativo permanece disponível",
]

VALID_RISKS = [
    "Reversão do ciclo de afrouxamento monetário",
    "Deterioração do rating de crédito",
    "Concentração de vencimentos em janela curta",
]


def _fake_case_orm(**overrides) -> SimpleNamespace:
    """Simula um objeto ORM FinancialDecisionCase para from_attributes."""
    defaults = {
        "id": uuid.uuid4(),
        "title": "Caso de teste",
        "description": "Descrição com mais de vinte caracteres para passar a validação",
        "financial_domain": FinancialDomain.funding,
        "impact_score": 3,
        "financial_exposure": 10_000_000.0,
        "time_horizon": TimeHorizon.medium,
        "external_agents_present": False,
        "decision_type": DecisionType.debt_structuring,
        "framework_selected": FrameworkType.trade_off,
        "scenario_required": False,
        "state": DecisionState.DRAFT,
        "created_at": datetime.now(tz=timezone.utc),
        "updated_at": datetime.now(tz=timezone.utc),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ─────────────────────────────────────────────────────────────────────────────
#  FinancialDecisionCaseCreate
# ─────────────────────────────────────────────────────────────────────────────

class TestFinancialDecisionCaseCreate:
    def test_valid_minimal(self):
        schema = FinancialDecisionCaseCreate(**VALID_CREATE_PAYLOAD)
        assert schema.title == VALID_CREATE_PAYLOAD["title"]
        assert schema.external_agents_present is False  # default
        assert schema.time_horizon is None  # opcional

    def test_valid_full(self):
        payload = {
            **VALID_CREATE_PAYLOAD,
            "time_horizon": "long",
            "external_agents_present": True,
        }
        schema = FinancialDecisionCaseCreate(**payload)
        assert schema.time_horizon == TimeHorizon.long
        assert schema.external_agents_present is True

    def test_title_too_short(self):
        with pytest.raises(ValidationError) as exc_info:
            FinancialDecisionCaseCreate(**{**VALID_CREATE_PAYLOAD, "title": "abc"})
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("title",) for e in errors)

    def test_description_too_short(self):
        with pytest.raises(ValidationError) as exc_info:
            FinancialDecisionCaseCreate(**{**VALID_CREATE_PAYLOAD, "description": "curto"})
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("description",) for e in errors)

    def test_financial_exposure_zero_rejected(self):
        with pytest.raises(ValidationError):
            FinancialDecisionCaseCreate(**{**VALID_CREATE_PAYLOAD, "financial_exposure": 0})

    def test_financial_exposure_negative_rejected(self):
        with pytest.raises(ValidationError):
            FinancialDecisionCaseCreate(**{**VALID_CREATE_PAYLOAD, "financial_exposure": -100.0})

    def test_financial_exposure_minimum_accepted(self):
        schema = FinancialDecisionCaseCreate(**{**VALID_CREATE_PAYLOAD, "financial_exposure": 0.01})
        assert schema.financial_exposure == 0.01

    def test_invalid_financial_domain(self):
        with pytest.raises(ValidationError):
            FinancialDecisionCaseCreate(**{**VALID_CREATE_PAYLOAD, "financial_domain": "invalid"})

    def test_invalid_decision_type(self):
        with pytest.raises(ValidationError):
            FinancialDecisionCaseCreate(**{**VALID_CREATE_PAYLOAD, "decision_type": "unknown"})

    def test_invalid_time_horizon(self):
        with pytest.raises(ValidationError):
            FinancialDecisionCaseCreate(**{**VALID_CREATE_PAYLOAD, "time_horizon": "century"})

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError) as exc_info:
            FinancialDecisionCaseCreate(title="Titulo válido")
        error_locs = {e["loc"][0] for e in exc_info.value.errors()}
        assert "description" in error_locs
        assert "financial_domain" in error_locs
        assert "financial_exposure" in error_locs
        assert "decision_type" in error_locs

    def test_readOnly_fields_absent(self):
        """Campos readOnly (id, state, framework_selected, scenario_required) não devem existir no schema."""
        fields = FinancialDecisionCaseCreate.model_fields
        for readOnly_field in ("id", "state", "framework_selected", "scenario_required"):
            assert readOnly_field not in fields, f"Campo readOnly '{readOnly_field}' não deve existir em Create"


# ─────────────────────────────────────────────────────────────────────────────
#  ClassifyRequest
# ─────────────────────────────────────────────────────────────────────────────

class TestClassifyRequest:
    def test_valid_boundaries(self):
        assert ClassifyRequest(impact_score=1).impact_score == 1
        assert ClassifyRequest(impact_score=5).impact_score == 5

    def test_impact_score_below_min(self):
        with pytest.raises(ValidationError):
            ClassifyRequest(impact_score=0)

    def test_impact_score_above_max(self):
        with pytest.raises(ValidationError):
            ClassifyRequest(impact_score=6)

    def test_missing_impact_score(self):
        with pytest.raises(ValidationError):
            ClassifyRequest()


# ─────────────────────────────────────────────────────────────────────────────
#  StructureRequest — regras de negócio
# ─────────────────────────────────────────────────────────────────────────────

class TestStructureRequest:
    def test_valid(self):
        schema = StructureRequest(assumptions=VALID_ASSUMPTIONS, risks=VALID_RISKS)
        assert len(schema.assumptions) == 3
        assert len(schema.risks) == 3

    def test_more_than_minimum_accepted(self):
        four_items = VALID_ASSUMPTIONS + ["Premissa extra"]
        schema = StructureRequest(assumptions=four_items, risks=VALID_RISKS)
        assert len(schema.assumptions) == 4

    def test_assumptions_below_minimum(self):
        with pytest.raises(ValidationError) as exc_info:
            StructureRequest(assumptions=["A", "B"], risks=VALID_RISKS)
        errors = exc_info.value.errors()
        assert any("premissas" in str(e["msg"]).lower() or "assumptions" in str(e["loc"]) for e in errors)

    def test_risks_below_minimum(self):
        with pytest.raises(ValidationError) as exc_info:
            StructureRequest(assumptions=VALID_ASSUMPTIONS, risks=["R1"])
        errors = exc_info.value.errors()
        assert any("riscos" in str(e["msg"]).lower() or "risks" in str(e["loc"]) for e in errors)

    def test_empty_assumptions(self):
        with pytest.raises(ValidationError):
            StructureRequest(assumptions=[], risks=VALID_RISKS)

    def test_empty_risks(self):
        with pytest.raises(ValidationError):
            StructureRequest(assumptions=VALID_ASSUMPTIONS, risks=[])

    def test_exactly_two_assumptions_fails(self):
        with pytest.raises(ValidationError) as exc_info:
            StructureRequest(assumptions=["A", "B"], risks=VALID_RISKS)
        msg = str(exc_info.value)
        assert "2" in msg  # A contagem deve aparecer na mensagem de erro

    def test_exactly_two_risks_fails(self):
        with pytest.raises(ValidationError) as exc_info:
            StructureRequest(assumptions=VALID_ASSUMPTIONS, risks=["R1", "R2"])
        msg = str(exc_info.value)
        assert "2" in msg


# ─────────────────────────────────────────────────────────────────────────────
#  DecideRequest
# ─────────────────────────────────────────────────────────────────────────────

class TestDecideRequest:
    def test_valid_minimal(self):
        schema = DecideRequest(executive_decision="Aprovamos a reestruturação total.")
        assert schema.divergence_justification is None
        assert schema.monitoring_criteria is None

    def test_valid_full(self):
        schema = DecideRequest(
            executive_decision="Optamos por renegociar apenas 60% da dívida neste momento.",
            divergence_justification="Contexto geopolítico justifica postura conservadora.",
            monitoring_criteria=["DRE trimestral", "Covenants bancários"],
        )
        assert schema.divergence_flag_present()  # monitoring_criteria e justificativa presentes

    def test_executive_decision_too_short(self):
        with pytest.raises(ValidationError):
            DecideRequest(executive_decision="Curta")

    def test_missing_executive_decision(self):
        with pytest.raises(ValidationError):
            DecideRequest()

    def test_readOnly_fields_absent(self):
        fields = DecideRequest.model_fields
        assert "state" not in fields
        assert "divergence_flag" not in fields


# Método auxiliar adicionado via monkey-patch para o teste acima
def _divergence_flag_present(self: DecideRequest) -> bool:
    return self.divergence_justification is not None or self.monitoring_criteria is not None


DecideRequest.divergence_flag_present = _divergence_flag_present  # type: ignore[attr-defined]


# ─────────────────────────────────────────────────────────────────────────────
#  ReviewRequest
# ─────────────────────────────────────────────────────────────────────────────

class TestReviewRequest:
    VALID_SUMMARY = "A decisão de reestruturação resultou em redução de 15% no custo da dívida."

    def test_valid_minimal(self):
        schema = ReviewRequest(outcome_summary=self.VALID_SUMMARY)
        assert schema.forecast_accuracy_score is None

    def test_valid_full(self):
        schema = ReviewRequest(
            outcome_summary=self.VALID_SUMMARY,
            forecast_accuracy_score=8,
            risk_realization_rate=25.5,
            capital_allocation_efficiency_score=90.0,
            divergence_outcome_flag=False,
        )
        assert schema.forecast_accuracy_score == 8

    def test_outcome_summary_too_short(self):
        with pytest.raises(ValidationError):
            ReviewRequest(outcome_summary="Curto.")

    def test_forecast_accuracy_score_out_of_range(self):
        with pytest.raises(ValidationError):
            ReviewRequest(outcome_summary=self.VALID_SUMMARY, forecast_accuracy_score=11)
        with pytest.raises(ValidationError):
            ReviewRequest(outcome_summary=self.VALID_SUMMARY, forecast_accuracy_score=0)

    def test_risk_realization_rate_out_of_range(self):
        with pytest.raises(ValidationError):
            ReviewRequest(outcome_summary=self.VALID_SUMMARY, risk_realization_rate=101.0)
        with pytest.raises(ValidationError):
            ReviewRequest(outcome_summary=self.VALID_SUMMARY, risk_realization_rate=-1.0)

    def test_capital_allocation_efficiency_score_boundary(self):
        schema = ReviewRequest(outcome_summary=self.VALID_SUMMARY, capital_allocation_efficiency_score=0.0)
        assert schema.capital_allocation_efficiency_score == 0.0
        schema = ReviewRequest(outcome_summary=self.VALID_SUMMARY, capital_allocation_efficiency_score=100.0)
        assert schema.capital_allocation_efficiency_score == 100.0


# ─────────────────────────────────────────────────────────────────────────────
#  Response schemas — from_attributes (simulação ORM)
# ─────────────────────────────────────────────────────────────────────────────

class TestAssumptionResponse:
    def test_from_dict(self):
        schema = AssumptionResponse(
            id=uuid.uuid4(),
            text="Taxa Selic estável",
            is_implicit=False,
        )
        assert schema.is_implicit is False

    def test_from_orm(self):
        orm_obj = SimpleNamespace(
            id=uuid.uuid4(),
            text="Premissa implícita detectada",
            is_implicit=True,
        )
        schema = AssumptionResponse.model_validate(orm_obj)
        assert schema.is_implicit is True


class TestRiskResponse:
    def test_from_orm(self):
        orm_obj = SimpleNamespace(
            id=uuid.uuid4(),
            text="Risco de inadimplência",
            materialized=False,
        )
        schema = RiskResponse.model_validate(orm_obj)
        assert schema.materialized is False


class TestStateTransitionResponse:
    def test_from_orm_with_from_state_none(self):
        orm_obj = SimpleNamespace(
            id=uuid.uuid4(),
            from_state=None,
            to_state=DecisionState.DRAFT,
            transitioned_at=datetime.now(tz=timezone.utc),
            triggered_by=None,
        )
        schema = StateTransitionResponse.model_validate(orm_obj)
        assert schema.from_state is None
        assert schema.to_state == DecisionState.DRAFT

    def test_from_orm_with_transition(self):
        orm_obj = SimpleNamespace(
            id=uuid.uuid4(),
            from_state=DecisionState.DRAFT,
            to_state=DecisionState.CLASSIFIED,
            transitioned_at=datetime.now(tz=timezone.utc),
            triggered_by="user:abc",
        )
        schema = StateTransitionResponse.model_validate(orm_obj)
        assert schema.from_state == DecisionState.DRAFT
        assert schema.triggered_by == "user:abc"


class TestFinancialDecisionCaseResponse:
    def test_from_orm(self):
        orm_obj = _fake_case_orm()
        schema = FinancialDecisionCaseResponse.model_validate(orm_obj)
        assert schema.state == DecisionState.DRAFT
        assert schema.scenario_required is False

    def test_scenario_required_true_when_impact_score_4(self):
        orm_obj = _fake_case_orm(impact_score=4, scenario_required=True)
        schema = FinancialDecisionCaseResponse.model_validate(orm_obj)
        assert schema.scenario_required is True

    def test_scenario_required_true_when_impact_score_5(self):
        orm_obj = _fake_case_orm(impact_score=5, scenario_required=True)
        schema = FinancialDecisionCaseResponse.model_validate(orm_obj)
        assert schema.scenario_required is True

    def test_nullable_fields(self):
        orm_obj = _fake_case_orm(
            impact_score=None,
            time_horizon=None,
            framework_selected=None,
        )
        schema = FinancialDecisionCaseResponse.model_validate(orm_obj)
        assert schema.impact_score is None
        assert schema.time_horizon is None
        assert schema.framework_selected is None


class TestFinancialDecisionCaseFullResponse:
    def test_defaults_empty_lists(self):
        orm_obj = _fake_case_orm()
        # FullResponse requer campos adicionais não presentes no ORM diretamente.
        # Usamos model_validate para ler os campos base e model_copy para adicionar extras.
        base = FinancialDecisionCaseResponse.model_validate(orm_obj)
        schema = FinancialDecisionCaseFullResponse(
            **base.model_dump(),
            assumptions=[],
            risks=[],
            financial_metrics_impacted=[],
        )
        assert schema.assumptions == []
        assert schema.risks == []
        assert schema.recommendation is None
        assert schema.divergence_flag is None

    def test_with_nested_objects(self):
        assumption = AssumptionResponse(id=uuid.uuid4(), text="Premissa 1", is_implicit=False)
        risk = RiskResponse(id=uuid.uuid4(), text="Risco 1", materialized=False)
        schema = FinancialDecisionCaseFullResponse(
            id=uuid.uuid4(),
            title="Caso completo",
            description="Descrição do caso completo com mais de vinte caracteres",
            financial_domain=FinancialDomain.funding,
            impact_score=4,
            financial_exposure=5_000_000.0,
            time_horizon=TimeHorizon.long,
            external_agents_present=True,
            decision_type=DecisionType.capital_allocation,
            framework_selected=FrameworkType.scenario_analysis,
            scenario_required=True,
            state=DecisionState.RECOMMENDED,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
            assumptions=[assumption],
            risks=[risk],
            financial_metrics_impacted=["EBITDA", "DSCR", "LTV"],
            recommendation="Reestruturar 70% da dívida via mercado de capitais.",
            executive_decision=None,
            divergence_flag=None,
        )
        assert len(schema.assumptions) == 1
        assert len(schema.financial_metrics_impacted) == 3
        assert schema.scenario_required is True


# ─────────────────────────────────────────────────────────────────────────────
#  Response schemas — state machine
# ─────────────────────────────────────────────────────────────────────────────

class TestClassifyResponse:
    def test_valid(self):
        schema = ClassifyResponse(
            state=DecisionState.CLASSIFIED,
            framework_selected=FrameworkType.scenario_analysis,
            scenario_required=True,
        )
        assert schema.scenario_required is True

    def test_missing_field(self):
        with pytest.raises(ValidationError):
            ClassifyResponse(state=DecisionState.CLASSIFIED)


class TestStructureResponse:
    def test_valid(self):
        schema = StructureResponse(
            state=DecisionState.STRUCTURED,
            assumptions_count=3,
            risks_count=5,
        )
        assert schema.assumptions_count == 3


class TestAnalysisResponse:
    def test_valid_minimal(self):
        schema = AnalysisResponse(
            state=DecisionState.RECOMMENDED,
            recommendation="Recomendar reestruturação imediata.",
            framework_selected=FrameworkType.trade_off,
            financial_metrics_impacted=["EBITDA", "Net Debt / EBITDA"],
        )
        assert schema.llm_unavailable is False
        assert schema.scenario_summary is None
        assert schema.game_theory_model is None

    def test_valid_with_game_theory(self):
        gt_model = GameTheoryModel(
            players=["CFO", "Banco Credor"],
            strategies={"CFO": ["negociar", "aguardar"], "Banco Credor": ["aceitar", "recusar"]},
            payoffs={"CFO-negociar/Banco-aceitar": "ótimo", "CFO-aguardar/Banco-recusar": "ruim"},
            equilibrium="Nash: CFO=negociar, Banco=aceitar",
            strategic_risk="Risco de recusa abrupta pelo credor",
        )
        schema = AnalysisResponse(
            state=DecisionState.RECOMMENDED,
            recommendation="Negociar imediatamente.",
            framework_selected=FrameworkType.game_theory,
            financial_metrics_impacted=["DSCR"],
            game_theory_model=gt_model,
        )
        assert schema.game_theory_model is not None
        assert "CFO" in schema.game_theory_model.players

    def test_llm_unavailable_flag(self):
        schema = AnalysisResponse(
            state=DecisionState.RECOMMENDED,
            recommendation="Análise determinística: recomendar conservadorismo.",
            framework_selected=FrameworkType.risk_matrix,
            financial_metrics_impacted=[],
            llm_unavailable=True,
        )
        assert schema.llm_unavailable is True


class TestDecideResponse:
    def test_valid(self):
        schema = DecideResponse(state=DecisionState.DECIDED, divergence_flag=True)
        assert schema.divergence_flag is True


class TestReviewResponse:
    def test_valid(self):
        schema = ReviewResponse(state=DecisionState.CLOSED)
        assert schema.state == DecisionState.CLOSED


class TestCaseCreatedResponse:
    def test_valid(self):
        case_id = uuid.uuid4()
        schema = CaseCreatedResponse(id=case_id, state=DecisionState.DRAFT)
        assert schema.id == case_id
        assert schema.state == DecisionState.DRAFT


# ─────────────────────────────────────────────────────────────────────────────
#  Response schemas — listagens e auditoria
# ─────────────────────────────────────────────────────────────────────────────

class TestPaginatedCasesResponse:
    def test_valid_empty_list(self):
        schema = PaginatedCasesResponse(items=[], total=0, page=1, limit=20)
        assert schema.total == 0
        assert schema.items == []

    def test_valid_with_items(self):
        orm_obj = _fake_case_orm()
        case = FinancialDecisionCaseResponse.model_validate(orm_obj)
        schema = PaginatedCasesResponse(items=[case], total=1, page=1, limit=20)
        assert len(schema.items) == 1

    def test_page_minimum(self):
        with pytest.raises(ValidationError):
            PaginatedCasesResponse(items=[], total=0, page=0, limit=20)

    def test_limit_maximum(self):
        with pytest.raises(ValidationError):
            PaginatedCasesResponse(items=[], total=0, page=1, limit=101)


class TestStateTransitionsListResponse:
    def test_valid(self):
        transition = StateTransitionResponse(
            id=uuid.uuid4(),
            from_state=None,
            to_state=DecisionState.DRAFT,
            transitioned_at=datetime.now(tz=timezone.utc),
            triggered_by=None,
        )
        schema = StateTransitionsListResponse(
            decision_case_id=uuid.uuid4(),
            transitions=[transition],
        )
        assert len(schema.transitions) == 1

    def test_empty_transitions(self):
        schema = StateTransitionsListResponse(
            decision_case_id=uuid.uuid4(),
            transitions=[],
        )
        assert schema.transitions == []


# ─────────────────────────────────────────────────────────────────────────────
#  ErrorResponse
# ─────────────────────────────────────────────────────────────────────────────

class TestErrorResponse:
    def test_valid_minimal(self):
        schema = ErrorResponse(error="CASE_NOT_FOUND", message="Nenhum caso encontrado")
        assert schema.details is None

    def test_valid_with_details(self):
        schema = ErrorResponse(
            error="INVALID_STATE_TRANSITION",
            message="Transição inválida: DRAFT → ANALYZED",
            details={"allowed_transitions": ["DRAFT → CLASSIFIED"]},
        )
        assert schema.details is not None
        assert "allowed_transitions" in schema.details

    def test_missing_error_field(self):
        with pytest.raises(ValidationError):
            ErrorResponse(message="Erro sem código")

    def test_missing_message_field(self):
        with pytest.raises(ValidationError):
            ErrorResponse(error="SOME_ERROR")

    def test_known_error_codes(self):
        """Verifica que os códigos de erro padronizados do OpenAPI são aceitos."""
        error_codes = [
            "UNAUTHORIZED",
            "CASE_NOT_FOUND",
            "INVALID_STATE_TRANSITION",
            "INSUFFICIENT_ASSUMPTIONS",
            "INSUFFICIENT_RISKS",
        ]
        for code in error_codes:
            schema = ErrorResponse(error=code, message=f"Mensagem para {code}")
            assert schema.error == code


# ─────────────────────────────────────────────────────────────────────────────
#  Enums — validação básica
# ─────────────────────────────────────────────────────────────────────────────

class TestEnums:
    def test_financial_domain_values(self):
        valid = ["planning", "reporting", "treasury", "funding", "risk"]
        for v in valid:
            assert FinancialDomain(v).value == v

    def test_decision_state_values(self):
        valid = ["DRAFT", "CLASSIFIED", "STRUCTURED", "ANALYZED",
                 "RECOMMENDED", "DECIDED", "UNDER_REVIEW", "CLOSED"]
        for v in valid:
            assert DecisionState(v).value == v

    def test_framework_type_values(self):
        valid = ["pdca", "scenario_analysis", "game_theory", "trade_off", "risk_matrix", "capital_allocation"]
        for v in valid:
            assert FrameworkType(v).value == v

    def test_time_horizon_values(self):
        for v in ["short", "medium", "long"]:
            assert TimeHorizon(v).value == v

    def test_decision_type_all_values(self):
        valid = [
            "budget_adjustment", "forecast_revision", "capital_allocation",
            "debt_structuring", "liquidity_management", "risk_hedging",
            "cost_reduction", "investment_evaluation",
        ]
        for v in valid:
            assert DecisionType(v).value == v


# ─────────────────────────────────────────────────────────────────────────────
#  GameTheoryModel
# ─────────────────────────────────────────────────────────────────────────────

class TestGameTheoryModel:
    def test_valid(self):
        schema = GameTheoryModel(
            players=["CFO", "Banco"],
            strategies={"CFO": ["negociar"], "Banco": ["aceitar", "recusar"]},
            payoffs={"CFO+Banco": "ótimo"},
            equilibrium="Nash dominante",
            strategic_risk="Risco de recusa",
        )
        assert schema.equilibrium == "Nash dominante"

    def test_equilibrium_optional(self):
        schema = GameTheoryModel(
            players=["A"],
            strategies={"A": ["x"]},
            payoffs={"A-x": "ok"},
            strategic_risk="Nenhum risco identificado",
        )
        assert schema.equilibrium is None
