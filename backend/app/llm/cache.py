"""
Cache Redis — LLM Layer

Cache de resultados de análise LLM com chave SHA-256 derivada dos inputs.
Falhas de cache (Redis indisponível, dados corrompidos) são silenciosas —
o sistema continua funcional sem cache (degradado, não quebrado).

Chave: llm:analysis:{SHA256(canonical_json_of_inputs)}
TTL:   86400s (24h) por padrão — configurável em LLM_CACHE_TTL.
"""
from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Optional

import redis.asyncio as aioredis

from app.core.config import settings
from app.llm.parser import LLMAnalysisResult
from app.llm.prompt_builder import PromptContext

if TYPE_CHECKING:
    pass

_KEY_PREFIX = "llm:analysis:"


def build_cache_key(ctx: PromptContext) -> str:
    """Deriva a chave de cache a partir dos inputs determinísticos da análise.

    Usa sorted() em assumptions e risks para que a ordem de inserção
    não afete o resultado da chave.

    Args:
        ctx: Contexto do caso decisório.

    Returns:
        String no formato ``llm:analysis:{sha256_hex}``.
    """
    data: dict = {
        "decision_type": ctx.decision_type.value,
        "framework": ctx.framework_selected.value,
        "scenario_required": ctx.scenario_required,
        "game_theory_active": ctx.game_theory_active,
        "assumptions": sorted(ctx.assumptions),
        "risks": sorted(ctx.risks),
        "knowledge_snippets": sorted(ctx.knowledge_snippets),
        "heuristics_context": sorted(ctx.heuristics_context),
    }
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=True)
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    return f"{_KEY_PREFIX}{digest}"


class LLMCache:
    """Cache Redis assíncrono para resultados de análise LLM.

    Aceita um cliente Redis externo (útil para testes com fakeredis).
    Se nenhum cliente for fornecido, cria uma conexão a partir de REDIS_URL.
    """

    def __init__(self, redis_client: Optional[aioredis.Redis] = None) -> None:
        self._redis = redis_client

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
        return self._redis

    async def get(self, key: str) -> Optional[LLMAnalysisResult]:
        """Recupera um resultado do cache.

        Returns:
            LLMAnalysisResult se encontrado e válido, None caso contrário.
        """
        try:
            redis = await self._get_redis()
            raw = await redis.get(key)
            if raw is None:
                return None
            return LLMAnalysisResult.model_validate(json.loads(raw))
        except Exception:
            return None  # cache miss silencioso

    async def set(
        self,
        key: str,
        result: LLMAnalysisResult,
        ttl: Optional[int] = None,
    ) -> None:
        """Armazena um resultado no cache com TTL.

        Falhas de escrita são silenciosas — não interrompem o fluxo principal.
        """
        effective_ttl = ttl if ttl is not None else settings.LLM_CACHE_TTL
        try:
            redis = await self._get_redis()
            await redis.setex(key, effective_ttl, result.model_dump_json())
        except Exception:
            pass  # cache write failure — degraded mode, not fatal
