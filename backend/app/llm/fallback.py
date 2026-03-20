"""
Fallback Handler — LLM Layer

Retorna uma LLMAnalysisResult parcial com llm_unavailable=True quando o LLM
está indisponível (timeout, erro de API, falha de parse).

Métricas financeiras são preenchidas deterministicamente por framework —
sem dependência de LLM.

O audit_log é gravado com action=LLM_FALLBACK para rastreabilidade.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_logger import AuditAction, AuditLogger
from app.llm.parser import LLMAnalysisResult
from app.llm.prompt_builder import PromptContext
from app.models.enums import FrameworkType

# ---------------------------------------------------------------------------
# Métricas padrão por framework (modo determinístico puro)
# ---------------------------------------------------------------------------
_FRAMEWORK_DEFAULT_METRICS: dict[FrameworkType, list[str]] = {
    FrameworkType.pdca:             ["EBITDA", "OpEx", "Variância Orçamentária"],
    FrameworkType.scenario_analysis: ["Receita Líquida", "Margem EBITDA", "FCO"],
    FrameworkType.game_theory:      ["VPL", "TIR", "Payback", "Custo do Capital"],
    FrameworkType.trade_off:        ["EBITDA", "Custo Médio Ponderado de Capital"],
    FrameworkType.risk_matrix:      ["VaR", "Exposição Financeira", "Índice de Liquidez"],
    FrameworkType.capital_allocation:    ["ROIC", "WACC", "VPL", "TIR"],
    FrameworkType.decision_matrix:       ["Score Ponderado", "Critérios de Decisão", "Ranking de Alternativas"],
    FrameworkType.cost_benefit_analysis: ["NPV", "TIR", "Payback Period", "Relação Custo-Benefício"],
    FrameworkType.decision_tree:         ["EMV", "Probabilidade por Ramo", "Payoff Esperado"],
    FrameworkType.swot_analysis:         ["Forças", "Fraquezas", "Oportunidades", "Ameaças"],
    FrameworkType.delphi_method:         ["Grau de Consenso", "Convergência de Opiniões", "Stakeholder Alignment"],
}

_FALLBACK_RECOMMENDATION = (
    "Análise em modo determinístico (LLM indisponível). "
    "Recomenda-se revisão manual da decisão com base nas premissas e riscos declarados. "
    "Acione o Mentor novamente quando o serviço de análise estiver disponível."
)


class FallbackHandler:
    """Gera resposta determinística quando o LLM está indisponível."""

    @staticmethod
    async def handle(
        ctx: PromptContext,
        session: AsyncSession,
        error: Optional[Exception] = None,
    ) -> LLMAnalysisResult:
        """Retorna LLMAnalysisResult de fallback e grava audit log.

        Args:
            ctx: Contexto do caso para extrair framework e case_id.
            session: Sessão SQLAlchemy para gravar o audit log.
            error: Exceção que motivou o fallback (incluída no payload de auditoria).

        Returns:
            LLMAnalysisResult com llm_unavailable=True.
        """
        AuditLogger.log(
            session=session,
            action=AuditAction.LLM_FALLBACK,
            decision_case_id=ctx.case_id,
            payload={
                "framework": ctx.framework_selected.value,
                "error": str(error) if error else "unknown",
            },
        )

        metrics = _FRAMEWORK_DEFAULT_METRICS.get(ctx.framework_selected, [])

        recommendation = _FALLBACK_RECOMMENDATION
        if ctx.heuristics_context:
            recommendation += (
                f"\n\nContexto histórico: {len(ctx.heuristics_context)} "
                "heurística(s) organizacional(is) ativa(s) foram consideradas."
            )

        return LLMAnalysisResult(
            recommendation=recommendation,
            financial_metrics_impacted=metrics,
            scenario_summary=None,
            implicit_assumptions_found=[],
            game_theory_model=None,
            llm_unavailable=True,
        )
