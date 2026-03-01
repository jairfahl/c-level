"""
Framework Selector — CFO Mentor Engine

Seleciona automaticamente o framework analítico a ser aplicado em um caso
decisório, com base em decision_type e external_agents_present.

Regras de seleção (alinhadas à Fase 2 da especificação):

  Prioridade 1 — Game Theory (sobrescreve o mapeamento base):
    external_agents_present=True AND decision_type ∈ {debt_structuring,
    investment_evaluation, capital_allocation} → game_theory

  Prioridade 2 — Mapeamento determinístico por decision_type:
    budget_adjustment      → pdca
    forecast_revision      → scenario_analysis
    capital_allocation     → capital_allocation
    debt_structuring       → trade_off          (sem contraparte externa)
    liquidity_management   → risk_matrix
    risk_hedging           → risk_matrix
    cost_reduction         → trade_off
    investment_evaluation  → scenario_analysis  (sem contraparte externa)
"""
from __future__ import annotations

from app.models.enums import DecisionType, FrameworkType

# Tipos de decisão elegíveis para ativação de Game Theory
_GAME_THEORY_ELIGIBLE: frozenset[DecisionType] = frozenset({
    DecisionType.debt_structuring,
    DecisionType.investment_evaluation,
    DecisionType.capital_allocation,
})

# Mapeamento base: decision_type → framework (quando game theory NÃO está ativa)
_BASE_FRAMEWORK: dict[DecisionType, FrameworkType] = {
    DecisionType.budget_adjustment:    FrameworkType.pdca,
    DecisionType.forecast_revision:    FrameworkType.scenario_analysis,
    DecisionType.capital_allocation:   FrameworkType.capital_allocation,
    DecisionType.debt_structuring:     FrameworkType.trade_off,
    DecisionType.liquidity_management: FrameworkType.risk_matrix,
    DecisionType.risk_hedging:         FrameworkType.risk_matrix,
    DecisionType.cost_reduction:       FrameworkType.trade_off,
    DecisionType.investment_evaluation: FrameworkType.scenario_analysis,
}


class FrameworkSelector:
    """Seleciona o framework analítico de forma determinística e pura."""

    @staticmethod
    def select(
        decision_type: DecisionType,
        external_agents_present: bool,
    ) -> FrameworkType:
        """Retorna o FrameworkType apropriado para o caso.

        Args:
            decision_type: Tipo de decisão financeira do caso.
            external_agents_present: Indica presença de contraparte externa
                                     (banco, competidor, regulador).

        Returns:
            FrameworkType selecionado pela engine determinística.
        """
        if external_agents_present and decision_type in _GAME_THEORY_ELIGIBLE:
            return FrameworkType.game_theory

        return _BASE_FRAMEWORK[decision_type]
