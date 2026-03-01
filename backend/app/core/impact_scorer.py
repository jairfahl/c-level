"""
Financial Impact Scorer — CFO Mentor Engine

Calcula o impact_score de um caso decisório com base na exposição financeira
(financial_exposure em BRL) e determina se análise de cenários é obrigatória.

Tabela de escores (alinhada à Fase 2 da especificação):
  1 — Baixo:     exposure < R$ 100.000
  2 — Moderado:  R$ 100.000 ≤ exposure < R$ 500.000
  3 — Relevante: R$ 500.000 ≤ exposure < R$ 2.000.000
  4 — Alto:      R$ 2.000.000 ≤ exposure ≤ R$ 10.000.000
  5 — Crítico:   exposure > R$ 10.000.000

scenario_required = True quando impact_score ≥ 4 (alinhado ao campo readOnly do OpenAPI).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreResult:
    """Resultado imutável do cálculo de impacto."""

    impact_score: int
    scenario_required: bool


class FinancialImpactScorer:
    """Calcula o score de impacto financeiro de forma determinística e pura."""

    # Limites superiores exclusivos (exceto o último que é inclusivo via else)
    _THRESHOLDS: tuple[tuple[float, int], ...] = (
        (100_000.0,    1),
        (500_000.0,    2),
        (2_000_000.0,  3),
        (10_000_000.0, 4),  # inclusivo: <= 10M → score 4
    )

    @staticmethod
    def score(financial_exposure: float) -> ScoreResult:
        """Determina o impact_score e o flag scenario_required.

        Args:
            financial_exposure: Valor da exposição financeira em BRL (> 0).

        Returns:
            ScoreResult com impact_score (1–5) e scenario_required (bool).
        """
        if financial_exposure < 100_000.0:
            impact_score = 1
        elif financial_exposure < 500_000.0:
            impact_score = 2
        elif financial_exposure < 2_000_000.0:
            impact_score = 3
        elif financial_exposure <= 10_000_000.0:
            impact_score = 4
        else:
            impact_score = 5

        return ScoreResult(
            impact_score=impact_score,
            scenario_required=(impact_score >= 4),
        )
