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

from dataclasses import dataclass

from anthropic import AsyncAnthropic

from app.core.config import settings


@dataclass(frozen=True)
class CompletionResult:
    """Resultado de uma chamada ao Claude com métricas de uso."""
    text: str
    input_tokens: int = 0
    output_tokens: int = 0


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
        result = await self.complete_with_usage(system_prompt, user_prompt)
        return result.text

    async def complete_with_usage(self, system_prompt: str, user_prompt: str) -> CompletionResult:
        """Envia os prompts ao Claude e retorna texto + métricas de uso de tokens.

        Returns:
            CompletionResult com text, input_tokens e output_tokens.
        """
        message = await self._client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=settings.ANTHROPIC_MAX_TOKENS,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return CompletionResult(
            text=message.content[0].text,
            input_tokens=getattr(message.usage, "input_tokens", 0),
            output_tokens=getattr(message.usage, "output_tokens", 0),
        )
