"""
Integration tests for the CFO Mentor API REST layer.

Strategy:
- Override `get_db`           → yield a mock AsyncSession (no real DB)
- Override `get_current_user` → return fixed user payload (auth bypassed)
- Override `get_llm_service`  → return a mock LLMService
- For 401 tests, skip get_current_user override and send bad/no token.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import create_access_token, get_current_user
from app.core.database import get_db
from app.api.routers.state_machine import get_llm_service
from app.llm.parser import LLMAnalysisResult
from app.main import app
from app.models.enums import DecisionState, DecisionType, FinancialDomain, FrameworkType

BASE_URL = "http://test"
API = "/v1/financial-decision-cases"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_mock_case(**kwargs) -> MagicMock:
    """Mimics a FinancialDecisionCase ORM instance for Pydantic model_validate."""
    case = MagicMock()
    case.id = kwargs.get("id", uuid.uuid4())
    case.title = kwargs.get("title", "Reestruturação da dívida bancária")
    case.description = kwargs.get("description", "Caso sobre dívida de longo prazo com bancos credores")
    case.financial_domain = kwargs.get("financial_domain", FinancialDomain.funding)
    case.impact_score = kwargs.get("impact_score", 4)
    case.financial_exposure = kwargs.get("financial_exposure", 45_000_000.0)
    case.time_horizon = kwargs.get("time_horizon", None)
    case.external_agents_present = kwargs.get("external_agents_present", True)
    case.decision_type = kwargs.get("decision_type", DecisionType.debt_structuring)
    case.framework_selected = kwargs.get("framework_selected", FrameworkType.game_theory)
    case.scenario_required = kwargs.get("scenario_required", True)
    case.state = kwargs.get("state", DecisionState.DRAFT)
    case.created_at = kwargs.get("created_at", datetime.utcnow())
    case.updated_at = kwargs.get("updated_at", datetime.utcnow())
    case.assumptions = kwargs.get("assumptions", [])
    case.risks = kwargs.get("risks", [])
    case.metrics_impacted = kwargs.get("metrics_impacted", [])
    case.decisions = kwargs.get("decisions", [])
    return case


def make_mock_assumption(text: str, is_implicit: bool = False) -> MagicMock:
    a = MagicMock()
    a.id = uuid.uuid4()
    a.text = text
    a.is_implicit = is_implicit
    a.created_at = datetime.utcnow()
    return a


def make_mock_risk(text: str) -> MagicMock:
    r = MagicMock()
    r.id = uuid.uuid4()
    r.text = text
    r.materialized = False
    r.created_at = datetime.utcnow()
    return r


def make_mock_transition(from_state, to_state, case_id=None) -> MagicMock:
    t = MagicMock()
    t.id = uuid.uuid4()
    t.decision_case_id = case_id or uuid.uuid4()
    t.from_state = from_state
    t.to_state = to_state
    t.transitioned_at = datetime.utcnow()
    t.triggered_by = "test-user-01"
    return t


def _exec_result(scalar_one_or_none=None, scalars_all=None, scalar=None) -> MagicMock:
    """Build a mock that mimics a SQLAlchemy CursorResult."""
    r = MagicMock()
    r.scalar_one_or_none.return_value = scalar_one_or_none
    r.scalars.return_value.all.return_value = scalars_all or []
    r.scalar.return_value = scalar if scalar is not None else 0
    return r


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_token() -> str:
    return create_access_token({"sub": "test-user-01"})


@pytest.fixture
def auth_headers(valid_token) -> dict:
    return {"Authorization": f"Bearer {valid_token}"}


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.add = MagicMock()   # session.add() is synchronous in SQLAlchemy
    return session


@pytest.fixture
def mock_llm_result() -> LLMAnalysisResult:
    return LLMAnalysisResult(
        recommendation="Recomendação: reestruturar a dívida em 3 tranches anuais.",
        financial_metrics_impacted=["EBITDA", "VPL"],
        scenario_summary="Cenário base projeta redução de 15% no custo da dívida.",
        implicit_assumptions_found=["Taxa de câmbio estável no período"],
        game_theory_model=None,
        llm_unavailable=False,
    )


@pytest.fixture
def mock_llm_service(mock_llm_result) -> MagicMock:
    service = MagicMock()
    service.analyze = AsyncMock(return_value=mock_llm_result)
    return service


@pytest.fixture
def full_override(mock_session, mock_llm_service):
    """Override DB + auth + LLM — for happy-path tests."""
    async def _get_db():
        yield mock_session

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_current_user] = lambda: {"sub": "test-user-01"}
    app.dependency_overrides[get_llm_service] = lambda: mock_llm_service
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def db_override(mock_session):
    """Override DB only — auth runs normally. For 401 tests (missing/invalid token)."""
    async def _get_db():
        yield mock_session

    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# POST /v1/financial-decision-cases
# ---------------------------------------------------------------------------

CASE_PAYLOAD = {
    "title": "Reestruturação da dívida bancária",
    "description": "Caso sobre dívida de longo prazo com bancos credores nacionais",
    "financial_domain": "funding",
    "financial_exposure": 45_000_000.0,
    "decision_type": "debt_structuring",
    "external_agents_present": True,
}


class TestCreateCase:
    async def test_success(self, full_override, auth_headers):
        case_id = uuid.uuid4()
        mock_case = MagicMock(id=case_id, state=DecisionState.DRAFT)

        with patch("app.api.routers.financial_decision_cases.FinancialDecisionCase", return_value=mock_case):
            async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
                response = await client.post(API, headers=auth_headers, json=CASE_PAYLOAD)

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(case_id)
        assert data["state"] == "DRAFT"

    async def test_no_token_returns_401(self, db_override):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.post(API, json=CASE_PAYLOAD)
        assert response.status_code == 401

    async def test_invalid_token_returns_401(self, db_override):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.post(
                API,
                headers={"Authorization": "Bearer invalid.jwt.token"},
                json=CASE_PAYLOAD,
            )
        assert response.status_code == 401
        assert response.json()["error"] == "UNAUTHORIZED"

    async def test_title_too_short_returns_400(self, full_override, auth_headers):
        payload = {**CASE_PAYLOAD, "title": "Hi"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.post(API, headers=auth_headers, json=payload)
        assert response.status_code == 400
        assert response.json()["error"] == "VALIDATION_ERROR"

    async def test_missing_required_field_returns_400(self, full_override, auth_headers):
        payload = {k: v for k, v in CASE_PAYLOAD.items() if k != "financial_exposure"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.post(API, headers=auth_headers, json=payload)
        assert response.status_code == 400
        assert response.json()["error"] == "VALIDATION_ERROR"

    async def test_negative_exposure_returns_400(self, full_override, auth_headers):
        payload = {**CASE_PAYLOAD, "financial_exposure": -1.0}
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.post(API, headers=auth_headers, json=payload)
        assert response.status_code == 400
        assert response.json()["error"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# GET /v1/financial-decision-cases
# ---------------------------------------------------------------------------

class TestListCases:
    async def test_success_empty(self, full_override, mock_session, auth_headers):
        mock_session.execute.side_effect = [
            _exec_result(scalar=0),
            _exec_result(scalars_all=[]),
        ]
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.get(API, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["page"] == 1
        assert data["limit"] == 20

    async def test_success_with_items(self, full_override, mock_session, auth_headers):
        case1 = make_mock_case()
        mock_session.execute.side_effect = [
            _exec_result(scalar=1),
            _exec_result(scalars_all=[case1]),
        ]
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.get(API, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["state"] == "DRAFT"

    async def test_no_token_returns_401(self, db_override):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.get(API)
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /v1/financial-decision-cases/{case_id}
# ---------------------------------------------------------------------------

class TestGetCase:
    async def test_success(self, full_override, mock_session, auth_headers):
        case_id = uuid.uuid4()
        mock_case = make_mock_case(id=case_id, state=DecisionState.STRUCTURED)
        mock_session.execute.return_value = _exec_result(scalar_one_or_none=mock_case)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.get(f"{API}/{case_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(case_id)
        assert data["state"] == "STRUCTURED"
        assert data["assumptions"] == []
        assert data["risks"] == []

    async def test_not_found_returns_404(self, full_override, mock_session, auth_headers):
        mock_session.execute.return_value = _exec_result(scalar_one_or_none=None)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.get(f"{API}/{uuid.uuid4()}", headers=auth_headers)

        assert response.status_code == 404
        assert response.json()["error"] == "CASE_NOT_FOUND"

    async def test_no_token_returns_401(self, db_override):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.get(f"{API}/{uuid.uuid4()}")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# PUT /v1/financial-decision-cases/{case_id}/classify
# ---------------------------------------------------------------------------

class TestClassifyCase:
    async def test_success(self, full_override, mock_session, auth_headers):
        case_id = uuid.uuid4()
        mock_case = make_mock_case(id=case_id, state=DecisionState.DRAFT)
        mock_session.execute.return_value = _exec_result(scalar_one_or_none=mock_case)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(
                f"{API}/{case_id}/classify",
                headers=auth_headers,
                json={"impact_score": 4},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "CLASSIFIED"
        assert data["framework_selected"] == "game_theory"
        assert data["scenario_required"] is True

    async def test_not_found_returns_404(self, full_override, mock_session, auth_headers):
        mock_session.execute.return_value = _exec_result(scalar_one_or_none=None)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(
                f"{API}/{uuid.uuid4()}/classify",
                headers=auth_headers,
                json={"impact_score": 3},
            )

        assert response.status_code == 404
        assert response.json()["error"] == "CASE_NOT_FOUND"

    async def test_invalid_transition_returns_409(self, full_override, mock_session, auth_headers):
        # Case already CLASSIFIED — CLASSIFIED → CLASSIFIED is invalid
        mock_case = make_mock_case(state=DecisionState.CLASSIFIED)
        mock_session.execute.return_value = _exec_result(scalar_one_or_none=mock_case)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(
                f"{API}/{mock_case.id}/classify",
                headers=auth_headers,
                json={"impact_score": 4},
            )

        assert response.status_code == 409
        assert response.json()["error"] == "INVALID_STATE_TRANSITION"

    async def test_invalid_impact_score_returns_400(self, full_override, auth_headers):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(
                f"{API}/{uuid.uuid4()}/classify",
                headers=auth_headers,
                json={"impact_score": 10},  # max is 5
            )
        assert response.status_code == 400
        assert response.json()["error"] == "VALIDATION_ERROR"

    async def test_no_token_returns_401(self, db_override):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(f"{API}/{uuid.uuid4()}/classify", json={"impact_score": 3})
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# PUT /v1/financial-decision-cases/{case_id}/structure
# ---------------------------------------------------------------------------

STRUCTURE_PAYLOAD = {
    "assumptions": ["Selic estável em 10.5%", "Receita cresce +8% a.a.", "Crédito disponível no mercado"],
    "risks": ["Alta de juros acima de 2pp", "Downgrade de rating", "Concentração de vencimentos"],
}


class TestStructureCase:
    async def test_success(self, full_override, mock_session, auth_headers):
        case_id = uuid.uuid4()
        mock_case = make_mock_case(id=case_id, state=DecisionState.CLASSIFIED)
        mock_session.execute.return_value = _exec_result(scalar_one_or_none=mock_case)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(
                f"{API}/{case_id}/structure",
                headers=auth_headers,
                json=STRUCTURE_PAYLOAD,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "STRUCTURED"
        assert data["assumptions_count"] == 3
        assert data["risks_count"] == 3

    async def test_not_found_returns_404(self, full_override, mock_session, auth_headers):
        mock_session.execute.return_value = _exec_result(scalar_one_or_none=None)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(
                f"{API}/{uuid.uuid4()}/structure",
                headers=auth_headers,
                json=STRUCTURE_PAYLOAD,
            )

        assert response.status_code == 404

    async def test_invalid_transition_returns_409(self, full_override, mock_session, auth_headers):
        # DRAFT → STRUCTURED is invalid (must go through CLASSIFIED first)
        mock_case = make_mock_case(state=DecisionState.DRAFT)
        mock_session.execute.return_value = _exec_result(scalar_one_or_none=mock_case)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(
                f"{API}/{mock_case.id}/structure",
                headers=auth_headers,
                json=STRUCTURE_PAYLOAD,
            )

        assert response.status_code == 409
        assert response.json()["error"] == "INVALID_STATE_TRANSITION"

    async def test_too_few_assumptions_returns_400(self, full_override, auth_headers):
        payload = {**STRUCTURE_PAYLOAD, "assumptions": ["Apenas uma premissa"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(
                f"{API}/{uuid.uuid4()}/structure",
                headers=auth_headers,
                json=payload,
            )
        assert response.status_code == 400
        assert response.json()["error"] == "VALIDATION_ERROR"

    async def test_no_token_returns_401(self, db_override):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(f"{API}/{uuid.uuid4()}/structure", json=STRUCTURE_PAYLOAD)
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# PUT /v1/financial-decision-cases/{case_id}/analyze
# ---------------------------------------------------------------------------

class TestAnalyzeCase:
    async def test_success(self, full_override, mock_session, mock_llm_result, auth_headers):
        case_id = uuid.uuid4()
        mock_case = make_mock_case(
            id=case_id,
            state=DecisionState.STRUCTURED,
            assumptions=[make_mock_assumption("Selic estável"), make_mock_assumption("Receita +8%")],
            risks=[make_mock_risk("Alta de juros")],
        )
        mock_session.execute.return_value = _exec_result(scalar_one_or_none=mock_case)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(f"{API}/{case_id}/analyze", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "RECOMMENDED"
        assert data["recommendation"] == mock_llm_result.recommendation
        assert data["framework_selected"] == "game_theory"
        assert data["llm_unavailable"] is False
        assert "EBITDA" in data["financial_metrics_impacted"]

    async def test_llm_fallback_returns_200_with_flag(self, full_override, mock_session, mock_llm_service, auth_headers):
        fallback_result = LLMAnalysisResult(
            recommendation="Fallback: análise determinística aplicada.",
            financial_metrics_impacted=["VPL", "TIR", "Payback", "Custo do Capital"],
            llm_unavailable=True,
        )
        mock_llm_service.analyze = AsyncMock(return_value=fallback_result)

        case_id = uuid.uuid4()
        mock_case = make_mock_case(id=case_id, state=DecisionState.STRUCTURED)
        mock_session.execute.return_value = _exec_result(scalar_one_or_none=mock_case)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(f"{API}/{case_id}/analyze", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["llm_unavailable"] is True

    async def test_not_found_returns_404(self, full_override, mock_session, auth_headers):
        mock_session.execute.return_value = _exec_result(scalar_one_or_none=None)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(f"{API}/{uuid.uuid4()}/analyze", headers=auth_headers)

        assert response.status_code == 404

    async def test_invalid_transition_returns_409(self, full_override, mock_session, auth_headers):
        mock_case = make_mock_case(state=DecisionState.DRAFT)  # DRAFT → ANALYZED is invalid
        mock_session.execute.return_value = _exec_result(scalar_one_or_none=mock_case)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(f"{API}/{mock_case.id}/analyze", headers=auth_headers)

        assert response.status_code == 409

    async def test_no_token_returns_401(self, db_override):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(f"{API}/{uuid.uuid4()}/analyze")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# PUT /v1/financial-decision-cases/{case_id}/decide
# ---------------------------------------------------------------------------

DECIDE_PAYLOAD = {
    "executive_decision": "Aprovamos a reestruturação completa conforme recomendado.",
}

DECIDE_DIVERGE_PAYLOAD = {
    "executive_decision": "Optamos por apenas 60% da reestruturação proposta.",
    "divergence_justification": "Contexto geopolítico exige postura conservadora.",
    "monitoring_criteria": ["DRE trimestral", "Covenants bancários"],
}


class TestDecideCase:
    def _mock_case_with_decision(self, state=DecisionState.RECOMMENDED) -> MagicMock:
        mock_decision = MagicMock()
        mock_decision.recommendation = "Recomendação do mentor CFO."
        mock_decision.executive_decision = None
        mock_decision.divergence_flag = False
        return make_mock_case(state=state, decisions=[mock_decision])

    async def test_success_no_divergence(self, full_override, mock_session, auth_headers):
        mock_case = self._mock_case_with_decision()
        mock_session.execute.return_value = _exec_result(scalar_one_or_none=mock_case)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(
                f"{API}/{mock_case.id}/decide",
                headers=auth_headers,
                json=DECIDE_PAYLOAD,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "DECIDED"
        assert data["divergence_flag"] is False

    async def test_success_with_divergence(self, full_override, mock_session, auth_headers):
        mock_case = self._mock_case_with_decision()
        mock_session.execute.return_value = _exec_result(scalar_one_or_none=mock_case)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(
                f"{API}/{mock_case.id}/decide",
                headers=auth_headers,
                json=DECIDE_DIVERGE_PAYLOAD,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["divergence_flag"] is True

    async def test_not_found_returns_404(self, full_override, mock_session, auth_headers):
        mock_session.execute.return_value = _exec_result(scalar_one_or_none=None)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(
                f"{API}/{uuid.uuid4()}/decide",
                headers=auth_headers,
                json=DECIDE_PAYLOAD,
            )

        assert response.status_code == 404

    async def test_invalid_transition_returns_409(self, full_override, mock_session, auth_headers):
        # DRAFT → DECIDED is invalid
        mock_case = self._mock_case_with_decision(state=DecisionState.DRAFT)
        mock_session.execute.return_value = _exec_result(scalar_one_or_none=mock_case)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(
                f"{API}/{mock_case.id}/decide",
                headers=auth_headers,
                json=DECIDE_PAYLOAD,
            )

        assert response.status_code == 409

    async def test_executive_decision_too_short_returns_400(self, full_override, auth_headers):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(
                f"{API}/{uuid.uuid4()}/decide",
                headers=auth_headers,
                json={"executive_decision": "Sim."},
            )
        assert response.status_code == 400
        assert response.json()["error"] == "VALIDATION_ERROR"

    async def test_no_token_returns_401(self, db_override):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(f"{API}/{uuid.uuid4()}/decide", json=DECIDE_PAYLOAD)
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# PUT /v1/financial-decision-cases/{case_id}/review
# ---------------------------------------------------------------------------

REVIEW_PAYLOAD = {
    "outcome_summary": "Reestruturação reduziu custo da dívida em 15% conforme projetado.",
    "forecast_accuracy_score": 8,
    "risk_realization_rate": 20.0,
    "capital_allocation_efficiency_score": 90.0,
}


class TestReviewCase:
    async def test_success_from_decided_state(self, full_override, mock_session, auth_headers):
        case_id = uuid.uuid4()
        mock_case = make_mock_case(id=case_id, state=DecisionState.DECIDED)
        mock_session.execute.return_value = _exec_result(scalar_one_or_none=mock_case)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(
                f"{API}/{case_id}/review",
                headers=auth_headers,
                json=REVIEW_PAYLOAD,
            )

        assert response.status_code == 200
        assert response.json()["state"] == "CLOSED"

    async def test_success_from_under_review_state(self, full_override, mock_session, auth_headers):
        case_id = uuid.uuid4()
        mock_case = make_mock_case(id=case_id, state=DecisionState.UNDER_REVIEW)
        mock_session.execute.return_value = _exec_result(scalar_one_or_none=mock_case)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(
                f"{API}/{case_id}/review",
                headers=auth_headers,
                json=REVIEW_PAYLOAD,
            )

        assert response.status_code == 200
        assert response.json()["state"] == "CLOSED"

    async def test_not_found_returns_404(self, full_override, mock_session, auth_headers):
        mock_session.execute.return_value = _exec_result(scalar_one_or_none=None)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(
                f"{API}/{uuid.uuid4()}/review",
                headers=auth_headers,
                json=REVIEW_PAYLOAD,
            )

        assert response.status_code == 404

    async def test_invalid_transition_returns_409(self, full_override, mock_session, auth_headers):
        # DRAFT → UNDER_REVIEW (then CLOSED) is invalid — expects DECIDED or UNDER_REVIEW
        mock_case = make_mock_case(state=DecisionState.DRAFT)
        mock_session.execute.return_value = _exec_result(scalar_one_or_none=mock_case)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(
                f"{API}/{mock_case.id}/review",
                headers=auth_headers,
                json=REVIEW_PAYLOAD,
            )

        assert response.status_code == 409

    async def test_no_token_returns_401(self, db_override):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(f"{API}/{uuid.uuid4()}/review", json=REVIEW_PAYLOAD)
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /v1/financial-decision-cases/{case_id}/state-transitions
# ---------------------------------------------------------------------------

class TestAuditTrail:
    async def test_success_with_transitions(self, full_override, mock_session, auth_headers):
        case_id = uuid.uuid4()
        t1 = make_mock_transition(from_state=None, to_state=DecisionState.DRAFT, case_id=case_id)
        t2 = make_mock_transition(
            from_state=DecisionState.DRAFT, to_state=DecisionState.CLASSIFIED, case_id=case_id
        )
        mock_session.execute.side_effect = [
            _exec_result(scalar_one_or_none=case_id),   # case existence check
            _exec_result(scalars_all=[t1, t2]),          # transitions list
        ]

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.get(f"{API}/{case_id}/state-transitions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["decision_case_id"] == str(case_id)
        assert len(data["transitions"]) == 2
        assert data["transitions"][1]["to_state"] == "CLASSIFIED"

    async def test_empty_transitions(self, full_override, mock_session, auth_headers):
        case_id = uuid.uuid4()
        mock_session.execute.side_effect = [
            _exec_result(scalar_one_or_none=case_id),
            _exec_result(scalars_all=[]),
        ]

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.get(f"{API}/{case_id}/state-transitions", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["transitions"] == []

    async def test_case_not_found_returns_404(self, full_override, mock_session, auth_headers):
        mock_session.execute.return_value = _exec_result(scalar_one_or_none=None)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.get(f"{API}/{uuid.uuid4()}/state-transitions", headers=auth_headers)

        assert response.status_code == 404
        assert response.json()["error"] == "CASE_NOT_FOUND"

    async def test_no_token_returns_401(self, db_override):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.get(f"{API}/{uuid.uuid4()}/state-transitions")
        assert response.status_code == 401

    async def test_invalid_token_returns_401(self, db_override):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.get(
                f"{API}/{uuid.uuid4()}/state-transitions",
                headers={"Authorization": "Bearer bad.token"},
            )
        assert response.status_code == 401
        assert response.json()["error"] == "UNAUTHORIZED"


# ---------------------------------------------------------------------------
# PUT /v1/financial-decision-cases/{case_id}/hypothesis
# ---------------------------------------------------------------------------

HYPOTHESIS_PAYLOAD = {
    "initial_hypothesis": "Acredito que devemos reestruturar a dívida em parcelas menores para reduzir risco."
}


class TestHypothesis:
    def _mock_case_with_decision(self, state=DecisionState.RECOMMENDED) -> MagicMock:
        mock_decision = MagicMock()
        mock_decision.recommendation = "Recomendação do mentor CFO."
        mock_decision.initial_hypothesis = None
        mock_decision.executive_decision = None
        mock_decision.divergence_flag = False
        return make_mock_case(state=state, decisions=[mock_decision])

    async def test_hypothesis_success(self, full_override, mock_session, auth_headers):
        mock_case = self._mock_case_with_decision()
        mock_session.execute.return_value = _exec_result(scalar_one_or_none=mock_case)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(
                f"{API}/{mock_case.id}/hypothesis",
                headers=auth_headers,
                json=HYPOTHESIS_PAYLOAD,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "recorded"
        assert mock_case.decisions[-1].initial_hypothesis == HYPOTHESIS_PAYLOAD["initial_hypothesis"]

    async def test_hypothesis_wrong_state(self, full_override, mock_session, auth_headers):
        mock_case = self._mock_case_with_decision(state=DecisionState.STRUCTURED)
        mock_session.execute.return_value = _exec_result(scalar_one_or_none=mock_case)

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(
                f"{API}/{mock_case.id}/hypothesis",
                headers=auth_headers,
                json=HYPOTHESIS_PAYLOAD,
            )

        assert response.status_code == 409
        assert response.json()["error"] == "INVALID_STATE_TRANSITION"

    async def test_hypothesis_too_short(self, full_override, auth_headers):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.put(
                f"{API}/{uuid.uuid4()}/hypothesis",
                headers=auth_headers,
                json={"initial_hypothesis": "Curto demais"},
            )

        assert response.status_code == 400
        assert response.json()["error"] == "VALIDATION_ERROR"
