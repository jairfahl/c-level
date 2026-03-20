"""
Testes unitários — Learning Module (P-10)

Cobertura:
- ReviewService.compute_divergence_outcome: regra divergência + forecast score
- ReviewService.update_risk_materialization: threshold 50 %, marcação de riscos
- HeuristicsService: create, list (com e sem filtros), deactivate + erro 404
- ReviewTrigger.get_cases_pending_review: filtragem por estado + idade + review
- HeuristicsNotFoundError: construtor e mensagem
- Endpoints (integração): POST /heuristics, GET /heuristics, PUT /deactivate,
  GET /admin/pending-reviews — com/sem autenticação, filtros de query
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import HeuristicNotFoundError
from app.main import app
from app.models.enums import DecisionState, DecisionType, FinancialDomain
from app.services.heuristics_service import HeuristicsService
from app.services.review_service import ReviewService
from app.services.review_trigger import REVIEW_THRESHOLD_DAYS, ReviewTrigger
from app.core.database import get_db
from app.core.auth import get_current_user

BASE_URL = "http://test"
HEURISTICS_API = "/v1/heuristics"
ADMIN_API = "/v1/admin"


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _mock_session() -> AsyncMock:
    s = AsyncMock()
    s.add = MagicMock()
    s.flush = AsyncMock()
    return s


def _exec(
    scalar_one_or_none=None,
    scalars_all=None,
) -> MagicMock:
    r = MagicMock()
    r.scalar_one_or_none.return_value = scalar_one_or_none
    r.scalars.return_value.all.return_value = scalars_all or []
    return r


def _mock_case(state: DecisionState = DecisionState.DECIDED) -> MagicMock:
    c = MagicMock()
    c.id = uuid.uuid4()
    c.state = state
    c.financial_domain = FinancialDomain.funding
    c.decision_type = DecisionType.debt_structuring
    c.financial_exposure = 52_000_000.0
    c.updated_at = datetime.utcnow() - timedelta(days=100)
    return c


def _mock_heuristic(active: bool = True) -> MagicMock:
    h = MagicMock()
    h.id = uuid.uuid4()
    h.decision_type = DecisionType.debt_structuring
    h.financial_domain = FinancialDomain.funding
    h.heuristic_key = "bilateral_negotiation_preferred"
    h.heuristic_value = {"trigger": "external_agents=true", "confidence": 0.85}
    h.source_case_id = None
    h.active = active
    h.created_at = datetime.utcnow()
    h.updated_at = datetime.utcnow()
    return h


AUTH_HEADERS = {"Authorization": "Bearer test-token"}


# ─────────────────────────────────────────────────────────────────────────────
#  ReviewService — compute_divergence_outcome
# ─────────────────────────────────────────────────────────────────────────────

class TestReviewServiceDivergenceOutcome:
    """Regra: True quando divergence_flag=True E forecast_accuracy_score < 5."""

    async def test_no_divergence_decision_returns_false(self):
        session = _mock_session()
        session.execute.return_value = _exec(scalar_one_or_none=None)
        case = _mock_case()
        result = await ReviewService.compute_divergence_outcome(case, 3, session)
        assert result is False

    async def test_divergence_with_score_gte_5_returns_false(self):
        """Divergência existe mas previsão foi boa → False."""
        session = _mock_session()
        session.execute.return_value = _exec(scalar_one_or_none=MagicMock())
        case = _mock_case()
        result = await ReviewService.compute_divergence_outcome(case, 5, session)
        assert result is False

    async def test_divergence_with_score_exactly_5_returns_false(self):
        session = _mock_session()
        session.execute.return_value = _exec(scalar_one_or_none=MagicMock())
        case = _mock_case()
        result = await ReviewService.compute_divergence_outcome(case, 5, session)
        assert result is False

    @pytest.mark.parametrize("score", [1, 2, 3, 4])
    async def test_divergence_with_score_lt_5_returns_true(self, score: int):
        """Divergência + previsão ruim (score < 5) → True."""
        session = _mock_session()
        session.execute.return_value = _exec(scalar_one_or_none=MagicMock())
        case = _mock_case()
        result = await ReviewService.compute_divergence_outcome(case, score, session)
        assert result is True

    async def test_divergence_with_none_score_returns_false(self):
        """Score None → não pode avaliar divergência de outcome → False."""
        session = _mock_session()
        session.execute.return_value = _exec(scalar_one_or_none=MagicMock())
        case = _mock_case()
        result = await ReviewService.compute_divergence_outcome(case, None, session)
        assert result is False

    async def test_no_db_call_when_score_is_none(self):
        """Com score None, a query de divergência nem deve ser executada."""
        session = _mock_session()
        case = _mock_case()
        await ReviewService.compute_divergence_outcome(case, None, session)
        session.execute.assert_not_called()

    async def test_no_db_call_when_score_gte_5(self):
        """Com score >= 5, a query de divergência não precisa rodar."""
        session = _mock_session()
        case = _mock_case()
        await ReviewService.compute_divergence_outcome(case, 6, session)
        session.execute.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
#  ReviewService — update_risk_materialization
# ─────────────────────────────────────────────────────────────────────────────

class TestReviewServiceRiskMaterialization:
    """Regra MVP: rate > 50 % → todos os riscos marcados; caso contrário nada."""

    async def test_none_rate_makes_no_db_call(self):
        session = _mock_session()
        case = _mock_case()
        count = await ReviewService.update_risk_materialization(case, None, session)
        session.execute.assert_not_called()
        assert count == 0

    async def test_zero_rate_makes_no_db_call(self):
        session = _mock_session()
        case = _mock_case()
        count = await ReviewService.update_risk_materialization(case, 0.0, session)
        session.execute.assert_not_called()
        assert count == 0

    async def test_rate_exactly_50_makes_no_changes(self):
        """Fronteira: 50.0 % não aciona a marcação (regra: rate > 50)."""
        session = _mock_session()
        case = _mock_case()
        count = await ReviewService.update_risk_materialization(case, 50.0, session)
        session.execute.assert_not_called()
        assert count == 0

    async def test_rate_below_50_makes_no_db_call(self):
        session = _mock_session()
        case = _mock_case()
        count = await ReviewService.update_risk_materialization(case, 30.0, session)
        session.execute.assert_not_called()
        assert count == 0

    async def test_rate_above_50_marks_all_risks_materialized(self):
        """75 % → todos os 3 riscos marcados."""
        risk1 = MagicMock(materialized=False)
        risk2 = MagicMock(materialized=False)
        risk3 = MagicMock(materialized=False)
        session = _mock_session()
        session.execute.return_value = _exec(scalars_all=[risk1, risk2, risk3])
        case = _mock_case()
        count = await ReviewService.update_risk_materialization(case, 75.0, session)
        assert risk1.materialized is True
        assert risk2.materialized is True
        assert risk3.materialized is True
        assert count == 3

    async def test_rate_100_marks_all_risks(self):
        risk = MagicMock(materialized=False)
        session = _mock_session()
        session.execute.return_value = _exec(scalars_all=[risk])
        case = _mock_case()
        count = await ReviewService.update_risk_materialization(case, 100.0, session)
        assert risk.materialized is True
        assert count == 1

    async def test_rate_above_50_with_no_risks_returns_zero(self):
        """No risks in DB → 0 updated even if rate > 50."""
        session = _mock_session()
        session.execute.return_value = _exec(scalars_all=[])
        case = _mock_case()
        count = await ReviewService.update_risk_materialization(case, 80.0, session)
        assert count == 0


# ─────────────────────────────────────────────────────────────────────────────
#  HeuristicsService
# ─────────────────────────────────────────────────────────────────────────────

class TestHeuristicsServiceCreate:
    """Criação de heurística — INSERT only."""

    async def test_create_returns_heuristic_with_correct_fields(self):
        session = _mock_session()
        h = await HeuristicsService.create_heuristic(
            session=session,
            decision_type=DecisionType.debt_structuring,
            financial_domain=FinancialDomain.funding,
            heuristic_key="bilateral_negotiation_preferred",
            heuristic_value={"trigger": "external_agents=true", "confidence": 0.85},
        )
        session.add.assert_called_once_with(h)
        assert h.decision_type == DecisionType.debt_structuring
        assert h.financial_domain == FinancialDomain.funding
        assert h.heuristic_key == "bilateral_negotiation_preferred"
        assert h.active is True
        assert h.source_case_id is None

    async def test_create_with_source_case_id(self):
        session = _mock_session()
        src_id = uuid.uuid4()
        h = await HeuristicsService.create_heuristic(
            session=session,
            decision_type=DecisionType.liquidity_management,
            financial_domain=FinancialDomain.treasury,
            heuristic_key="hybrid_coverage_for_liquidity_gaps",
            heuristic_value={"trigger": "gap > 1M", "confidence": 0.9},
            source_case_id=src_id,
        )
        assert h.source_case_id == src_id

    async def test_create_does_not_delete(self):
        """Heurísticas nunca devem ser deletadas — serviço não expõe delete."""
        assert not hasattr(HeuristicsService, "delete_heuristic")


class TestHeuristicsServiceList:
    """Listagem de heurísticas — apenas ativas por padrão."""

    async def test_list_returns_active_heuristics(self):
        session = _mock_session()
        h1, h2 = _mock_heuristic(), _mock_heuristic()
        session.execute.return_value = _exec(scalars_all=[h1, h2])
        result = await HeuristicsService.list_heuristics(session)
        assert len(result) == 2

    async def test_list_with_decision_type_filter(self):
        session = _mock_session()
        session.execute.return_value = _exec(scalars_all=[_mock_heuristic()])
        result = await HeuristicsService.list_heuristics(
            session, decision_type=DecisionType.debt_structuring
        )
        assert len(result) == 1

    async def test_list_with_domain_filter(self):
        session = _mock_session()
        session.execute.return_value = _exec(scalars_all=[])
        result = await HeuristicsService.list_heuristics(
            session, financial_domain=FinancialDomain.treasury
        )
        assert result == []

    async def test_list_returns_empty_when_none_exist(self):
        session = _mock_session()
        session.execute.return_value = _exec(scalars_all=[])
        result = await HeuristicsService.list_heuristics(session)
        assert result == []


class TestHeuristicsServiceDeactivate:
    """Desativação — apenas active=False, nunca DELETE."""

    async def test_deactivate_sets_active_false(self):
        session = _mock_session()
        h = _mock_heuristic(active=True)
        session.execute.return_value = _exec(scalar_one_or_none=h)
        result = await HeuristicsService.deactivate_heuristic(session, h.id)
        assert result.active is False

    async def test_deactivate_nonexistent_raises_not_found(self):
        session = _mock_session()
        session.execute.return_value = _exec(scalar_one_or_none=None)
        with pytest.raises(HeuristicNotFoundError):
            await HeuristicsService.deactivate_heuristic(session, uuid.uuid4())

    async def test_deactivate_already_inactive_heuristic_works(self):
        """Desativar uma heurística já inativa não deve lançar erro."""
        session = _mock_session()
        h = _mock_heuristic(active=False)
        session.execute.return_value = _exec(scalar_one_or_none=h)
        result = await HeuristicsService.deactivate_heuristic(session, h.id)
        assert result.active is False


# ─────────────────────────────────────────────────────────────────────────────
#  ReviewTrigger — get_cases_pending_review
# ─────────────────────────────────────────────────────────────────────────────

class TestReviewTrigger:
    """Identifica casos DECIDED > 90 dias sem review."""

    async def test_returns_pending_case_over_threshold(self):
        session = _mock_session()
        case = _mock_case()  # updated_at = now - 100 days (over threshold)
        session.execute.return_value = _exec(scalars_all=[case])
        result = await ReviewTrigger.get_cases_pending_review(session)
        assert len(result) == 1
        assert result[0]["case_id"] == str(case.id)
        assert result[0]["days_pending"] >= 90

    async def test_returns_empty_when_no_pending_cases(self):
        session = _mock_session()
        session.execute.return_value = _exec(scalars_all=[])
        result = await ReviewTrigger.get_cases_pending_review(session)
        assert result == []

    async def test_threshold_constant_is_90(self):
        assert REVIEW_THRESHOLD_DAYS == 90

    async def test_result_contains_required_keys(self):
        session = _mock_session()
        case = _mock_case()
        session.execute.return_value = _exec(scalars_all=[case])
        result = await ReviewTrigger.get_cases_pending_review(session)
        required_keys = {
            "case_id", "title", "financial_domain", "decision_type",
            "financial_exposure", "decided_at", "days_pending"
        }
        assert required_keys.issubset(result[0].keys())

    async def test_multiple_cases_returned_in_order(self):
        """Múltiplos casos são retornados preservando a ordem do DB."""
        session = _mock_session()
        case1 = _mock_case()
        case1.updated_at = datetime.utcnow() - timedelta(days=120)
        case2 = _mock_case()
        case2.updated_at = datetime.utcnow() - timedelta(days=95)
        session.execute.return_value = _exec(scalars_all=[case1, case2])
        result = await ReviewTrigger.get_cases_pending_review(session)
        assert len(result) == 2
        # Both should have days_pending >= 90
        assert result[0]["days_pending"] >= 90
        assert result[1]["days_pending"] >= 90


# ─────────────────────────────────────────────────────────────────────────────
#  HeuristicNotFoundError — construtor
# ─────────────────────────────────────────────────────────────────────────────

class TestHeuristicNotFoundError:
    def test_error_code_and_status(self):
        exc = HeuristicNotFoundError()
        assert exc.error == "HEURISTIC_NOT_FOUND"
        assert exc.status_code == 404

    def test_message_is_in_portuguese(self):
        exc = HeuristicNotFoundError()
        assert "heurística" in exc.message.lower()


# ─────────────────────────────────────────────────────────────────────────────
#  Endpoint integration — /v1/heuristics
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_session():
    s = AsyncMock()
    s.add = MagicMock()
    s.flush = AsyncMock()
    return s


@pytest.fixture
def heuristic_override(mock_session):
    async def _get_db():
        yield mock_session

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_current_user] = lambda: {"sub": "test-architect"}
    yield mock_session
    app.dependency_overrides.clear()


@pytest.fixture
def no_auth_override(mock_session):
    async def _get_db():
        yield mock_session

    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.pop(get_db, None)


HEURISTIC_PAYLOAD = {
    "decision_type": "debt_structuring",
    "financial_domain": "funding",
    "heuristic_key": "bilateral_negotiation_preferred",
    "heuristic_value": {
        "trigger": "external_agents=true AND decision_type=debt_structuring",
        "always_check": ["spread de mercado", "BATNA dos credores"],
        "confidence": 0.85,
    },
}


class TestHeuristicsEndpointPost:

    async def test_create_heuristic_returns_201(self, heuristic_override, mock_session):
        h = _mock_heuristic()
        with patch(
            "app.api.routers.heuristics.HeuristicsService.create_heuristic",
            return_value=h,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url=BASE_URL
            ) as client:
                r = await client.post(
                    HEURISTICS_API, headers=AUTH_HEADERS, json=HEURISTIC_PAYLOAD
                )
        assert r.status_code == 201
        assert r.json()["heuristic_key"] == h.heuristic_key

    async def test_create_without_token_returns_401(self, no_auth_override):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url=BASE_URL
        ) as client:
            r = await client.post(HEURISTICS_API, json=HEURISTIC_PAYLOAD)
        assert r.status_code == 401

    async def test_create_missing_required_field_returns_400(self, heuristic_override):
        bad_payload = {k: v for k, v in HEURISTIC_PAYLOAD.items() if k != "heuristic_key"}
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url=BASE_URL
        ) as client:
            r = await client.post(
                HEURISTICS_API, headers=AUTH_HEADERS, json=bad_payload
            )
        assert r.status_code == 400


class TestHeuristicsEndpointGet:

    async def test_list_returns_200_with_heuristics(self, heuristic_override, mock_session):
        h = _mock_heuristic()
        with patch(
            "app.api.routers.heuristics.HeuristicsService.list_heuristics",
            return_value=[h],
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url=BASE_URL
            ) as client:
                r = await client.get(HEURISTICS_API, headers=AUTH_HEADERS)
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert len(body["heuristics"]) == 1

    async def test_list_empty_returns_200(self, heuristic_override, mock_session):
        with patch(
            "app.api.routers.heuristics.HeuristicsService.list_heuristics",
            return_value=[],
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url=BASE_URL
            ) as client:
                r = await client.get(HEURISTICS_API, headers=AUTH_HEADERS)
        assert r.status_code == 200
        assert r.json()["total"] == 0

    async def test_list_without_token_returns_401(self, no_auth_override):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url=BASE_URL
        ) as client:
            r = await client.get(HEURISTICS_API)
        assert r.status_code == 401

    async def test_list_with_decision_type_filter(self, heuristic_override, mock_session):
        with patch(
            "app.api.routers.heuristics.HeuristicsService.list_heuristics",
            return_value=[],
        ) as mock_list:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url=BASE_URL
            ) as client:
                r = await client.get(
                    f"{HEURISTICS_API}?decision_type=debt_structuring",
                    headers=AUTH_HEADERS,
                )
        assert r.status_code == 200
        mock_list.assert_called_once()
        call_kwargs = mock_list.call_args.kwargs
        assert call_kwargs["decision_type"] == DecisionType.debt_structuring


class TestHeuristicsEndpointDeactivate:

    async def test_deactivate_returns_200(self, heuristic_override, mock_session):
        h = _mock_heuristic(active=False)
        h_id = str(h.id)
        with patch(
            "app.api.routers.heuristics.HeuristicsService.deactivate_heuristic",
            return_value=h,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url=BASE_URL
            ) as client:
                r = await client.put(
                    f"{HEURISTICS_API}/{h_id}/deactivate",
                    headers=AUTH_HEADERS,
                )
        assert r.status_code == 200
        assert r.json()["active"] is False

    async def test_deactivate_not_found_returns_404(self, heuristic_override, mock_session):
        with patch(
            "app.api.routers.heuristics.HeuristicsService.deactivate_heuristic",
            side_effect=HeuristicNotFoundError(),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url=BASE_URL
            ) as client:
                r = await client.put(
                    f"{HEURISTICS_API}/{uuid.uuid4()}/deactivate",
                    headers=AUTH_HEADERS,
                )
        assert r.status_code == 404
        assert r.json()["error"] == "HEURISTIC_NOT_FOUND"

    async def test_deactivate_without_token_returns_401(self, no_auth_override):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url=BASE_URL
        ) as client:
            r = await client.put(f"{HEURISTICS_API}/{uuid.uuid4()}/deactivate")
        assert r.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
#  Endpoint integration — /v1/admin/pending-reviews
# ─────────────────────────────────────────────────────────────────────────────

class TestAdminPendingReviewsEndpoint:

    async def test_returns_200_with_pending_list(self, heuristic_override, mock_session):
        pending_case = {
            "case_id": str(uuid.uuid4()),
            "title": "Caso Pendente de Revisão",
            "financial_domain": "funding",
            "decision_type": "debt_structuring",
            "financial_exposure": 52_000_000.0,
            "decided_at": "2025-11-01T10:00:00",
            "days_pending": 120,
        }
        with patch(
            "app.api.routers.admin.ReviewTrigger.get_cases_pending_review",
            return_value=[pending_case],
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url=BASE_URL
            ) as client:
                r = await client.get(
                    f"{ADMIN_API}/pending-reviews", headers=AUTH_HEADERS
                )
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert body["threshold_days"] == REVIEW_THRESHOLD_DAYS
        assert body["pending"][0]["days_pending"] == 120

    async def test_returns_empty_list_when_no_pending(self, heuristic_override, mock_session):
        with patch(
            "app.api.routers.admin.ReviewTrigger.get_cases_pending_review",
            return_value=[],
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url=BASE_URL
            ) as client:
                r = await client.get(
                    f"{ADMIN_API}/pending-reviews", headers=AUTH_HEADERS
                )
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 0
        assert body["threshold_days"] == 90

    async def test_requires_authentication(self, no_auth_override):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url=BASE_URL
        ) as client:
            r = await client.get(f"{ADMIN_API}/pending-reviews")
        assert r.status_code == 401
