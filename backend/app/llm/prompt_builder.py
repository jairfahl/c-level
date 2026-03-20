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
    FrameworkType.decision_matrix: [
        "Identifique os critérios de decisão relevantes e atribua pesos percentuais (soma = 100%).",
        "Avalie cada alternativa disponível em cada critério numa escala de 1 a 10.",
        "Calcule o score ponderado total de cada alternativa e recomende a de maior pontuação.",
    ],
    FrameworkType.cost_benefit_analysis: [
        "Liste todos os custos envolvidos (diretos, indiretos, ocultos e de oportunidade).",
        "Liste todos os benefícios esperados (financeiros quantificáveis e intangíveis).",
        "Calcule NPV, TIR e payback period com taxa de desconto adequada ao perfil de risco.",
        "Conclua objetivamente se os benefícios justificam os custos no horizonte temporal declarado.",
    ],
    FrameworkType.decision_tree: [
        "Mapeie os nós de decisão (escolhas do executivo) e nós de chance (eventos incertos).",
        "Atribua probabilidades a cada ramo de chance (soma = 100% por nó) e payoffs monetários nas folhas.",
        "Calcule o EMV (Expected Monetary Value) de cada ramo e recomende o caminho de maior valor esperado.",
    ],
    FrameworkType.swot_analysis: [
        "Identifique as Forças (Strengths) internas da organização relevantes a esta decisão.",
        "Identifique as Fraquezas (Weaknesses) internas que podem comprometer a decisão.",
        "Mapeie as Oportunidades (Opportunities) externas que a decisão pode aproveitar.",
        "Mapeie as Ameaças (Threats) externas que podem impactar negativamente o resultado.",
        "Cruze os quadrantes (ex: Forças + Oportunidades) para derivar a recomendação estratégica.",
    ],
    FrameworkType.delphi_method: [
        "Identifique os stakeholders-chave e seus respectivos critérios e interesses na decisão.",
        "Sintetize as perspectivas divergentes e aponte os principais pontos de conflito.",
        "Proponha o caminho de maior consenso com mitigação explícita das divergências identificadas.",
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
    knowledge_snippets: list[str] = field(default_factory=list)
    heuristics_context: list[str] = field(default_factory=list)
    frameworks_selected: list["FrameworkType"] = field(default_factory=list)
    # Se preenchido, substitui framework_selected como lista de frameworks aplicados.
    # O primeiro item é sempre o framework principal.


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
            f"- **Framework(s) analítico(s):** "
            f"{', '.join(fw.value for fw in ctx.frameworks_selected) if ctx.frameworks_selected else ctx.framework_selected.value}\n"
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

        # ── § 3.5 Knowledge Base Context ─────────────────────────────────
        if ctx.knowledge_snippets:
            kb_parts = [
                "## Contexto da Base de Conhecimento Organizacional\n"
                "Os trechos abaixo são de documentos internos relevantes.\n"
                "Use-os como contexto adicional para fundamentar sua análise."
            ]
            for i, snippet in enumerate(ctx.knowledge_snippets, 1):
                kb_parts.append(f"**Documento {i}:**\n{snippet}")
            sections.append("\n---\n".join(kb_parts))

        # ── § 3.6 Heurísticas Organizacionais ─────────────────────────
        if ctx.heuristics_context:
            heuristic_parts = [
                "## Heurísticas Organizacionais Aprendidas\n"
                "Os padrões abaixo foram extraídos de decisões anteriores encerradas.\n"
                "Use-os como referência para calibrar sua análise e recomendação."
            ]
            for i, heuristic in enumerate(ctx.heuristics_context, 1):
                heuristic_parts.append(f"**Padrão {i}:**\n{heuristic}")
            sections.append("\n---\n".join(heuristic_parts))

        # ── § 4 Instructions (Multi-Framework aware) ────────────────────
        frameworks = ctx.frameworks_selected if ctx.frameworks_selected else [ctx.framework_selected]

        if len(frameworks) == 1:
            # Análise mono-framework (comportamento original)
            base = _FRAMEWORK_INSTRUCTIONS.get(
                frameworks[0],
                ["Analise a decisão com rigor metodológico e recomende a melhor alternativa."],
            )
            instructions: list[str] = list(base)
        else:
            # Análise multi-framework: instrui o LLM a aplicar cada lente
            instructions = [
                f"Esta análise utiliza **{len(frameworks)} frameworks complementares**. "
                "Aplique cada um como uma lente analítica distinta e, ao final, "
                "sintetize uma recomendação integrada que considere todas as perspectivas."
            ]
            for idx, fw in enumerate(frameworks, 1):
                fw_instructions = _FRAMEWORK_INSTRUCTIONS.get(
                    fw,
                    ["Analise a decisão com rigor metodológico."],
                )
                fw_body = " ".join(fw_instructions)
                label = "principal" if idx == 1 else "complementar"
                instructions.append(
                    f"**Framework {idx} ({fw.value} — {label}):** {fw_body}"
                )
            instructions.append(
                "Ao final, apresente uma **síntese integrada** que combine os insights "
                "de todos os frameworks aplicados em uma recomendação coerente e fundamentada."
            )

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

    @staticmethod
    def build_learning_summary(heuristics_data: list[dict]) -> tuple[str, str]:
        """Constrói prompts para gerar resumo executivo dos aprendizados.

        Args:
            heuristics_data: Lista de dicts com dados das heurísticas ativas.

        Returns:
            Tupla (system_prompt, user_prompt).
        """
        system = (
            "Você é um analista financeiro sênior. Sintetize os padrões aprendidos "
            "em um resumo executivo estruturado para C-Level. Máximo 500 caracteres. "
            "Formato: bullet points concisos agrupados por tema. Sem introdução, sem "
            "conclusão genérica. Apenas fatos e padrões. "
            'Responda APENAS JSON: {"summary": "..."}'
        )
        import json as _json
        user = (
            "## Heurísticas Financeiras Ativas\n\n"
            + _json.dumps(heuristics_data, ensure_ascii=False, indent=2)
        )
        return system, user

    @staticmethod
    def build_relevance_check(text_snippet: str, domain: str) -> tuple[str, str]:
        """Constrói prompts para validação de relevância de documento via LLM.

        Args:
            text_snippet: Primeiros ~2000 chars do texto extraído.
            domain: Domínio financeiro (ex: 'treasury', 'planning').

        Returns:
            Tupla (system_prompt, user_prompt).
        """
        system = (
            "Você é especialista em governança financeira C-Level. "
            "Avalie se o documento abaixo é relevante para o domínio financeiro indicado. "
            "Considere se o conteúdo trata de finanças corporativas, tesouraria, planejamento "
            "financeiro, gestão de riscos financeiros, estrutura de capital ou temas correlatos. "
            'Responda APENAS JSON válido: '
            '{"verdict": "relevant|borderline|irrelevant", '
            '"confidence": 0.0-1.0, '
            '"reason": "explicação em pt-BR, máx 60 palavras"}'
        )
        user = (
            f"Domínio financeiro: {domain}\n\n"
            f"Texto do documento (primeiros 2000 caracteres):\n{text_snippet[:2000]}"
        )
        return system, user

    @staticmethod
    def build_classification_check(
        title: str,
        description: str,
        current_domain: "FinancialDomain",
        current_decision_type: "DecisionType",
    ) -> tuple[str, str]:
        from app.models.enums import FinancialDomain, DecisionType
        domains = ", ".join(d.value for d in FinancialDomain)
        types   = ", ".join(t.value for t in DecisionType)
        system = (
            "Você é especialista em classificação de decisões financeiras C-Level. "
            "Analise título e descrição e avalie se domínio e tipo estão corretos. "
            f"Domínios disponíveis: {domains}. Tipos disponíveis: {types}. "
            'Responda APENAS JSON válido: '
            '{"reclassification_needed": bool, "suggested_domain": "valor ou null", '
            '"suggested_decision_type": "valor ou null", "confidence": 0.0-1.0, '
            '"reason": "explicação em pt-BR, máx 80 palavras"}'
        )
        user = (
            f'Título: "{title}"\n'
            f'Descrição: "{description}"\n'
            f"Domínio atual: {current_domain.value}\n"
            f"Tipo atual: {current_decision_type.value}"
        )
        return system, user
