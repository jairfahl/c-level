"""
Testes unitários — LLM Layer (P-05)

Cobertura:
- PromptBuilder: geração correta de seções, instruções por framework,
  flags scenario_required / game_theory_active.
- ResponseParser: extração JSON de texto puro e markdown fence,
  validação Pydantic, erros de parse.
- build_cache_key: determinismo, independência de ordem (sorted),
  chaves distintas para inputs distintos.
- LLMCache: hit/miss, TTL padrão, falhas silenciosas (redis down).
- FallbackHandler: llm_unavailable=True, métricas por framework,
  gravação de AuditLog.
- LLMService: cache hit (sem chamada LLM), cache miss + sucesso,
  fallback em APIError, fallback em LLMParseError.
"""
from __future__ import annotations

import json
import uuid
from types import SimpleNamespace
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import fakeredis
import pytest

from app.core.audit_logger import AuditAction
from app.llm.cache import LLMCache, build_cache_key
from app.llm.fallback import (
    FallbackHandler,
    _FALLBACK_RECOMMENDATION,
    _FRAMEWORK_DEFAULT_METRICS,
)
from app.llm.parser import LLMAnalysisResult, LLMParseError, ResponseParser
from app.llm.prompt_builder import (
    SYSTEM_PROMPT,
    PromptBuilder,
    PromptContext,
    _FRAMEWORK_INSTRUCTIONS,
)
from app.llm.service import LLMService
from app.models.enums import DecisionType, FinancialDomain, FrameworkType, TimeHorizon
from app.models.financial_decision_case import AuditLog


# ─────────────────────────────────────────────────────────────────────────────
#  Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def ctx() -> PromptContext:
    return PromptContext(
        case_id=uuid.uuid4(),
        decision_type=DecisionType.debt_structuring,
        financial_domain=FinancialDomain.funding,
        financial_exposure=45_000_000.0,
        time_horizon=TimeHorizon.long,
        framework_selected=FrameworkType.game_theory,
        scenario_required=True,
        game_theory_active=True,
        assumptions=[
            "Taxa Selic se mantém em 10,5%",
            "Receita crescerá 8% no próximo exercício",
            "Linha de crédito rotativo permanece disponível",
        ],
        risks=[
            "Reversão do ciclo de afrouxamento monetário",
            "Deterioração do rating de crédito",
            "Concentração de vencimentos em janela curta",
        ],
    )


@pytest.fixture
def ctx_simple() -> PromptContext:
    """Contexto sem game_theory, sem scenario_required."""
    return PromptContext(
        case_id=uuid.uuid4(),
        decision_type=DecisionType.budget_adjustment,
        financial_domain=FinancialDomain.planning,
        financial_exposure=80_000.0,
        time_horizon=TimeHorizon.short,
        framework_selected=FrameworkType.pdca,
        scenario_required=False,
        game_theory_active=False,
        assumptions=["A1", "A2", "A3"],
        risks=["R1", "R2", "R3"],
    )


def _mock_session() -> MagicMock:
    session = MagicMock()
    session.add = MagicMock()
    return session


async def _fake_redis() -> fakeredis.FakeAsyncRedis:
    return fakeredis.FakeAsyncRedis(decode_responses=True)


_VALID_LLM_JSON_PAYLOAD = {
    "recommendation": "Reestruturar 70% da dívida via mercado de capitais.",
    "financial_metrics_impacted": ["VPL", "TIR", "DSCR"],
    "scenario_summary": "Cenário base: redução de 15% no custo da dívida.",
    "implicit_assumptions_found": ["Mercado de capitais permanece receptivo"],
    "game_theory_model": {
        "players": ["CFO", "Banco Credor"],
        "strategies": {
            "CFO": ["negociar", "aguardar"],
            "Banco Credor": ["aceitar", "recusar"],
        },
        "payoffs": {"CFO-negociar/Banco-aceitar": "ótimo"},
        "equilibrium": "Nash: CFO=negociar, Banco=aceitar",
        "strategic_risk": "Risco de recusa abrupta",
    },
}

_VALID_LLM_RAW = json.dumps(_VALID_LLM_JSON_PAYLOAD)


# ─────────────────────────────────────────────────────────────────────────────
#  PromptBuilder
# ─────────────────────────────────────────────────────────────────────────────

class TestPromptBuilder:
    def test_build_returns_two_strings(self, ctx: PromptContext):
        system, user = PromptBuilder.build(ctx)
        assert isinstance(system, str)
        assert isinstance(user, str)

    def test_system_prompt_is_exact_constant(self, ctx: PromptContext):
        system, _ = PromptBuilder.build(ctx)
        assert system == SYSTEM_PROMPT
        assert "structured financial decision-making mentor" in system
        assert "JSON contract" in system

    def test_user_prompt_contains_context_section(self, ctx: PromptContext):
        _, user = PromptBuilder.build(ctx)
        assert "## Contexto da Decisão" in user
        assert ctx.decision_type.value in user
        assert ctx.financial_domain.value in user
        assert "45,000,000.00" in user
        assert ctx.framework_selected.value in user

    def test_user_prompt_contains_time_horizon(self, ctx: PromptContext):
        _, user = PromptBuilder.build(ctx)
        assert ctx.time_horizon.value in user  # "long"

    def test_user_prompt_time_horizon_none(self, ctx: PromptContext):
        ctx.time_horizon = None
        _, user = PromptBuilder.build(ctx)
        assert "não especificado" in user

    def test_user_prompt_contains_assumptions_section(self, ctx: PromptContext):
        _, user = PromptBuilder.build(ctx)
        assert "## Premissas Declaradas" in user
        for assumption in ctx.assumptions:
            assert assumption in user

    def test_user_prompt_contains_risks_section(self, ctx: PromptContext):
        _, user = PromptBuilder.build(ctx)
        assert "## Riscos Identificados" in user
        for risk in ctx.risks:
            assert risk in user

    def test_user_prompt_no_assumptions_shows_placeholder(self, ctx: PromptContext):
        ctx.assumptions = []
        _, user = PromptBuilder.build(ctx)
        assert "Nenhuma premissa declarada" in user

    def test_user_prompt_no_risks_shows_placeholder(self, ctx: PromptContext):
        ctx.risks = []
        _, user = PromptBuilder.build(ctx)
        assert "Nenhum risco declarado" in user

    def test_user_prompt_contains_instructions_section(self, ctx: PromptContext):
        _, user = PromptBuilder.build(ctx)
        assert "## Instruções de Análise" in user

    def test_user_prompt_contains_json_contract_section(self, ctx: PromptContext):
        _, user = PromptBuilder.build(ctx)
        assert "## Contrato de Saída" in user
        assert "recommendation" in user
        assert "financial_metrics_impacted" in user

    def test_scenario_required_true_adds_scenario_instruction(self, ctx: PromptContext):
        ctx.scenario_required = True
        _, user = PromptBuilder.build(ctx)
        assert "scenario_required = true" in user

    def test_scenario_required_false_no_scenario_instruction(self, ctx_simple: PromptContext):
        ctx_simple.scenario_required = False
        _, user = PromptBuilder.build(ctx_simple)
        assert "scenario_required = true" not in user

    def test_game_theory_active_true_adds_game_theory_instruction(self, ctx: PromptContext):
        ctx.game_theory_active = True
        _, user = PromptBuilder.build(ctx)
        assert "game_theory_active = true" in user

    def test_game_theory_active_false_no_game_theory_instruction(self, ctx_simple: PromptContext):
        ctx_simple.game_theory_active = False
        _, user = PromptBuilder.build(ctx_simple)
        assert "game_theory_active = true" not in user

    def test_implicit_assumption_instruction_always_present(self, ctx_simple: PromptContext):
        _, user = PromptBuilder.build(ctx_simple)
        assert "premissas implícitas" in user.lower()

    @pytest.mark.parametrize("framework", list(FrameworkType))
    def test_all_frameworks_produce_instructions(self, framework: FrameworkType):
        ctx = PromptContext(
            case_id=uuid.uuid4(),
            decision_type=DecisionType.budget_adjustment,
            financial_domain=FinancialDomain.planning,
            financial_exposure=100_000.0,
            time_horizon=None,
            framework_selected=framework,
            scenario_required=False,
            game_theory_active=False,
            assumptions=["A1", "A2", "A3"],
            risks=["R1", "R2", "R3"],
        )
        _, user = PromptBuilder.build(ctx)
        assert "## Instruções de Análise" in user
        assert len(user) > 200  # non-trivial output

    def test_framework_instructions_covers_all_framework_types(self):
        for ft in FrameworkType:
            assert ft in _FRAMEWORK_INSTRUCTIONS, (
                f"FrameworkType.{ft.value} não tem instruções em _FRAMEWORK_INSTRUCTIONS"
            )

    def test_numbers_formatted_with_commas(self, ctx: PromptContext):
        ctx.financial_exposure = 1_234_567.89
        _, user = PromptBuilder.build(ctx)
        assert "1,234,567.89" in user


# ─────────────────────────────────────────────────────────────────────────────
#  ResponseParser
# ─────────────────────────────────────────────────────────────────────────────

class TestResponseParser:
    def test_parse_raw_json(self):
        result = ResponseParser.parse(_VALID_LLM_RAW)
        assert isinstance(result, LLMAnalysisResult)
        assert result.recommendation == _VALID_LLM_JSON_PAYLOAD["recommendation"]
        assert "VPL" in result.financial_metrics_impacted
        assert result.llm_unavailable is False

    def test_parse_json_in_markdown_fence(self):
        wrapped = f"```json\n{_VALID_LLM_RAW}\n```"
        result = ResponseParser.parse(wrapped)
        assert result.recommendation == _VALID_LLM_JSON_PAYLOAD["recommendation"]

    def test_parse_json_in_generic_fence(self):
        wrapped = f"```\n{_VALID_LLM_RAW}\n```"
        result = ResponseParser.parse(wrapped)
        assert result.recommendation == _VALID_LLM_JSON_PAYLOAD["recommendation"]

    def test_parse_json_with_surrounding_text(self):
        text = f"Here is the analysis:\n{_VALID_LLM_RAW}\nEnd of analysis."
        result = ResponseParser.parse(text)
        assert result.recommendation == _VALID_LLM_JSON_PAYLOAD["recommendation"]

    def test_game_theory_model_parsed(self):
        result = ResponseParser.parse(_VALID_LLM_RAW)
        assert result.game_theory_model is not None
        assert "CFO" in result.game_theory_model.players
        assert result.game_theory_model.equilibrium is not None

    def test_game_theory_model_null(self):
        payload = {**_VALID_LLM_JSON_PAYLOAD, "game_theory_model": None}
        result = ResponseParser.parse(json.dumps(payload))
        assert result.game_theory_model is None

    def test_optional_fields_have_defaults(self):
        minimal = json.dumps({"recommendation": "Approve immediately."})
        result = ResponseParser.parse(minimal)
        assert result.financial_metrics_impacted == []
        assert result.scenario_summary is None
        assert result.implicit_assumptions_found == []
        assert result.game_theory_model is None

    def test_no_json_raises_parse_error(self):
        with pytest.raises(LLMParseError, match="No valid JSON"):
            ResponseParser.parse("Sorry, I cannot analyze this case.")

    def test_invalid_json_raises_parse_error(self):
        with pytest.raises(LLMParseError):
            ResponseParser.parse("{ invalid json }")

    def test_missing_required_field_raises_parse_error(self):
        """recommendation é obrigatório — ausência deve lançar LLMParseError."""
        no_recommendation = json.dumps({
            "financial_metrics_impacted": ["EBITDA"],
        })
        with pytest.raises(LLMParseError, match="schema validation"):
            ResponseParser.parse(no_recommendation)

    def test_llm_analysis_result_llm_unavailable_default_false(self):
        result = LLMAnalysisResult(recommendation="OK")
        assert result.llm_unavailable is False


# ─────────────────────────────────────────────────────────────────────────────
#  build_cache_key
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildCacheKey:
    def test_key_has_correct_prefix(self, ctx: PromptContext):
        key = build_cache_key(ctx)
        assert key.startswith("llm:analysis:")

    def test_key_deterministic_same_inputs(self, ctx: PromptContext):
        key1 = build_cache_key(ctx)
        key2 = build_cache_key(ctx)
        assert key1 == key2

    def test_key_order_independent_assumptions(self, ctx: PromptContext):
        ctx2 = PromptContext(
            **{**ctx.__dict__, "assumptions": list(reversed(ctx.assumptions))}
        )
        assert build_cache_key(ctx) == build_cache_key(ctx2)

    def test_key_order_independent_risks(self, ctx: PromptContext):
        ctx2 = PromptContext(
            **{**ctx.__dict__, "risks": list(reversed(ctx.risks))}
        )
        assert build_cache_key(ctx) == build_cache_key(ctx2)

    def test_different_framework_different_key(self, ctx: PromptContext):
        ctx2 = PromptContext(**{**ctx.__dict__, "framework_selected": FrameworkType.pdca})
        assert build_cache_key(ctx) != build_cache_key(ctx2)

    def test_different_decision_type_different_key(self, ctx: PromptContext):
        ctx2 = PromptContext(
            **{**ctx.__dict__, "decision_type": DecisionType.budget_adjustment}
        )
        assert build_cache_key(ctx) != build_cache_key(ctx2)

    def test_different_assumptions_different_key(self, ctx: PromptContext):
        ctx2 = PromptContext(
            **{**ctx.__dict__, "assumptions": ["completamente diferente"]}
        )
        assert build_cache_key(ctx) != build_cache_key(ctx2)

    def test_key_is_sha256_hex(self, ctx: PromptContext):
        key = build_cache_key(ctx)
        hex_part = key.replace("llm:analysis:", "")
        assert len(hex_part) == 64
        assert all(c in "0123456789abcdef" for c in hex_part)


# ─────────────────────────────────────────────────────────────────────────────
#  LLMCache
# ─────────────────────────────────────────────────────────────────────────────

class TestLLMCache:
    @pytest.fixture
    async def cache(self) -> LLMCache:
        redis = fakeredis.FakeAsyncRedis(decode_responses=True)
        return LLMCache(redis_client=redis)

    @pytest.mark.asyncio
    async def test_miss_returns_none(self, cache: LLMCache):
        result = await cache.get("nonexistent-key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_then_get_returns_result(self, cache: LLMCache):
        stored = LLMAnalysisResult(
            recommendation="Buy low, sell high.",
            financial_metrics_impacted=["EBITDA"],
        )
        await cache.set("test-key", stored, ttl=60)
        retrieved = await cache.get("test-key")
        assert retrieved is not None
        assert retrieved.recommendation == stored.recommendation
        assert retrieved.financial_metrics_impacted == ["EBITDA"]

    @pytest.mark.asyncio
    async def test_set_then_get_preserves_game_theory_model(self, cache: LLMCache):
        stored = LLMAnalysisResult(**LLMAnalysisResult.model_validate(
            _VALID_LLM_JSON_PAYLOAD
        ).model_dump())
        await cache.set("test-gt", stored, ttl=60)
        retrieved = await cache.get("test-gt")
        assert retrieved is not None
        assert retrieved.game_theory_model is not None
        assert retrieved.game_theory_model.players == stored.game_theory_model.players

    @pytest.mark.asyncio
    async def test_get_with_broken_redis_returns_none(self):
        """Redis que lança exceção → cache miss silencioso."""
        broken_redis = AsyncMock()
        broken_redis.get = AsyncMock(side_effect=ConnectionError("Redis down"))
        cache = LLMCache(redis_client=broken_redis)
        result = await cache.get("any-key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_with_broken_redis_does_not_raise(self):
        """Falha de escrita no Redis não deve propagar exceção."""
        broken_redis = AsyncMock()
        broken_redis.setex = AsyncMock(side_effect=ConnectionError("Redis down"))
        cache = LLMCache(redis_client=broken_redis)
        stored = LLMAnalysisResult(recommendation="OK")
        # Must not raise
        await cache.set("any-key", stored)

    @pytest.mark.asyncio
    async def test_custom_ttl_accepted(self, cache: LLMCache):
        stored = LLMAnalysisResult(recommendation="Short-lived result.")
        await cache.set("ttl-key", stored, ttl=5)
        retrieved = await cache.get("ttl-key")
        assert retrieved is not None

    @pytest.mark.asyncio
    async def test_corrupted_cache_value_returns_none(self, cache: LLMCache):
        """Dado corrompido no Redis deve resultar em cache miss, não exceção."""
        redis = fakeredis.FakeAsyncRedis(decode_responses=True)
        await redis.set("corrupt-key", "not-valid-json{{{")
        cache_with_corrupt = LLMCache(redis_client=redis)
        result = await cache_with_corrupt.get("corrupt-key")
        assert result is None


# ─────────────────────────────────────────────────────────────────────────────
#  FallbackHandler
# ─────────────────────────────────────────────────────────────────────────────

class TestFallbackHandler:
    @pytest.mark.asyncio
    async def test_returns_llm_unavailable_true(self, ctx: PromptContext):
        session = _mock_session()
        result = await FallbackHandler.handle(ctx, session)
        assert result.llm_unavailable is True

    @pytest.mark.asyncio
    async def test_recommendation_is_fallback_constant(self, ctx: PromptContext):
        session = _mock_session()
        result = await FallbackHandler.handle(ctx, session)
        assert result.recommendation == _FALLBACK_RECOMMENDATION

    @pytest.mark.asyncio
    async def test_metrics_populated_by_framework(self, ctx: PromptContext):
        session = _mock_session()
        result = await FallbackHandler.handle(ctx, session)
        expected = _FRAMEWORK_DEFAULT_METRICS[ctx.framework_selected]
        assert result.financial_metrics_impacted == expected

    @pytest.mark.asyncio
    @pytest.mark.parametrize("framework", list(FrameworkType))
    async def test_all_frameworks_have_default_metrics(self, framework: FrameworkType):
        ctx = PromptContext(
            case_id=uuid.uuid4(),
            decision_type=DecisionType.budget_adjustment,
            financial_domain=FinancialDomain.planning,
            financial_exposure=50_000.0,
            time_horizon=None,
            framework_selected=framework,
            scenario_required=False,
            game_theory_active=False,
        )
        session = _mock_session()
        result = await FallbackHandler.handle(ctx, session)
        assert isinstance(result.financial_metrics_impacted, list)
        assert len(result.financial_metrics_impacted) > 0, (
            f"Framework {framework.value} deve ter métricas de fallback"
        )

    @pytest.mark.asyncio
    async def test_scenario_summary_is_none(self, ctx: PromptContext):
        session = _mock_session()
        result = await FallbackHandler.handle(ctx, session)
        assert result.scenario_summary is None

    @pytest.mark.asyncio
    async def test_game_theory_model_is_none(self, ctx: PromptContext):
        session = _mock_session()
        result = await FallbackHandler.handle(ctx, session)
        assert result.game_theory_model is None

    @pytest.mark.asyncio
    async def test_implicit_assumptions_empty(self, ctx: PromptContext):
        session = _mock_session()
        result = await FallbackHandler.handle(ctx, session)
        assert result.implicit_assumptions_found == []

    @pytest.mark.asyncio
    async def test_audit_log_written_with_llm_fallback_action(self, ctx: PromptContext):
        session = _mock_session()
        await FallbackHandler.handle(ctx, session, error=RuntimeError("timeout"))
        session.add.assert_called_once()
        added = session.add.call_args.args[0]
        assert isinstance(added, AuditLog)
        assert added.action == AuditAction.LLM_FALLBACK
        assert added.decision_case_id == ctx.case_id

    @pytest.mark.asyncio
    async def test_audit_log_payload_contains_error_info(self, ctx: PromptContext):
        session = _mock_session()
        error = ValueError("Connection refused")
        await FallbackHandler.handle(ctx, session, error=error)
        added = session.add.call_args.args[0]
        assert "Connection refused" in added.payload["error"]
        assert added.payload["framework"] == ctx.framework_selected.value

    @pytest.mark.asyncio
    async def test_audit_log_payload_error_none_when_no_error(self, ctx: PromptContext):
        session = _mock_session()
        await FallbackHandler.handle(ctx, session, error=None)
        added = session.add.call_args.args[0]
        assert added.payload["error"] == "unknown"

    def test_framework_default_metrics_covers_all_framework_types(self):
        for ft in FrameworkType:
            assert ft in _FRAMEWORK_DEFAULT_METRICS, (
                f"FrameworkType.{ft.value} não tem métricas de fallback em _FRAMEWORK_DEFAULT_METRICS"
            )


# ─────────────────────────────────────────────────────────────────────────────
#  LLMService
# ─────────────────────────────────────────────────────────────────────────────

class TestLLMService:
    """Testa o fluxo completo: cache hit/miss, sucesso, fallback em erro."""

    @pytest.fixture
    async def cache(self) -> LLMCache:
        redis = fakeredis.FakeAsyncRedis(decode_responses=True)
        return LLMCache(redis_client=redis)

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        client = MagicMock()
        client.complete = AsyncMock(return_value=_VALID_LLM_RAW)
        return client

    @pytest.mark.asyncio
    async def test_cache_miss_calls_llm_and_returns_result(
        self, ctx: PromptContext, mock_client: MagicMock, cache: LLMCache
    ):
        session = _mock_session()
        service = LLMService(client=mock_client, cache=cache)

        result = await service.analyze(ctx, session)

        mock_client.complete.assert_awaited_once()
        assert result.recommendation == _VALID_LLM_JSON_PAYLOAD["recommendation"]
        assert result.llm_unavailable is False

    @pytest.mark.asyncio
    async def test_cache_hit_skips_llm_call(
        self, ctx: PromptContext, mock_client: MagicMock, cache: LLMCache
    ):
        session = _mock_session()
        # Pre-populate cache
        key = build_cache_key(ctx)
        stored = LLMAnalysisResult(recommendation="Cached result.", financial_metrics_impacted=[])
        await cache.set(key, stored)

        service = LLMService(client=mock_client, cache=cache)
        result = await service.analyze(ctx, session)

        mock_client.complete.assert_not_awaited()
        assert result.recommendation == "Cached result."

    @pytest.mark.asyncio
    async def test_result_is_cached_after_successful_llm_call(
        self, ctx: PromptContext, mock_client: MagicMock, cache: LLMCache
    ):
        session = _mock_session()
        service = LLMService(client=mock_client, cache=cache)

        await service.analyze(ctx, session)

        # Second call — LLM should NOT be called again
        mock_client.complete.reset_mock()
        result2 = await service.analyze(ctx, session)

        mock_client.complete.assert_not_awaited()
        assert result2.llm_unavailable is False

    @pytest.mark.asyncio
    async def test_llm_api_error_triggers_fallback(
        self, ctx: PromptContext, cache: LLMCache
    ):
        session = _mock_session()
        failing_client = MagicMock()
        failing_client.complete = AsyncMock(side_effect=ConnectionError("API unreachable"))

        service = LLMService(client=failing_client, cache=cache)
        result = await service.analyze(ctx, session)

        assert result.llm_unavailable is True
        assert result.recommendation == _FALLBACK_RECOMMENDATION

    @pytest.mark.asyncio
    async def test_parse_error_triggers_fallback(
        self, ctx: PromptContext, cache: LLMCache
    ):
        session = _mock_session()
        bad_client = MagicMock()
        bad_client.complete = AsyncMock(return_value="not valid json at all!")

        service = LLMService(client=bad_client, cache=cache)
        result = await service.analyze(ctx, session)

        assert result.llm_unavailable is True

    @pytest.mark.asyncio
    async def test_llm_called_audit_log_written_on_success(
        self, ctx: PromptContext, mock_client: MagicMock, cache: LLMCache
    ):
        session = _mock_session()
        service = LLMService(client=mock_client, cache=cache)
        await service.analyze(ctx, session)

        added_objects = [c.args[0] for c in session.add.call_args_list]
        audit_logs = [o for o in added_objects if isinstance(o, AuditLog)]
        assert any(log.action == AuditAction.LLM_CALLED for log in audit_logs)

    @pytest.mark.asyncio
    async def test_fallback_audit_log_written_on_error(
        self, ctx: PromptContext, cache: LLMCache
    ):
        session = _mock_session()
        failing_client = MagicMock()
        failing_client.complete = AsyncMock(side_effect=TimeoutError("30s exceeded"))

        service = LLMService(client=failing_client, cache=cache)
        await service.analyze(ctx, session)

        added_objects = [c.args[0] for c in session.add.call_args_list]
        audit_logs = [o for o in added_objects if isinstance(o, AuditLog)]
        assert any(log.action == AuditAction.LLM_FALLBACK for log in audit_logs)

    @pytest.mark.asyncio
    async def test_triggered_by_included_in_llm_called_payload(
        self, ctx: PromptContext, mock_client: MagicMock, cache: LLMCache
    ):
        session = _mock_session()
        service = LLMService(client=mock_client, cache=cache)
        await service.analyze(ctx, session, triggered_by="user:test-id")

        added_objects = [c.args[0] for c in session.add.call_args_list]
        llm_log = next(
            (o for o in added_objects if isinstance(o, AuditLog) and o.action == AuditAction.LLM_CALLED),
            None,
        )
        assert llm_log is not None
        assert llm_log.payload["triggered_by"] == "user:test-id"

    @pytest.mark.asyncio
    async def test_game_theory_model_propagated(
        self, ctx: PromptContext, mock_client: MagicMock, cache: LLMCache
    ):
        session = _mock_session()
        service = LLMService(client=mock_client, cache=cache)
        result = await service.analyze(ctx, session)

        assert result.game_theory_model is not None
        assert result.game_theory_model.strategic_risk is not None

    @pytest.mark.asyncio
    async def test_fallback_metrics_match_framework(
        self, ctx: PromptContext, cache: LLMCache
    ):
        """Fallback para game_theory deve retornar as métricas de game_theory."""
        session = _mock_session()
        failing_client = MagicMock()
        failing_client.complete = AsyncMock(side_effect=Exception("down"))

        service = LLMService(client=failing_client, cache=cache)
        result = await service.analyze(ctx, session)

        expected = _FRAMEWORK_DEFAULT_METRICS[FrameworkType.game_theory]
        assert result.financial_metrics_impacted == expected
