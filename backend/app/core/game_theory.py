"""
Game Theory Activator — CFO Mentor Engine

Determina se o módulo de Teoria dos Jogos deve ser ativado para um caso
decisório, com base nos critérios da especificação Fase 2.

Critério de ativação:
  external_agents_present = True
  AND decision_type ∈ {debt_structuring, investment_evaluation, capital_allocation}

Quando ativo, o FrameworkSelector retornará FrameworkType.game_theory e o
contexto LLM será enriquecido com estrutura de jogos (players, strategies,
payoffs, equilibrium).

Este módulo é puramente determinístico — sem side effects e sem chamadas a LLM.
"""
from __future__ import annotations

from app.models.enums import DecisionType

# Tipos de decisão que qualificam para análise de Game Theory
# quando há contraparte externa (banco, competidor, regulador, etc.)
GAME_THEORY_ELIGIBLE_TYPES: frozenset[DecisionType] = frozenset({
    DecisionType.debt_structuring,
    DecisionType.investment_evaluation,
    DecisionType.capital_allocation,
})


class GameTheoryActivator:
    """Avalia se a análise de Teoria dos Jogos deve ser aplicada ao caso."""

    @staticmethod
    def is_active(
        decision_type: DecisionType,
        external_agents_present: bool,
    ) -> bool:
        """Retorna True se Game Theory deve ser ativada para este caso.

        Args:
            decision_type: Tipo de decisão financeira do caso.
            external_agents_present: Indica presença de contraparte externa.

        Returns:
            True se todos os critérios de ativação forem atendidos.
        """
        return external_agents_present and decision_type in GAME_THEORY_ELIGIBLE_TYPES
