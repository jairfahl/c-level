"""
Relevance Validator — Validação determinística de relevância de documentos para o domínio financeiro.

Analisa os primeiros 3000 caracteres do texto extraído e classifica como:
- RELEVANT: conteúdo claramente financeiro
- BORDERLINE: conteúdo misto ou ambíguo
- IRRELEVANT: conteúdo fora do domínio financeiro
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class RelevanceVerdict(str, Enum):
    RELEVANT = "relevant"
    BORDERLINE = "borderline"
    IRRELEVANT = "irrelevant"


@dataclass(frozen=True)
class RelevanceResult:
    verdict: RelevanceVerdict
    confidence: float
    reason: str
    domain_keywords_found: list[str] = field(default_factory=list)
    off_topic_keywords_found: list[str] = field(default_factory=list)


# ── Keyword dictionaries ──────────────────────────────────────────────────

FINANCIAL_KEYWORDS: set[str] = {
    # PT-BR
    "ebitda", "wacc", "irr", "tir", "npv", "vpl", "dcf", "capex", "opex",
    "dre", "hedge", "fluxo de caixa", "balanço patrimonial", "receita líquida",
    "margem bruta", "margem ebitda", "margem líquida", "custo de capital",
    "estrutura de capital", "alavancagem", "endividamento", "divida",
    "amortização", "depreciação", "ativo circulante", "passivo circulante",
    "capital de giro", "orçamento", "forecast", "projeção financeira",
    "roi", "roic", "roe", "payback", "valuation", "lucro líquido",
    "lucro operacional", "resultado financeiro", "juros", "selic", "cdi",
    "câmbio", "inflação", "ipca", "igpm", "tesouraria", "caixa",
    "liquidez", "solvência", "rating", "covenants", "debênture",
    "emissão de dívida", "captação", "financiamento", "investimento",
    "alocação de capital", "risco financeiro", "risco de mercado",
    "risco de crédito", "risco de liquidez", "hedge cambial",
    "derivativos", "swap", "ndf", "opção", "taxa de juros",
    "custo fixo", "custo variável", "ponto de equilíbrio", "break-even",
    "demonstração de resultados", "fluxo de caixa descontado",
    "planejamento financeiro", "gestão financeira", "controladoria",
    "auditoria financeira", "compliance financeiro", "governança",
    "orçamento de capital", "budget", "p&l", "balance sheet",
    "cash flow", "free cash flow", "fcf", "fco", "ebit",
    "net income", "gross margin", "operating margin", "debt ratio",
    "leverage", "working capital", "accounts receivable", "accounts payable",
    "treasury", "funding", "capital structure", "cost of debt",
    "cost of equity", "beta", "risk premium", "discount rate",
    "terminal value", "enterprise value", "equity value",
}

OFF_TOPIC_KEYWORDS: set[str] = {
    "pipeline de vendas", "funil de vendas", "leads", "mql", "sql qualificado",
    "recrutamento", "seleção de candidatos", "onboarding de funcionários",
    "marketing digital", "seo", "sem", "google ads", "facebook ads",
    "social media", "engajamento", "followers", "curtidas",
    "sprint", "deploy", "kubernetes", "docker", "devops", "ci/cd",
    "pull request", "code review", "microserviços", "api gateway",
    "machine learning", "deep learning", "neural network",
    "user experience", "wireframe", "figma", "design system",
    "backlog de produto", "product discovery", "user story",
    "okr de vendas", "quota de vendas", "comissão de vendas",
    "nps", "customer success", "churn de clientes",
    "logística", "supply chain", "estoque de produtos",
    "receita de marketing", "campanha publicitária",
}

SCAN_LENGTH = 3000


class RelevanceValidator:
    """Valida se o texto de um documento é relevante para o domínio financeiro."""

    @staticmethod
    def validate(text: str, domain: str = "financial") -> RelevanceResult:
        """Analisa os primeiros SCAN_LENGTH caracteres e retorna um RelevanceResult."""
        snippet = text[:SCAN_LENGTH].lower()

        positive_found: list[str] = []
        for kw in FINANCIAL_KEYWORDS:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, snippet):
                positive_found.append(kw)

        negative_found: list[str] = []
        for kw in OFF_TOPIC_KEYWORDS:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, snippet):
                negative_found.append(kw)

        pos_count = len(positive_found)
        neg_count = len(negative_found)

        if pos_count >= 3 and neg_count == 0:
            return RelevanceResult(
                verdict=RelevanceVerdict.RELEVANT,
                confidence=0.9,
                reason=f"Documento contém {pos_count} termos financeiros relevantes.",
                domain_keywords_found=sorted(positive_found),
                off_topic_keywords_found=[],
            )

        if pos_count >= 1 and neg_count <= pos_count:
            confidence = 0.5 + min(0.2, pos_count * 0.05)
            return RelevanceResult(
                verdict=RelevanceVerdict.BORDERLINE,
                confidence=round(confidence, 2),
                reason=(
                    f"Documento contém {pos_count} termo(s) financeiro(s) mas também "
                    f"{neg_count} termo(s) de outros domínios. Verifique se é adequado."
                ),
                domain_keywords_found=sorted(positive_found),
                off_topic_keywords_found=sorted(negative_found),
            )

        reason = (
            f"Documento não parece ser financeiro. "
            f"Termos financeiros: {pos_count}, termos fora do domínio: {neg_count}."
        )
        return RelevanceResult(
            verdict=RelevanceVerdict.IRRELEVANT,
            confidence=0.85 if neg_count > 0 else 0.6,
            reason=reason,
            domain_keywords_found=sorted(positive_found),
            off_topic_keywords_found=sorted(negative_found),
        )
