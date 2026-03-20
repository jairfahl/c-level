"""
Framework Selector — CFO Mentor Engine

Seleciona automaticamente o framework analítico a ser aplicado em um caso
decisório, com base em decision_type e external_agents_present.

Multi-Framework Selection (v2): método suggest() retorna lista priorizada
de frameworks para apresentação ao executivo antes da análise.

Catálogo Rico (v3): FRAMEWORK_CATALOG fornece metadata completa (descrição,
complexidade, combinações recomendadas) para cada framework. Métodos
catalog() e suggest_detailed() expõem esses dados para a API.
"""
from __future__ import annotations

from typing import Any

from app.models.enums import DecisionType, FrameworkType

# Tipos de decisão elegíveis para ativação de Game Theory
_GAME_THEORY_ELIGIBLE: frozenset[DecisionType] = frozenset({
    DecisionType.debt_structuring,
    DecisionType.investment_evaluation,
    DecisionType.capital_allocation,
})

# Mapeamento base: decision_type → framework primário
_BASE_FRAMEWORK: dict[DecisionType, FrameworkType] = {
    DecisionType.budget_adjustment:     FrameworkType.pdca,
    DecisionType.forecast_revision:     FrameworkType.scenario_analysis,
    DecisionType.capital_allocation:    FrameworkType.capital_allocation,
    DecisionType.debt_structuring:      FrameworkType.trade_off,
    DecisionType.liquidity_management:  FrameworkType.risk_matrix,
    DecisionType.risk_hedging:          FrameworkType.risk_matrix,
    DecisionType.cost_reduction:        FrameworkType.trade_off,
    DecisionType.investment_evaluation: FrameworkType.scenario_analysis,
}

# Justificativas por framework — exibidas ao executivo no painel de seleção
FRAMEWORK_RATIONALE: dict[FrameworkType, str] = {
    FrameworkType.pdca:                  "Ajuste recorrente — PDCA estrutura ciclos de melhoria e controle.",
    FrameworkType.scenario_analysis:     "Incerteza elevada — quantifica futuros pessimista, base e otimista.",
    FrameworkType.game_theory:           "Contraparte externa — mapeia estratégias, payoffs e equilíbrio de Nash.",
    FrameworkType.trade_off:             "Alternativas excludentes — clarifica custo de oportunidade de cada opção.",
    FrameworkType.risk_matrix:           "Múltiplos riscos — prioriza por probabilidade × impacto financeiro.",
    FrameworkType.capital_allocation:    "Alocação entre projetos — maximiza geração de valor (ROIC vs WACC).",
    FrameworkType.decision_matrix:       "Múltiplas alternativas — scoring ponderado por critérios estrutura a escolha.",
    FrameworkType.cost_benefit_analysis: "Exposição elevada — quantifica NPV, IRR e payback da decisão.",
    FrameworkType.decision_tree:         "Alto impacto com bifurcações — calcula EMV probabilístico por caminho.",
    FrameworkType.swot_analysis:         "Contexto competitivo — mapeia forças, fraquezas, oportunidades e ameaças.",
    FrameworkType.delphi_method:         "Múltiplos stakeholders — consenso iterativo estruturado.",
}

# ---------------------------------------------------------------------------
# Catálogo rico de frameworks — metadata completa para UI guiada
# ---------------------------------------------------------------------------

FRAMEWORK_CATALOG: dict[FrameworkType, dict[str, Any]] = {
    FrameworkType.pdca: {
        "name": "PDCA",
        "description": (
            "Estrutura ciclos iterativos de Plan-Do-Check-Act para decisões "
            "operacionais recorrentes. Ideal quando o objetivo é melhoria "
            "contínua com métricas de controle."
        ),
        "icon_label": "cycle",
        "complexity": "baixa",
        "recommended_for": [
            DecisionType.budget_adjustment,
            DecisionType.cost_reduction,
        ],
        "pairs_well_with": [
            FrameworkType.risk_matrix,
            FrameworkType.cost_benefit_analysis,
        ],
        "rationale": FRAMEWORK_RATIONALE[FrameworkType.pdca],
    },
    FrameworkType.scenario_analysis: {
        "name": "Análise de Cenários",
        "description": (
            "Quantifica futuros pessimista, base e otimista com probabilidades "
            "associadas. Recomendado quando há alta incerteza macroeconômica "
            "ou múltiplas variáveis externas relevantes."
        ),
        "icon_label": "bar-chart",
        "complexity": "média",
        "recommended_for": [
            DecisionType.forecast_revision,
            DecisionType.investment_evaluation,
            DecisionType.capital_allocation,
        ],
        "pairs_well_with": [
            FrameworkType.decision_tree,
            FrameworkType.cost_benefit_analysis,
            FrameworkType.risk_matrix,
        ],
        "rationale": FRAMEWORK_RATIONALE[FrameworkType.scenario_analysis],
    },
    FrameworkType.game_theory: {
        "name": "Teoria dos Jogos",
        "description": (
            "Modela interações estratégicas com contrapartes externas — mapeia "
            "estratégias, payoffs e identifica equilíbrios de Nash. Essencial "
            "quando o resultado depende das ações de terceiros."
        ),
        "icon_label": "users",
        "complexity": "alta",
        "recommended_for": [
            DecisionType.debt_structuring,
            DecisionType.investment_evaluation,
            DecisionType.capital_allocation,
        ],
        "pairs_well_with": [
            FrameworkType.scenario_analysis,
            FrameworkType.trade_off,
        ],
        "rationale": FRAMEWORK_RATIONALE[FrameworkType.game_theory],
    },
    FrameworkType.trade_off: {
        "name": "Trade-Off",
        "description": (
            "Clarifica o custo de oportunidade entre alternativas mutuamente "
            "excludentes. Estrutura a comparação quando é preciso abrir mão "
            "de um benefício para obter outro."
        ),
        "icon_label": "scale",
        "complexity": "média",
        "recommended_for": [
            DecisionType.debt_structuring,
            DecisionType.cost_reduction,
            DecisionType.capital_allocation,
        ],
        "pairs_well_with": [
            FrameworkType.cost_benefit_analysis,
            FrameworkType.decision_matrix,
        ],
        "rationale": FRAMEWORK_RATIONALE[FrameworkType.trade_off],
    },
    FrameworkType.risk_matrix: {
        "name": "Matriz de Riscos",
        "description": (
            "Prioriza riscos por probabilidade × impacto financeiro. "
            "Fundamental para decisões onde múltiplos riscos competem por "
            "atenção e recursos de mitigação."
        ),
        "icon_label": "grid",
        "complexity": "baixa",
        "recommended_for": [
            DecisionType.liquidity_management,
            DecisionType.risk_hedging,
        ],
        "pairs_well_with": [
            FrameworkType.scenario_analysis,
            FrameworkType.swot_analysis,
        ],
        "rationale": FRAMEWORK_RATIONALE[FrameworkType.risk_matrix],
    },
    FrameworkType.capital_allocation: {
        "name": "Alocação de Capital",
        "description": (
            "Maximiza geração de valor comparando ROIC vs WACC entre projetos "
            "concorrentes. Ideal para decisões de portfólio e distribuição de "
            "recursos entre iniciativas."
        ),
        "icon_label": "coins",
        "complexity": "alta",
        "recommended_for": [
            DecisionType.capital_allocation,
            DecisionType.investment_evaluation,
        ],
        "pairs_well_with": [
            FrameworkType.decision_matrix,
            FrameworkType.cost_benefit_analysis,
        ],
        "rationale": FRAMEWORK_RATIONALE[FrameworkType.capital_allocation],
    },
    FrameworkType.decision_matrix: {
        "name": "Matriz de Decisão",
        "description": (
            "Scoring ponderado por critérios múltiplos para comparar alternativas "
            "de forma estruturada. Útil quando há mais de 2 opções e múltiplos "
            "critérios de avaliação."
        ),
        "icon_label": "table",
        "complexity": "média",
        "recommended_for": [
            DecisionType.capital_allocation,
            DecisionType.investment_evaluation,
            DecisionType.cost_reduction,
        ],
        "pairs_well_with": [
            FrameworkType.trade_off,
            FrameworkType.cost_benefit_analysis,
        ],
        "rationale": FRAMEWORK_RATIONALE[FrameworkType.decision_matrix],
    },
    FrameworkType.cost_benefit_analysis: {
        "name": "Custo-Benefício",
        "description": (
            "Quantifica NPV, IRR e payback da decisão para avaliar viabilidade "
            "financeira. Recomendado quando a exposição financeira é elevada e "
            "o retorno precisa ser mensurado com precisão."
        ),
        "icon_label": "calculator",
        "complexity": "média",
        "recommended_for": [
            DecisionType.investment_evaluation,
            DecisionType.capital_allocation,
            DecisionType.debt_structuring,
        ],
        "pairs_well_with": [
            FrameworkType.scenario_analysis,
            FrameworkType.decision_tree,
        ],
        "rationale": FRAMEWORK_RATIONALE[FrameworkType.cost_benefit_analysis],
    },
    FrameworkType.decision_tree: {
        "name": "Árvore de Decisão",
        "description": (
            "Calcula EMV (Expected Monetary Value) probabilístico por caminho "
            "decisório. Ideal quando a decisão apresenta bifurcações sequenciais "
            "com impactos financeiros distintos."
        ),
        "icon_label": "git-branch",
        "complexity": "alta",
        "recommended_for": [
            DecisionType.investment_evaluation,
            DecisionType.capital_allocation,
            DecisionType.debt_structuring,
        ],
        "pairs_well_with": [
            FrameworkType.scenario_analysis,
            FrameworkType.cost_benefit_analysis,
        ],
        "rationale": FRAMEWORK_RATIONALE[FrameworkType.decision_tree],
    },
    FrameworkType.swot_analysis: {
        "name": "SWOT / FOFA",
        "description": (
            "Mapeia Forças, Fraquezas, Oportunidades e Ameaças no contexto "
            "competitivo. Recomendado para decisões estratégicas que envolvem "
            "posicionamento de mercado."
        ),
        "icon_label": "crosshair",
        "complexity": "baixa",
        "recommended_for": [
            DecisionType.investment_evaluation,
            DecisionType.forecast_revision,
        ],
        "pairs_well_with": [
            FrameworkType.risk_matrix,
            FrameworkType.scenario_analysis,
        ],
        "rationale": FRAMEWORK_RATIONALE[FrameworkType.swot_analysis],
    },
    FrameworkType.delphi_method: {
        "name": "Método Delphi",
        "description": (
            "Consenso iterativo estruturado entre múltiplos especialistas ou "
            "stakeholders. Indicado quando a decisão exige convergência de "
            "opiniões diversas antes da deliberação."
        ),
        "icon_label": "message-circle",
        "complexity": "alta",
        "recommended_for": [
            DecisionType.forecast_revision,
            DecisionType.capital_allocation,
        ],
        "pairs_well_with": [
            FrameworkType.scenario_analysis,
            FrameworkType.swot_analysis,
        ],
        "rationale": FRAMEWORK_RATIONALE[FrameworkType.delphi_method],
    },
}


class FrameworkSelector:
    """Seleciona e sugere frameworks analíticos de forma determinística."""

    @staticmethod
    def select(
        decision_type: DecisionType,
        external_agents_present: bool,
    ) -> FrameworkType:
        """Retorna o FrameworkType primário para o caso."""
        if external_agents_present and decision_type in _GAME_THEORY_ELIGIBLE:
            return FrameworkType.game_theory
        return _BASE_FRAMEWORK[decision_type]

    @staticmethod
    def suggest(
        decision_type: DecisionType,
        external_agents_present: bool,
        impact_score: int | None = None,
        financial_exposure: float | None = None,
    ) -> list[FrameworkType]:
        """Retorna lista priorizada de frameworks sugeridos (primary first, máx 3).

        O primeiro item é o framework principal (obrigatório).
        Os demais são sugestões secundárias baseadas no contexto do caso.
        """
        primary = FrameworkSelector.select(decision_type, external_agents_present)
        suggestions: list[FrameworkType] = [primary]

        # Árvore de Decisão: alto impacto com múltiplos cenários
        if (impact_score or 0) >= 4 and FrameworkType.decision_tree not in suggestions:
            suggestions.append(FrameworkType.decision_tree)

        # Custo-Benefício: exposição financeira elevada
        if (financial_exposure or 0) >= 2_000_000 and FrameworkType.cost_benefit_analysis not in suggestions:
            suggestions.append(FrameworkType.cost_benefit_analysis)

        # Matriz de Decisão: múltiplas alternativas de alocação
        if decision_type in (DecisionType.capital_allocation, DecisionType.investment_evaluation) \
                and FrameworkType.decision_matrix not in suggestions:
            suggestions.append(FrameworkType.decision_matrix)

        return suggestions[:3]

    @staticmethod
    def available() -> list[FrameworkType]:
        """Retorna todos os frameworks disponíveis para seleção manual."""
        return list(FrameworkType)

    @staticmethod
    def catalog() -> list[dict[str, Any]]:
        """Retorna catálogo completo de frameworks com metadata rica."""
        entries: list[dict[str, Any]] = []
        for fw, meta in FRAMEWORK_CATALOG.items():
            entries.append({
                "framework": fw,
                "name": meta["name"],
                "description": meta["description"],
                "icon_label": meta["icon_label"],
                "complexity": meta["complexity"],
                "recommended_for": meta["recommended_for"],
                "pairs_well_with": meta["pairs_well_with"],
                "rationale": meta["rationale"],
            })
        return entries

    @staticmethod
    def suggest_detailed(
        decision_type: DecisionType,
        external_agents_present: bool,
        impact_score: int | None = None,
        financial_exposure: float | None = None,
    ) -> list[dict[str, Any]]:
        """Retorna sugestões com metadata rica e why_suggested contextual."""
        suggested = FrameworkSelector.suggest(
            decision_type, external_agents_present,
            impact_score=impact_score,
            financial_exposure=financial_exposure,
        )
        primary = suggested[0] if suggested else None
        result: list[dict[str, Any]] = []
        for fw in suggested:
            meta = FRAMEWORK_CATALOG.get(fw, {})
            if fw == primary:
                why = f"Framework principal para decisões de {decision_type.value}."
            elif fw == FrameworkType.decision_tree:
                why = f"Recomendado: impacto elevado (score {impact_score}) requer mapeamento de bifurcações."
            elif fw == FrameworkType.cost_benefit_analysis:
                exp_label = f"R$ {(financial_exposure or 0):,.0f}"
                why = f"Recomendado: exposição financeira elevada ({exp_label}) exige quantificação rigorosa."
            elif fw == FrameworkType.decision_matrix:
                why = "Recomendado: múltiplas alternativas de alocação exigem scoring ponderado."
            else:
                why = meta.get("rationale", "")
            result.append({
                "framework": fw,
                "name": meta.get("name", fw.value),
                "description": meta.get("description", ""),
                "icon_label": meta.get("icon_label", ""),
                "complexity": meta.get("complexity", "média"),
                "is_primary": fw == primary,
                "why_suggested": why,
                "pairs_well_with": meta.get("pairs_well_with", []),
                "recommended_for": meta.get("recommended_for", []),
            })
        return result
