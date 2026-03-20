"""
Response Parser — LLM Layer

Extrai e valida o JSON retornado pelo Claude.
Suporta resposta em JSON puro ou dentro de um bloco markdown ```json ... ```.

Qualquer resposta que não satisfaça o schema LLMAnalysisResult levanta
LLMParseError — o caller (service.py) trata isso como fallback.
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional

from pydantic import BaseModel, Field, ValidationError

from app.schemas import GameTheoryModel


class LLMParseError(Exception):
    """Levantada quando a resposta do LLM não pode ser convertida em LLMAnalysisResult."""


class LLMAnalysisResult(BaseModel):
    """Resultado validado da análise gerada pelo Claude.

    Subconjunto de AnalysisResponse (sem `state` e `framework_selected`,
    que são adicionados pela camada de serviço antes de retornar ao cliente).
    """

    recommendation: str
    financial_metrics_impacted: list[str] = Field(default_factory=list)
    scenario_summary: Optional[str] = None
    implicit_assumptions_found: list[str] = Field(default_factory=list)
    game_theory_model: Optional[GameTheoryModel] = None
    llm_unavailable: bool = False


class ResponseParser:
    """Extrai e valida o output JSON do Claude."""

    @staticmethod
    def parse(raw_text: str) -> LLMAnalysisResult:
        """Converte o texto raw do LLM em LLMAnalysisResult validado.

        Args:
            raw_text: Texto completo retornado pelo Claude.

        Returns:
            LLMAnalysisResult com os campos preenchidos.

        Raises:
            LLMParseError: Se nenhum JSON válido for encontrado ou a validação Pydantic falhar.
        """
        data = ResponseParser._extract_json(raw_text)
        ResponseParser._normalize_game_theory(data)
        try:
            return LLMAnalysisResult.model_validate(data)
        except ValidationError as exc:
            raise LLMParseError(
                f"LLM output failed schema validation: {exc}"
            ) from exc

    @staticmethod
    def _normalize_game_theory(data: dict[str, Any]) -> None:
        """Set game_theory_model to None when the LLM returns it with null sub-fields.

        The prompt contract always includes the game_theory_model key, so the LLM
        often returns it with null values even when game theory is not active.
        """
        gt = data.get("game_theory_model")
        if gt is None:
            return
        # If it's a dict where all values are None/empty, discard it
        if isinstance(gt, dict) and all(v is None or v == [] or v == {} for v in gt.values()):
            data["game_theory_model"] = None

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        """Extrai o primeiro objeto JSON do texto.

        Tenta, em ordem:
        1. Bloco markdown ```json ... ``` ou ``` ... ```
        2. Objeto JSON raw (primeira ocorrência de { ... })
        """
        # Attempt 1: markdown code fence
        fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fence_match:
            try:
                return json.loads(fence_match.group(1))
            except json.JSONDecodeError:
                pass

        # Attempt 2: raw JSON object (greedy — takes the largest { ... })
        raw_match = re.search(r"\{.*\}", text, re.DOTALL)
        if raw_match:
            try:
                return json.loads(raw_match.group(0))
            except json.JSONDecodeError:
                pass

        raise LLMParseError(
            f"No valid JSON found in LLM response. First 300 chars: {text[:300]!r}"
        )
