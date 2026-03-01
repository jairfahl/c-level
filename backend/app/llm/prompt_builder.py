"""
Prompt Builder — LLM Layer

Constrói os prompts SYSTEM + USER enviados ao Claude para análise de casos
decisórios financeiros. Segue o template da Fase 4 da especificação CFO Mentor.

Template de saída exige JSON estrito — o parser downstream depende deste contrato.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from app.models.enums import DecisionType, FinancialDomain, FrameworkType, TimeHorizon

# ---------------------------------------------------------------------------
# System prompt — persona e restrições do Mentor
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a structured financial decision-making mentor for CFOs.\n"
    "Your role is to analyze financial decisions using rigorous methodology.\n"
    "Never provide opinions without structure. Always identify risks.\n"
    "Never skip assumption explicitiation.\n"
    "Output must follow the exact JSON contract defined below."
)

# ---------------------------------------------------------------------------
# Output JSON contract communicated to the model
# ---------------------------------------------------------------------------
_JSON_CONTRACT = """{
  "recommendation": "<string — recomendação estruturada e fundamentada>",
  "financial_metrics_impacted": ["<métrica 1>", "<métrica 2>"],
  "scenario_summary": "<string quando scenario_required=true, caso contrário null>",
  "implicit_assumptions_found": ["<premissa implícita detectada>"],
  "game_theory_model": {
    "players": ["<agente 1>", "<agente 2>"],
    "strategies": {"<agente>": ["<estratégia 1>", "<estratégia 2>"]},
    "payoffs": {"<combinação>": "<valor ou descrição>"},
    "equilibrium": "<equilíbrio de Nash ou null>",
    "strategic_risk": "<descrição do risco estratégico>"
  }
}

Return ONLY valid JSON. No markdown fences, no explanatory text."""

# ---------------------------------------------------------------------------
# Framework-specific analysis instructions
# ---------------------------------------------------------------------------
_FRAMEWORK_INSTRUCTIONS: dict[FrameworkType, list[str]] = {
    FrameworkType.pdca: [
        "Aplique o ciclo PDCA: identifique o problema (Plan), as ações corretivas (Do), "
        "métricas de controle (Check) e ajustes necessários (Act).",
        "Foque em variações orçamentárias, causas-raiz e ações de correção mensuráveis.",
    ],
    FrameworkType.scenario_analysis: [
        "Construa três cenários: pessimista, base e otimista.",
        "Para cada cenário, quantifique impacto em EBITDA, FCO e métricas-chave.",
        "Indique qual cenário tem maior probabilidade e justifique.",
    ],
    FrameworkType.game_theory: [
        "Identifique todos os agentes estratégicos (players) e suas motivações.",
        "Mapeie as estratégias disponíveis para cada agente.",
        "Calcule os payoffs estimados para cada combinação de estratégias.",
        "Identifique o equilíbrio de Nash ou estratégia dominante.",
        "Avalie o risco estratégico de cada posição.",
    ],
    FrameworkType.trade_off: [
        "Identifique os principais trade-offs entre as alternativas disponíveis.",
        "Quantifique custo de oportunidade, risco e benefício de cada opção.",
        "Recomende a opção com melhor equilíbrio risco/retorno.",
    ],
    FrameworkType.risk_matrix: [
        "Classifique cada risco identificado por probabilidade (1–5) e impacto financeiro (1–5).",
        "Priorize os riscos de maior score composto (probabilidade × impacto).",
        "Proponha mitigações específicas e mensuráveis para os top 3 riscos.",
    ],
    FrameworkType.capital_allocation: [
        "Avalie o retorno ajustado ao risco (ROIC vs WACC) de cada alternativa de alocação.",
        "Identifique o custo de oportunidade da decisão.",
        "Recomende a alocação que maximiza geração de valor para o acionista.",
    ],
}

_SCENARIO_INSTRUCTION = (
    "IMPORTANTE: scenario_required = true. Inclua 'scenario_summary' com análise dos "
    "cenários pessimista, base e otimista com impactos financeiros quantificados."
)

_GAME_THEORY_INSTRUCTION = (
    "IMPORTANTE: game_theory_active = true. Preencha obrigatoriamente o campo "
    "'game_theory_model' com players, strategies, payoffs, equilibrium e strategic_risk."
)

_IMPLICIT_ASSUMPTION_INSTRUCTION = (
    "Identifique premissas implícitas não declaradas pelo CFO que impactam materialmente "
    "a decisão e liste-as em 'implicit_assumptions_found'."
)


# ---------------------------------------------------------------------------
# PromptContext — contrato de entrada do Prompt Builder
# ---------------------------------------------------------------------------

@dataclass
class PromptContext:
    """Contexto completo do caso decisório para construção do prompt LLM.

    Criado pelo service layer a partir do ORM object e enriquecido pela
    engine determinística (P-04) antes de ser passado ao LLMService.
    """

    case_id: UUID
    decision_type: DecisionType
    financial_domain: FinancialDomain
    financial_exposure: float
    time_horizon: Optional[TimeHorizon]
    framework_selected: FrameworkType
    scenario_required: bool
    game_theory_active: bool
    assumptions: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Prompt Builder
# ---------------------------------------------------------------------------

class PromptBuilder:
    """Constrói os prompts SYSTEM + USER para análise pelo Claude."""

    @staticmethod
    def build(ctx: PromptContext) -> tuple[str, str]:
        """Retorna (system_prompt, user_prompt) prontos para envio ao Claude.

        Args:
            ctx: Contexto completo do caso decisório.

        Returns:
            Tupla (system_prompt, user_prompt).
        """
        return SYSTEM_PROMPT, PromptBuilder._build_user(ctx)

    @staticmethod
    def _build_user(ctx: PromptContext) -> str:
        horizon_str = ctx.time_horizon.value if ctx.time_horizon else "não especificado"
        sections: list[str] = []

        # ── § 1 Context ────────────────────────────────────────────────────
        sections.append(
            "## Contexto da Decisão\n"
            f"- **Tipo de decisão:** {ctx.decision_type.value}\n"
            f"- **Domínio financeiro:** {ctx.financial_domain.value}\n"
            f"- **Exposição financeira (BRL):** {ctx.financial_exposure:,.2f}\n"
            f"- **Horizonte temporal:** {horizon_str}\n"
            f"- **Framework analítico selecionado:** {ctx.framework_selected.value}\n"
            f"- **Análise de cenários obrigatória:** {'Sim' if ctx.scenario_required else 'Não'}\n"
            f"- **Teoria dos jogos ativa:** {'Sim' if ctx.game_theory_active else 'Não'}"
        )

        # ── § 2 Stated Assumptions ─────────────────────────────────────────
        if ctx.assumptions:
            assumptions_body = "\n".join(
                f"{i + 1}. {a}" for i, a in enumerate(ctx.assumptions)
            )
        else:
            assumptions_body = "Nenhuma premissa declarada."
        sections.append(f"## Premissas Declaradas\n{assumptions_body}")

        # ── § 3 Identified Risks ───────────────────────────────────────────
        if ctx.risks:
            risks_body = "\n".join(f"{i + 1}. {r}" for i, r in enumerate(ctx.risks))
        else:
            risks_body = "Nenhum risco declarado."
        sections.append(f"## Riscos Identificados\n{risks_body}")

        # ── § 4 Instructions ───────────────────────────────────────────────
        base = _FRAMEWORK_INSTRUCTIONS.get(
            ctx.framework_selected,
            ["Analise a decisão com rigor metodológico e recomende a melhor alternativa."],
        )
        instructions: list[str] = list(base)
        if ctx.scenario_required:
            instructions.append(_SCENARIO_INSTRUCTION)
        if ctx.game_theory_active:
            instructions.append(_GAME_THEORY_INSTRUCTION)
        instructions.append(_IMPLICIT_ASSUMPTION_INSTRUCTION)

        instructions_body = "\n".join(
            f"{i + 1}. {instr}" for i, instr in enumerate(instructions)
        )
        sections.append(f"## Instruções de Análise\n{instructions_body}")

        # ── § 5 Output JSON Contract ───────────────────────────────────────
        sections.append(f"## Contrato de Saída (JSON)\n{_JSON_CONTRACT}")

        return "\n\n".join(sections)
