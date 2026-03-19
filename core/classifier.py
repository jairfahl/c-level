"""
core/classifier.py
Engine determinístico de classificação de decisões.
Regras explícitas. Sem delegação ao LLM.
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from models.decision import (
    Classification,
    DecisionType,
    ImpactLevel,
    Reversibility,
    TimeHorizon,
)


# ─────────────────────────────────────────────
# VOCABULÁRIO DE CLASSIFICAÇÃO
# Cada chave é um padrão regex; valor é o tipo de decisão.
# Ordem importa — primeiro match vence.
# ─────────────────────────────────────────────

DECISION_TYPE_PATTERNS: list[tuple[re.Pattern, DecisionType]] = [
    (re.compile(r"\b(capit[ao]l|investimento|m&a|aquisi[cç][aã]o|desinvestimento|capex)\b", re.I), DecisionType.ALOCACAO_CAPITAL),
    (re.compile(r"\b(d[ií]vida|emiss[aã]o|financiamento|estrutura.de.capital|leverage|alavancagem|bond|debenture)\b", re.I), DecisionType.ESTRUTURA_FINANCEIRA),
    (re.compile(r"\b(caixa|liquidez|fluxo.de.caixa|capital.de.giro|working.capital|saldo)\b", re.I), DecisionType.GESTAO_CAIXA),
    (re.compile(r"\b(or[cç]amento|budget|planejamento.financeiro|plano.anual|LDO|LOA)\b", re.I), DecisionType.PLANEJAMENTO_ORCAMENTO),
    (re.compile(r"\b(forecast|revis[aã]o|proje[cç][aã]o|guidance|estimativa)\b", re.I), DecisionType.FORECAST),
    (re.compile(r"\b(risco|hedge|exposi[cç][aã]o|volatilidade|stress.test|VaR|mitig)\b", re.I), DecisionType.RISCO_FINANCEIRO),
]

IMPACT_KEYWORDS: dict[ImpactLevel, list[str]] = {
    ImpactLevel.CRITICO: [
        r"continuidade", r"insol[vê]ncia", r"crise", r"falência", r"ruptura",
        r"sistêmico", r"colapso", r"existencial",
    ],
    ImpactLevel.ELEVADO: [
        r"estrat[eé]gico", r"material", r"significativ", r"relevante",
        r"transform", r"restructur", r"reestrutur",
    ],
    ImpactLevel.MODERADO: [
        r"localizado", r"pontual", r"operacional", r"ajuste", r"revis[aã]o",
    ],
    ImpactLevel.BAIXO: [
        r"rotineiro", r"rotina", r"menor", r"marginal", r"pequeno",
    ],
}

REVERSIBILITY_PATTERNS: list[tuple[re.Pattern, Reversibility]] = [
    (re.compile(r"\b(irrevers[ií]vel|permanente|definitivo|fusão|aquisi[cç][aã]o)\b", re.I), Reversibility.IRREVERSIVEL),
    (re.compile(r"\b(parcial|condicional|rescis[aã]o|quebra.de.contrato)\b", re.I), Reversibility.PARCIALMENTE_REVERSIVEL),
    (re.compile(r"\b(revers[ií]vel|cancel[aá]vel|flex[ií]vel|ajust[aá]vel)\b", re.I), Reversibility.REVERSIVEL),
]

HORIZON_PATTERNS: list[tuple[re.Pattern, TimeHorizon]] = [
    (re.compile(r"\b(\d+\s*(?:dias?|semanas?|meses?)|curto.prazo|imediato|urgente)\b", re.I), TimeHorizon.CURTO_PRAZO),
    (re.compile(r"\b(ano|anual|12\s*meses|médio.prazo)\b", re.I), TimeHorizon.MEDIO_PRAZO),
    (re.compile(r"\b(plurianual|longo.prazo|estrat[eé]gico|3\s*anos|5\s*anos|décad)\b", re.I), TimeHorizon.LONGO_PRAZO),
]

STRATEGIC_INTERDEPENDENCE_PATTERNS = re.compile(
    r"\b(negocia[cç][aã]o|concorrente|competidor|mercado|banco|credor|investidor|"
    r"fornecedor.estrat[eé]gico|regulador|pricing|precifica[cç][aã]o|licita[cç][aã]o|"
    r"m&a|parceiro.estrat[eé]gico|contraparte)\b",
    re.I,
)

APQC_DOMAIN_MAP: dict[DecisionType, str] = {
    DecisionType.ALOCACAO_CAPITAL:       "Domínio 9 - Gestão Financeira / Alocação de Capital",
    DecisionType.ESTRUTURA_FINANCEIRA:   "Domínio 9 - Gestão Financeira / Estrutura de Capital",
    DecisionType.GESTAO_CAIXA:           "Domínio 9 - Gestão Financeira / Gestão de Caixa",
    DecisionType.PLANEJAMENTO_ORCAMENTO: "Domínio 9 - Gestão Financeira / Planejamento e Orçamento",
    DecisionType.FORECAST:               "Domínio 9 - Gestão Financeira / Forecast e Revisões",
    DecisionType.RISCO_FINANCEIRO:       "Domínio 9 - Gestão Financeira / Risco Financeiro",
    DecisionType.OUTRO:                  "Domínio 9 - Gestão Financeira / Outros",
}


# ─────────────────────────────────────────────
# RESULTADO INTERMEDIÁRIO
# ─────────────────────────────────────────────

@dataclass
class ClassificationResult:
    tipo_decisao: DecisionType
    impacto: ImpactLevel
    reversibilidade: Reversibility
    horizonte: TimeHorizon
    interdependencia_estrategica: bool
    dominio_apqc: str
    confianca: float          # 0.0–1.0
    flags: list[str]          # alertas do engine determinístico


# ─────────────────────────────────────────────
# CLASSIFIER
# ─────────────────────────────────────────────

class DecisionClassifier:
    """
    Engine determinístico de classificação.
    Regras explícitas. Zero delegação ao LLM.
    Retorna ClassificationResult para ser usado pelo LLM na geração do JSON final.
    """

    def classify(self, raw_input: str) -> ClassificationResult:
        tipo       = self._classify_type(raw_input)
        impacto    = self._classify_impact(raw_input, tipo)
        reversib   = self._classify_reversibility(raw_input, tipo)
        horizonte  = self._classify_horizon(raw_input, tipo)
        interdep   = self._has_strategic_interdependence(raw_input)
        flags      = self._generate_flags(raw_input, tipo, impacto, reversib, interdep)
        confianca  = self._compute_confidence(raw_input, tipo, impacto, reversib, horizonte)

        return ClassificationResult(
            tipo_decisao=tipo,
            impacto=impacto,
            reversibilidade=reversib,
            horizonte=horizonte,
            interdependencia_estrategica=interdep,
            dominio_apqc=APQC_DOMAIN_MAP[tipo],
            confianca=confianca,
            flags=flags,
        )

    # ── Tipo ──────────────────────────────────

    def _classify_type(self, text: str) -> DecisionType:
        for pattern, tipo in DECISION_TYPE_PATTERNS:
            if pattern.search(text):
                return tipo
        return DecisionType.OUTRO

    # ── Impacto ───────────────────────────────

    def _classify_impact(self, text: str, tipo: DecisionType) -> ImpactLevel:
        # Prioridade: keyword match sobre default por tipo
        for level in (ImpactLevel.CRITICO, ImpactLevel.ELEVADO, ImpactLevel.MODERADO, ImpactLevel.BAIXO):
            patterns = IMPACT_KEYWORDS[level]
            if any(re.search(p, text, re.I) for p in patterns):
                return level

        # Default determinístico por tipo quando não há keyword
        defaults: dict[DecisionType, ImpactLevel] = {
            DecisionType.ALOCACAO_CAPITAL:       ImpactLevel.ELEVADO,
            DecisionType.ESTRUTURA_FINANCEIRA:   ImpactLevel.ELEVADO,
            DecisionType.GESTAO_CAIXA:           ImpactLevel.MODERADO,
            DecisionType.PLANEJAMENTO_ORCAMENTO: ImpactLevel.MODERADO,
            DecisionType.FORECAST:               ImpactLevel.MODERADO,
            DecisionType.RISCO_FINANCEIRO:       ImpactLevel.ELEVADO,
            DecisionType.OUTRO:                  ImpactLevel.MODERADO,
        }
        return defaults[tipo]

    # ── Reversibilidade ───────────────────────

    def _classify_reversibility(self, text: str, tipo: DecisionType) -> Reversibility:
        for pattern, reversib in REVERSIBILITY_PATTERNS:
            if pattern.search(text):
                return reversib

        # Default por tipo
        defaults: dict[DecisionType, Reversibility] = {
            DecisionType.ALOCACAO_CAPITAL:       Reversibility.PARCIALMENTE_REVERSIVEL,
            DecisionType.ESTRUTURA_FINANCEIRA:   Reversibility.PARCIALMENTE_REVERSIVEL,
            DecisionType.GESTAO_CAIXA:           Reversibility.REVERSIVEL,
            DecisionType.PLANEJAMENTO_ORCAMENTO: Reversibility.REVERSIVEL,
            DecisionType.FORECAST:               Reversibility.REVERSIVEL,
            DecisionType.RISCO_FINANCEIRO:       Reversibility.PARCIALMENTE_REVERSIVEL,
            DecisionType.OUTRO:                  Reversibility.REVERSIVEL,
        }
        return defaults[tipo]

    # ── Horizonte ─────────────────────────────

    def _classify_horizon(self, text: str, tipo: DecisionType) -> TimeHorizon:
        for pattern, horizonte in HORIZON_PATTERNS:
            if pattern.search(text):
                return horizonte

        # Default por tipo
        defaults: dict[DecisionType, TimeHorizon] = {
            DecisionType.ALOCACAO_CAPITAL:       TimeHorizon.LONGO_PRAZO,
            DecisionType.ESTRUTURA_FINANCEIRA:   TimeHorizon.LONGO_PRAZO,
            DecisionType.GESTAO_CAIXA:           TimeHorizon.CURTO_PRAZO,
            DecisionType.PLANEJAMENTO_ORCAMENTO: TimeHorizon.MEDIO_PRAZO,
            DecisionType.FORECAST:               TimeHorizon.CURTO_PRAZO,
            DecisionType.RISCO_FINANCEIRO:       TimeHorizon.MEDIO_PRAZO,
            DecisionType.OUTRO:                  TimeHorizon.MEDIO_PRAZO,
        }
        return defaults[tipo]

    # ── Interdependência Estratégica ──────────

    def _has_strategic_interdependence(self, text: str) -> bool:
        return bool(STRATEGIC_INTERDEPENDENCE_PATTERNS.search(text))

    # ── Flags ─────────────────────────────────

    def _generate_flags(
        self,
        text: str,
        tipo: DecisionType,
        impacto: ImpactLevel,
        reversib: Reversibility,
        interdep: bool,
    ) -> list[str]:
        flags = []

        if tipo == DecisionType.OUTRO:
            flags.append("TIPO_NAO_IDENTIFICADO: classificação requer revisão manual ou input do LLM.")

        if impacto == ImpactLevel.CRITICO and reversib == Reversibility.IRREVERSIVEL:
            flags.append("RISCO_MAXIMAL: decisão crítica e irreversível. Protocolo completo obrigatório.")

        if interdep and tipo in (DecisionType.ESTRUTURA_FINANCEIRA, DecisionType.ALOCACAO_CAPITAL):
            flags.append("GAME_THEORY_ATIVADO: interdependência estratégica detectada em decisão de alto impacto.")

        if len(text.split()) < 15:
            flags.append("INPUT_INSUFICIENTE: descrição muito curta para classificação confiável. Solicitar mais contexto.")

        if impacto in (ImpactLevel.CRITICO, ImpactLevel.ELEVADO) and reversib == Reversibility.IRREVERSIVEL:
            flags.append("CENARIOS_OBRIGATORIOS: Etapa 05 não pode ser pulada.")

        return flags

    # ── Confiança ─────────────────────────────

    def _compute_confidence(
        self,
        text: str,
        tipo: DecisionType,
        impacto: ImpactLevel,
        reversib: Reversibility,
        horizonte: TimeHorizon,
    ) -> float:
        """
        Score de confiança da classificação determinística.
        0.0 = incerto, 1.0 = alta confiança.
        Abaixo de 0.5 → LLM deve revisar a classificação.
        """
        score = 0.0

        # Tipo identificado com certeza
        if tipo != DecisionType.OUTRO:
            score += 0.4

        # Impacto detectado por keyword (não por default)
        for level in IMPACT_KEYWORDS:
            if any(re.search(p, text, re.I) for p in IMPACT_KEYWORDS[level]):
                score += 0.2
                break

        # Reversibilidade detectada por keyword
        for pattern, _ in REVERSIBILITY_PATTERNS:
            if pattern.search(text):
                score += 0.2
                break

        # Horizonte detectado por keyword
        for pattern, _ in HORIZON_PATTERNS:
            if pattern.search(text):
                score += 0.2
                break

        return round(min(score, 1.0), 2)


    def to_classification(self, result: ClassificationResult, resumo: str, justificativa: str) -> Classification:
        """
        Converte ClassificationResult em schema Pydantic Classification.
        resumo e justificativa são gerados pelo LLM com base no ClassificationResult.
        """
        return Classification(
            tipo_decisao=result.tipo_decisao,
            impacto=result.impacto,
            reversibilidade=result.reversibilidade,
            horizonte=result.horizonte,
            interdependencia_estrategica=result.interdependencia_estrategica,
            dominio_apqc=result.dominio_apqc,
            decisao_resumida=resumo,
            justificativa_classificacao=justificativa,
        )


# ─────────────────────────────────────────────
# USO DIRETO (debug / teste rápido)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import json

    classifier = DecisionClassifier()

    casos_teste = [
        "Estamos avaliando a emissão de debêntures para refinanciar a dívida bancária de curto prazo e alongar o perfil de vencimento.",
        "Precisamos decidir se alocamos R$ 50MM em capex para expansão da planta ou distribuímos como dividendo.",
        "O forecast do Q3 precisa ser revisado dado o impacto cambial nas exportações.",
        "Negociação de renovação de linha de crédito rotativo com o banco principal. Há risco de o banco não renovar nas mesmas condições.",
        "Ajuste no budget de marketing do trimestre.",
    ]

    for caso in casos_teste:
        result = classifier.classify(caso)
        print(f"\nINPUT: {caso[:80]}...")
        print(f"  Tipo:          {result.tipo_decisao.value}")
        print(f"  Impacto:       {result.impacto.value}")
        print(f"  Reversib.:     {result.reversibilidade.value}")
        print(f"  Horizonte:     {result.horizonte.value}")
        print(f"  Interdep.:     {result.interdependencia_estrategica}")
        print(f"  Confiança:     {result.confianca}")
        if result.flags:
            print(f"  Flags:         {result.flags}")
