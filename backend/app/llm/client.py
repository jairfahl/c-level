"""
LLM Client — Anthropic Claude API

Wrapper fino sobre AsyncAnthropic. Não contém lógica de negócio — apenas
transporta SYSTEM + USER prompts e retorna o texto raw da resposta.

Configuração via Settings (app/core/config.py):
  ANTHROPIC_API_KEY   — obrigatório (lido da variável de ambiente)
  ANTHROPIC_MODEL     — modelo a usar (padrão: claude-3-5-sonnet-20241022)
  ANTHROPIC_MAX_TOKENS — limite de tokens (padrão: 4096)
  ANTHROPIC_TIMEOUT   — timeout em segundos (padrão: 30)
"""
from __future__ import annotations

from anthropic import AsyncAnthropic

from app.core.config import settings


class LLMClient:
    """Cliente assíncrono para a API Anthropic Claude.

    Instancie uma vez e reutilize — o AsyncAnthropic subjacente mantém
    connection pooling via httpx.
    """

    def __init__(self) -> None:
        self._client = AsyncAnthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            timeout=float(settings.ANTHROPIC_TIMEOUT),
        )

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Envia os prompts ao Claude e retorna o texto da resposta.

        Args:
            system_prompt: Persona e restrições do mentor financeiro.
            user_prompt: Contexto do caso + instruções + contrato JSON.

        Returns:
            Texto raw retornado pelo modelo (geralmente JSON).

        Raises:
            anthropic.APIError: Em erros de rede, autenticação ou limite de rate.
            anthropic.APITimeoutError: Quando o timeout é excedido.
        """
        message = await self._client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=settings.ANTHROPIC_MAX_TOKENS,
            temperature=0,  # saída determinística
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text
