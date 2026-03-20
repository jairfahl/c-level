"""
Integration tests: Complete Decision Protocol Flow (P-07)

Covers:
1. Full DRAFT → CLASSIFIED → STRUCTURED → ANALYZED → RECOMMENDED → DECIDED → CLOSED flow
2. Divergence flow variant (CFO diverges from mentor recommendation)
3. GET list with query-param filters (domain / state / decision_type)
4. /health and / health-check endpoints
5. Auth unit — get_current_user success path (covers auth.py:30)
6. LLMClient.complete() with mocked Anthropic backend (covers llm/client.py:47-54)
7. LLMCache default Redis initialization (covers cache.py:66)
8. Parser markdown fence with malformed JSON fallback (covers parser.py:77-78)
9. InsufficientAssumptionsError / InsufficientRisksError constructors (covers exceptions.py:28,37)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from httpx import ASGITransport, AsyncClient

from app.core.auth import create_access_token, get_current_user
from app.core.database import get_db
from app.core.exceptions import InsufficientAssumptionsError, InsufficientRisksError
from app.api.routers.state_machine import get_llm_service
from app.llm.cache import LLMCache
from app.llm.client import LLMClient
from app.llm.parser import LLMAnalysisResult, LLMParseError, ResponseParser
from app.main import app
from app.models.enums import DecisionState, DecisionType, FinancialDomain, FrameworkType

BASE_URL = "http://test"
API = "/v1/financial-decision-cases"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def make_mock_case(**kwargs) -> MagicMock:
    case = MagicMock()
    case.id = kwargs.get("id", uuid.uuid4())
    case.title = kwargs.get("title", "Reestruturação da dívida bancária")
    case.description = kwargs.get("description", "Caso sobre dívida com bancos credores nacionais")
    case.financial_domain = kwargs.get("financial_domain", FinancialDomain.funding)
    case.impact_score = kwargs.get("impact_score", 4)
    case.financial_exposure = kwargs.get("financial_exposure", 45_000_000.0)
    case.time_horizon = kwargs.get("time_horizon", None)
    case.external_agents_present = kwargs.get("external_agents_present", True)
    case.decision_type = kwargs.get("decision_type", DecisionType.debt_structuring)
    case.framework_selected = kwargs.get("framework_selected", FrameworkType.game_theory)
    case.scenario_required = kwargs.get("scenario_required", True)
    case.state = kwargs.get("state", DecisionState.DRAFT)
    case.created_at = kwargs.get("created_at", _now())
    case.updated_at = kwargs.get("updated_at", _now())
    case.assumptions = kwargs.get("assumptions", [])
    case.risks = kwargs.get("risks", [])
    case.metrics_impacted = kwargs.get("metrics_impacted", [])
    case.decisions = kwargs.get("decisions", [])
    return case


def _make_assumption(text: str) -> MagicMock:
    a = MagicMock()
    a.id = uuid.uuid4()
    a.text = text
    a.is_implicit = False
    a.created_at = _now()
    return a


def _make_risk(text: str) -> MagicMock:
    r = MagicMock()
    r.id = uuid.uuid4()
    r.text = text
    r.materialized = False
    r.created_at = _now()
    return r


def _make_transition(from_state, to_state, case_id=None) -> MagicMock:
    t = MagicMock()
    t.id = uuid.uuid4()
    t.decision_case_id = case_id or uuid.uuid4()
    t.from_state = from_state
    t.to_state = to_state
    t.transitioned_at = _now()
    t.triggered_by = "cfo-test-01"
    return t


def _exec(scalar_one_or_none=None, scalars_all=None, scalar=None) -> MagicMock:
    r = MagicMock()
    r.scalar_one_or_none.return_value = scalar_one_or_none
    r.scalars.return_value.all.return_value = scalars_all or []
    r.scalar.return_value = scalar if scalar is not None else 0
    return r


# ---------------------------------------------------------------------------
# Shared test payloads
# ---------------------------------------------------------------------------

CASE_PAYLOAD = {
    "title": "Reestruturação da dívida bancária",
    "description": "Caso sobre dívida de longo prazo com bancos credores nacionais",
    "financial_domain": "funding",
    "financial_exposure": 45_000_000.0,
    "decision_type": "debt_structuring",
    "external_agents_present": True,
}

STRUCTURE_PAYLOAD = {
    "assumptions": [
        "Selic estável em 10.5%",
        "Receita cresce +8% a.a.",
        "Crédito disponível no mercado",
    ],
    "risks": [
        "Alta de juros acima de 2pp",
        "Downgrade de rating",
        "Concentração de vencimentos",
    ],
}

REVIEW_PAYLOAD = {
    "outcome_summary": "Reestruturação reduziu custo da dívida em 15% conforme projetado.",
    "forecast_accuracy_score": 8,
    "risk_realization_rate": 20.0,
    "capital_allocation_efficiency_score": 90.0,
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_headers() -> dict:
    token = create_access_token({"sub": "cfo-test-01"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def llm_result() -> LLMAnalysisResult:
    return LLMAnalysisResult(
        recommendation="Reestruturar 100% da dívida em 3 tranches anuais com hedge cambial.",
        financial_metrics_impacted=["EBITDA", "VPL", "Custo Médio Ponderado de Capital"],
        scenario_summary="Cenário base: redução de 15% no custo da dívida em 24 meses.",
        implicit_assumptions_found=["Taxa de câmbio estável no período"],
        game_theory_model=None,
        llm_unavailable=False,
    )


@pytest.fixture
def mock_llm(llm_result) -> MagicMock:
    service = MagicMock()
    service.analyze = AsyncMock(return_value=llm_result)
    return service


@pytest.fixture
def full_override(mock_session, mock_llm):
    async def _get_db():
        yield mock_session

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_current_user] = lambda: {"sub": "cfo-test-01"}
    app.dependency_overrides[get_llm_service] = lambda: mock_llm
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 1. Full Decision Protocol Flow
# ---------------------------------------------------------------------------

class TestCompleteDecisionProtocolFlow:
    """
    Validates the complete DRAFT → CLASSIFIED → STRUCTURED → ANALYZED →
    RECOMMENDED → DECIDED → UNDER_REVIEW → CLOSED cycle in a single
    sequential test.
    """

    async def test_full_protocol_flow_no_divergence(
        self, full_override, mock_session, llm_result, auth_headers
    ):
        case_id = uuid.uuid4()

        # Single persistent mock case — StateMachineController mutates .state in place
        mock_case = make_mock_case(
            id=case_id,
            state=DecisionState.DRAFT,
            assumptions=[
                _make_assumption("Selic estável em 10.5%"),
                _make_assumption("Receita cresce +8% a.a."),
                _make_assumption("Crédito disponível no mercado"),
            ],
            risks=[
                _make_risk("Alta de juros acima de 2pp"),
                _make_risk("Downgrade de rating"),
                _make_risk("Concentração de vencimentos"),
            ],
        )
        mock_session.execute.return_value = _exec(scalar_one_or_none=mock_case)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:

            # ── Step 1: CREATE (DRAFT) ───────────────────────────────────────
            with patch(
                "app.api.routers.financial_decision_cases.FinancialDecisionCase",
                return_value=mock_case,
            ):
                r = await client.post(API, headers=auth_headers, json=CASE_PAYLOAD)

            assert r.status_code == 201
            assert r.json()["state"] == "DRAFT"
            assert r.json()["id"] == str(case_id)

            # ── Step 2: CLASSIFY → CLASSIFIED ───────────────────────────────
            r = await client.put(
                f"{API}/{case_id}/classify",
                headers=auth_headers,
                json={"impact_score": 4},
            )
            assert r.status_code == 200
            data = r.json()
            assert data["state"] == "CLASSIFIED"
            assert data["framework_selected"] == "game_theory"  # debt_structuring + external_agents
            assert data["scenario_required"] is True            # impact_score=4 ≥ 4

            # ── Step 3: STRUCTURE → STRUCTURED ──────────────────────────────
            r = await client.put(
                f"{API}/{case_id}/structure",
                headers=auth_headers,
                json=STRUCTURE_PAYLOAD,
            )
            assert r.status_code == 200
            data = r.json()
            assert data["state"] == "STRUCTURED"
            assert data["assumptions_count"] == 3
            assert data["risks_count"] == 3

            # ── Step 4: ANALYZE → RECOMMENDED (double transition + LLM) ─────
            r = await client.put(f"{API}/{case_id}/analyze", headers=auth_headers)
            assert r.status_code == 200
            data = r.json()
            assert data["state"] == "RECOMMENDED"
            assert data["recommendation"] == llm_result.recommendation
            assert data["framework_selected"] == "game_theory"
            assert data["llm_unavailable"] is False
            assert set(data["financial_metrics_impacted"]) == {
                "EBITDA", "VPL", "Custo Médio Ponderado de Capital"
            }
            assert data["implicit_assumptions_found"] == ["Taxa de câmbio estável no período"]
            assert data["scenario_summary"] is not None

            # ── Step 5: DECIDE → DECIDED (aligned with recommendation) ──────
            mock_decision = MagicMock()
            mock_decision.recommendation = llm_result.recommendation
            mock_decision.executive_decision = None
            mock_decision.divergence_flag = False
            mock_case.decisions = [mock_decision]

            r = await client.put(
                f"{API}/{case_id}/decide",
                headers=auth_headers,
                json={
                    "executive_decision": "Aprovamos a reestruturação completa conforme recomendado pelo Mentor CFO."
                },
            )
            assert r.status_code == 200
            data = r.json()
            assert data["state"] == "DECIDED"
            assert data["divergence_flag"] is False

            # ── Step 6: AUDIT TRAIL — 6 transitions recorded ─────────────────
            transitions = [
                _make_transition(None, DecisionState.DRAFT, case_id),
                _make_transition(DecisionState.DRAFT, DecisionState.CLASSIFIED, case_id),
                _make_transition(DecisionState.CLASSIFIED, DecisionState.STRUCTURED, case_id),
                _make_transition(DecisionState.STRUCTURED, DecisionState.ANALYZED, case_id),
                _make_transition(DecisionState.ANALYZED, DecisionState.RECOMMENDED, case_id),
                _make_transition(DecisionState.RECOMMENDED, DecisionState.DECIDED, case_id),
            ]
            mock_session.execute.side_effect = [
                _exec(scalar_one_or_none=case_id),    # case existence check
                _exec(scalars_all=transitions),        # transitions list
            ]

            r = await client.get(f"{API}/{case_id}/state-transitions", headers=auth_headers)
            assert r.status_code == 200
            data = r.json()
            assert data["decision_case_id"] == str(case_id)
            assert len(data["transitions"]) == 6
            to_states = [t["to_state"] for t in data["transitions"]]
            assert to_states == [
                "DRAFT", "CLASSIFIED", "STRUCTURED", "ANALYZED", "RECOMMENDED", "DECIDED"
            ]

            # Reset execute after side_effect
            mock_session.execute.side_effect = None
            mock_session.execute.return_value = _exec(scalar_one_or_none=mock_case)

            # ── Step 7: REVIEW → CLOSED (DECIDED → UNDER_REVIEW → CLOSED) ───
            r = await client.put(
                f"{API}/{case_id}/review",
                headers=auth_headers,
                json=REVIEW_PAYLOAD,
            )
            assert r.status_code == 200
            assert r.json()["state"] == "CLOSED"

    async def test_full_protocol_flow_with_divergence(
        self, full_override, mock_session, llm_result, auth_headers
    ):
        """CFO diverges from the LLM recommendation — divergence_flag=True recorded."""
        case_id = uuid.uuid4()
        mock_case = make_mock_case(id=case_id, state=DecisionState.DRAFT)
        mock_session.execute.return_value = _exec(scalar_one_or_none=mock_case)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            # POST
            with patch(
                "app.api.routers.financial_decision_cases.FinancialDecisionCase",
                return_value=mock_case,
            ):
                r = await client.post(API, headers=auth_headers, json=CASE_PAYLOAD)
            assert r.status_code == 201

            # CLASSIFY
            r = await client.put(
                f"{API}/{case_id}/classify", headers=auth_headers, json={"impact_score": 3}
            )
            assert r.json()["state"] == "CLASSIFIED"
            # scenario_required is a mock attribute — tested in unit tests, not here

            # STRUCTURE
            r = await client.put(
                f"{API}/{case_id}/structure", headers=auth_headers, json=STRUCTURE_PAYLOAD
            )
            assert r.json()["state"] == "STRUCTURED"

            # ANALYZE
            r = await client.put(f"{API}/{case_id}/analyze", headers=auth_headers)
            assert r.json()["state"] == "RECOMMENDED"

            # DECIDE — with divergence
            mock_decision = MagicMock()
            mock_decision.recommendation = llm_result.recommendation
            mock_decision.executive_decision = None
            mock_decision.divergence_flag = False
            mock_case.decisions = [mock_decision]

            r = await client.put(
                f"{API}/{case_id}/decide",
                headers=auth_headers,
                json={
                    "executive_decision": "Optamos por apenas 60% da reestruturação proposta pelo Mentor.",
                    "divergence_justification": "Contexto geopolítico exige postura conservadora.",
                    "monitoring_criteria": ["DRE trimestral", "Covenants bancários"],
                },
            )
            assert r.status_code == 200
            assert r.json()["state"] == "DECIDED"
            assert r.json()["divergence_flag"] is True

            # REVIEW (from UNDER_REVIEW directly, by starting from DECIDED)
            r = await client.put(
                f"{API}/{case_id}/review",
                headers=auth_headers,
                json={**REVIEW_PAYLOAD, "divergence_outcome_flag": True},
            )
            assert r.status_code == 200
            assert r.json()["state"] == "CLOSED"


# ---------------------------------------------------------------------------
# 2. GET /financial-decision-cases with query filters
#    Closes: financial_decision_cases.py lines 150, 152, 154, 159, 165
# ---------------------------------------------------------------------------

class TestListWithFilters:
    async def test_filter_by_domain(self, full_override, mock_session, auth_headers):
        mock_case = make_mock_case(financial_domain=FinancialDomain.funding)
        mock_session.execute.side_effect = [
            _exec(scalar=1),
            _exec(scalars_all=[mock_case]),
        ]
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            r = await client.get(f"{API}?domain=funding", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["total"] == 1

    async def test_filter_by_state(self, full_override, mock_session, auth_headers):
        mock_case = make_mock_case(state=DecisionState.CLASSIFIED)
        mock_session.execute.side_effect = [
            _exec(scalar=1),
            _exec(scalars_all=[mock_case]),
        ]
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            r = await client.get(f"{API}?state=CLASSIFIED", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["total"] == 1

    async def test_filter_by_decision_type(self, full_override, mock_session, auth_headers):
        mock_case = make_mock_case(decision_type=DecisionType.debt_structuring)
        mock_session.execute.side_effect = [
            _exec(scalar=1),
            _exec(scalars_all=[mock_case]),
        ]
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            r = await client.get(f"{API}?decision_type=debt_structuring", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["total"] == 1

    async def test_all_filters_combined(self, full_override, mock_session, auth_headers):
        mock_case = make_mock_case(
            financial_domain=FinancialDomain.funding,
            state=DecisionState.STRUCTURED,
            decision_type=DecisionType.debt_structuring,
        )
        mock_session.execute.side_effect = [
            _exec(scalar=1),
            _exec(scalars_all=[mock_case]),
        ]
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            r = await client.get(
                f"{API}?domain=funding&state=STRUCTURED&decision_type=debt_structuring",
                headers=auth_headers,
            )
        assert r.status_code == 200
        assert r.json()["total"] == 1
        assert r.json()["items"][0]["state"] == "STRUCTURED"

    async def test_pagination_params(self, full_override, mock_session, auth_headers):
        mock_session.execute.side_effect = [
            _exec(scalar=50),
            _exec(scalars_all=[]),
        ]
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            r = await client.get(f"{API}?page=3&limit=10", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["page"] == 3
        assert data["limit"] == 10
        assert data["total"] == 50


# ---------------------------------------------------------------------------
# 3. Health endpoints — closes main.py lines 50, 55
# ---------------------------------------------------------------------------

class TestHealthEndpoints:
    async def test_health_check(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            r = await client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["service"] == "mentor-cfo"
        assert data["version"] == "2.0.0"

    async def test_root(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            r = await client.get("/")
        assert r.status_code == 200
        assert "Mentor" in r.json()["message"]


# ---------------------------------------------------------------------------
# 4. Auth unit tests — closes auth.py line 30 (return payload)
# ---------------------------------------------------------------------------

class TestAuthUnit:
    async def test_valid_jwt_returns_payload(self):
        token = create_access_token({"sub": "cfo-unit-test"})
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        payload = await get_current_user(creds)
        assert payload["sub"] == "cfo-unit-test"

    async def test_invalid_jwt_raises_unauthorized(self):
        from app.core.exceptions import UnauthorizedError

        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad.token.here")
        with pytest.raises(UnauthorizedError):
            await get_current_user(creds)


# ---------------------------------------------------------------------------
# 5. LLMClient — closes llm/client.py lines 47-54
# ---------------------------------------------------------------------------

class TestLLMClient:
    async def test_complete_returns_text(self):
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Resposta do Claude")]

        mock_anthropic = MagicMock()
        mock_anthropic.messages.create = AsyncMock(return_value=mock_message)

        client = LLMClient()
        client._client = mock_anthropic

        result = await client.complete("system prompt", "user prompt")

        assert result == "Resposta do Claude"
        mock_anthropic.messages.create.assert_awaited_once()
        call_kwargs = mock_anthropic.messages.create.call_args.kwargs
        assert call_kwargs["temperature"] == 0
        assert {"role": "user", "content": "user prompt"} in call_kwargs["messages"]


# ---------------------------------------------------------------------------
# 6. LLMCache default Redis init — closes cache.py line 66
# ---------------------------------------------------------------------------

class TestLLMCacheDefaultInit:
    async def test_get_redis_lazy_init(self):
        """LLMCache creates Redis connection lazily when no client is provided."""
        cache = LLMCache()   # no client → _redis is None
        assert cache._redis is None

        fake_redis = AsyncMock()
        fake_redis.get = AsyncMock(return_value=None)

        with patch("app.llm.cache.aioredis.from_url", return_value=fake_redis) as mock_from_url:
            result = await cache.get("some-key")   # triggers _get_redis() → line 66

        assert result is None  # cache miss
        mock_from_url.assert_called_once()


# ---------------------------------------------------------------------------
# 7. Parser markdown fence with bad JSON — closes parser.py lines 77-78
# ---------------------------------------------------------------------------

class TestResponseParserEdgeCases:
    def test_fence_with_invalid_json_raises_parse_error(self):
        """Fence matches but content is malformed JSON → JSONDecodeError caught (lines 77-78).
        No valid raw JSON follows → LLMParseError is ultimately raised."""
        raw_text = "Análise:\n```json\n{invalid: json, missing: quotes}\n```\nSem JSON válido aqui."
        with pytest.raises(LLMParseError):
            ResponseParser.parse(raw_text)

    def test_no_json_raises_parse_error(self):
        with pytest.raises(LLMParseError):
            ResponseParser.parse("Este texto não contém nenhum JSON válido.")

    def test_json_fails_schema_validation_raises_parse_error(self):
        """Valid JSON but missing required 'recommendation' field → LLMParseError."""
        with pytest.raises(LLMParseError, match="schema validation"):
            ResponseParser.parse('{"not_a_recommendation": "missing field"}')


# ---------------------------------------------------------------------------
# 8. Exception constructors — closes exceptions.py lines 28, 37
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 9. scenario_required ORM property — closes financial_decision_case.py line 43
# ---------------------------------------------------------------------------

class TestScenarioRequiredProperty:
    """Validates the @property directly on a real (unsaved) ORM instance."""

    def test_scenario_required_true_when_score_gte_4(self):
        from app.models.financial_decision_case import FinancialDecisionCase

        case = FinancialDecisionCase(
            title="Test Case",
            description="A sufficiently long description for the test case.",
            financial_domain=FinancialDomain.funding,
            financial_exposure=50_000_000.0,
            external_agents_present=False,
            decision_type=DecisionType.debt_structuring,
        )
        case.impact_score = 4
        assert case.scenario_required is True

        case.impact_score = 5
        assert case.scenario_required is True

    def test_scenario_required_false_when_score_lt_4(self):
        from app.models.financial_decision_case import FinancialDecisionCase

        case = FinancialDecisionCase(
            title="Test Case",
            description="A sufficiently long description for the test case.",
            financial_domain=FinancialDomain.funding,
            financial_exposure=100_000.0,
            external_agents_present=False,
            decision_type=DecisionType.budget_adjustment,
        )
        case.impact_score = 3
        assert case.scenario_required is False

        case.impact_score = None
        assert case.scenario_required is False


# ---------------------------------------------------------------------------
# 10. Exception constructors — closes exceptions.py lines 28, 37
# ---------------------------------------------------------------------------

class TestExceptionConstructors:
    def test_insufficient_assumptions_error(self):
        err = InsufficientAssumptionsError(2)
        assert err.error == "INSUFFICIENT_ASSUMPTIONS"
        assert "3" in err.message
        assert "2" in err.message
        assert err.status_code == 400

    def test_insufficient_risks_error(self):
        err = InsufficientRisksError(1)
        assert err.error == "INSUFFICIENT_RISKS"
        assert "3" in err.message
        assert "1" in err.message
        assert err.status_code == 400
