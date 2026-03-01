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
from app.llm.cache import LLMCache, build_cache_key
from app.llm.client import LLMClient
from app.llm.fallback import FallbackHandler
from app.llm.parser import LLMAnalysisResult, ResponseParser
from app.llm.prompt_builder import PromptBuilder, PromptContext


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

            raw_text = await self._client.complete(system_prompt, user_prompt)
            result = ResponseParser.parse(raw_text)

            # ── 6. Cache result ────────────────────────────────────────────
            await self._cache.set(cache_key, result)

            return result

        except Exception as exc:
            # LLM unavailable, timeout, parse error → deterministic fallback
            return await FallbackHandler.handle(ctx, session, error=exc)
