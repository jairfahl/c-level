"""
LLM Service — Orquestrador da Análise LLM

Fluxo principal de analyze():
  1. Verificar cache Redis  →  cache hit → retornar imediatamente
  2. Construir prompts via PromptBuilder
  3. Gravar LLM_CALLED em audit_logs
  4. Chamar LLMClient (Anthropic API)
  5. Fazer parse/validação via ResponseParser
  6. Armazenar resultado no cache
  7. Retornar LLMAnalysisResult

  Em qualquer exceção das etapas 4–5: FallbackHandler.handle()

A engine determinística (P-04) NUNCA é chamada aqui — apenas prepara
o PromptContext antes de chamar este serviço.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_logger import AuditAction, AuditLogger
from app.core.config import settings
from app.llm.cache import LLMCache, build_cache_key
from app.llm.client import LLMClient
from app.llm.fallback import FallbackHandler
from app.llm.parser import LLMAnalysisResult, ResponseParser
from app.llm.prompt_builder import PromptBuilder, PromptContext

# Redis keys for token usage tracking
_USAGE_INPUT_KEY = "mentor:api_usage:input_tokens"
_USAGE_OUTPUT_KEY = "mentor:api_usage:output_tokens"


class LLMService:
    """Orquestra o ciclo completo de análise LLM com cache e fallback.

    Pode ser instanciado com dependências injetadas (útil para testes):
        service = LLMService(client=mock_client, cache=LLMCache(fake_redis))
    """

    def __init__(
        self,
        client: Optional[LLMClient] = None,
        cache: Optional[LLMCache] = None,
    ) -> None:
        self._client = client or LLMClient()
        self._cache = cache or LLMCache()

    async def _track_usage(self, input_tokens: int, output_tokens: int) -> None:
        """Acumula tokens consumidos no Redis (silencioso em falha)."""
        try:
            redis = await self._cache._get_redis()
            await redis.incrbyfloat(_USAGE_INPUT_KEY, input_tokens)
            await redis.incrbyfloat(_USAGE_OUTPUT_KEY, output_tokens)
        except Exception:
            pass

    async def get_api_balance(self) -> dict:
        """Retorna saldo estimado da API com base no uso acumulado de tokens."""
        budget = settings.API_CREDIT_BUDGET
        threshold = settings.API_CREDIT_WARNING_THRESHOLD
        input_price = settings.ANTHROPIC_INPUT_PRICE_PER_1M
        output_price = settings.ANTHROPIC_OUTPUT_PRICE_PER_1M

        input_tokens = 0
        output_tokens = 0
        try:
            redis = await self._cache._get_redis()
            raw_in = await redis.get(_USAGE_INPUT_KEY)
            raw_out = await redis.get(_USAGE_OUTPUT_KEY)
            input_tokens = int(float(raw_in)) if raw_in else 0
            output_tokens = int(float(raw_out)) if raw_out else 0
        except Exception:
            pass

        cost = (input_tokens * input_price / 1_000_000) + (output_tokens * output_price / 1_000_000)
        remaining = max(0.0, budget - cost)

        return {
            "budget": budget,
            "cost": round(cost, 4),
            "remaining": round(remaining, 4),
            "threshold": threshold,
            "warning": remaining <= threshold,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }

    async def analyze(
        self,
        ctx: PromptContext,
        session: AsyncSession,
        triggered_by: Optional[str] = None,
    ) -> LLMAnalysisResult:
        """Analisa um caso decisório financeiro com cache + fallback.

        Args:
            ctx: Contexto completo construído a partir do ORM object e
                 enriquecido pela engine determinística (P-04).
            session: Sessão SQLAlchemy ativa para gravar audit logs.
            triggered_by: Identificador do ator que acionou a análise
                          (ex: "user:uuid", "endpoint:/analyze").

        Returns:
            LLMAnalysisResult com llm_unavailable=False em sucesso
            ou llm_unavailable=True quando o fallback foi acionado.
        """
        # ── 1. Cache check ─────────────────────────────────────────────────
        cache_key = build_cache_key(ctx)
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return cached

        # ── 2. Build prompts ───────────────────────────────────────────────
        system_prompt, user_prompt = PromptBuilder.build(ctx)

        # ── 3 + 4 + 5. Call LLM → parse ───────────────────────────────────
        try:
            AuditLogger.log(
                session=session,
                action=AuditAction.LLM_CALLED,
                decision_case_id=ctx.case_id,
                payload={
                    "framework": ctx.framework_selected.value,
                    "triggered_by": triggered_by,
                },
            )

            completion = await self._client.complete_with_usage(system_prompt, user_prompt)
            await self._track_usage(completion.input_tokens, completion.output_tokens)
            result = ResponseParser.parse(completion.text)

            # ── 6. Cache result ────────────────────────────────────────────
            await self._cache.set(cache_key, result)

            return result

        except Exception as exc:
            # LLM unavailable, timeout, parse error → deterministic fallback
            return await FallbackHandler.handle(ctx, session, error=exc)

    async def generate_learning_summary(self, heuristics_data: list[dict]) -> Optional[str]:
        """Gera resumo executivo dos aprendizados via LLM.

        Retorna None em qualquer falha (non-blocking, mesmo padrão de validate_classification).
        """
        try:
            import re, json as _json
            system, user = PromptBuilder.build_learning_summary(heuristics_data)
            raw = await self._client.complete(system, user)
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if not m:
                return None
            data = _json.loads(m.group())
            return data.get("summary")
        except Exception:
            return None

    async def validate_relevance(self, text: str, domain: str) -> Optional[dict]:
        """Lightweight LLM call para validar relevância de documento. Retorna None em qualquer falha (non-blocking)."""
        try:
            import re, json as _json
            system, user = PromptBuilder.build_relevance_check(text, domain)
            raw = await self._client.complete(system, user)
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if not m:
                return None
            return _json.loads(m.group())
        except Exception:
            return None

    async def validate_classification(
        self,
        title: str,
        description: str,
        domain: "FinancialDomain",
        decision_type: "DecisionType",
    ) -> Optional["ClassificationSuggestionResponse"]:
        """Lightweight LLM call para validar classificação. Retorna None em qualquer falha (non-blocking)."""
        try:
            import re, json as _json
            from app.schemas import ClassificationSuggestionResponse
            system, user = PromptBuilder.build_classification_check(
                title, description, domain, decision_type
            )
            raw = await self._client.complete(system, user)
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if not m:
                return None
            data = _json.loads(m.group())
            return ClassificationSuggestionResponse(**data)
        except Exception:
            return None
