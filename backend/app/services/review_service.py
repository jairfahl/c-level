"""
Review Service — P-10 Learning Module

Lógica de pós-decisão chamada durante o fechamento do review (CLOSED):
  1. compute_divergence_outcome  — calcula divergence_outcome_flag automaticamente
  2. update_risk_materialization — marca financial_risks.materialized com base no
     risk_realization_rate informado pelo CFO

Regras (especificação Fase 6):
  - divergence_outcome_flag = True quando:
      * há um Decision com divergence_flag=True para o caso
      * E forecast_accuracy_score < 5 (previsão muito abaixo do realizado)
  - Materialização de riscos (MVP heurístico):
      * rate > 50 % → todos os riscos marcados como materializados
      * rate ≤ 50 % → nenhuma alteração automática
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financial_decision_case import Decision, FinancialDecisionCase, FinancialRisk


class ReviewService:
    """Serviço de revisão pós-decisão — sem estado (métodos estáticos)."""

    # ── 1. Divergence outcome calculation ─────────────────────────────────────

    @staticmethod
    async def compute_divergence_outcome(
        case: FinancialDecisionCase,
        forecast_accuracy_score: Optional[int],
        session: AsyncSession,
    ) -> bool:
        """Calcula divergence_outcome_flag automaticamente.

        Returns True quando o CFO divergiu da recomendação do Mentor (havia um
        Decision.divergence_flag=True) E a previsão foi significativamente
        imprecisa (forecast_accuracy_score < 5).

        Args:
            case: Caso decisório sendo fechado.
            forecast_accuracy_score: Score de acurácia do forecast (1–10) ou None.
            session: Sessão SQLAlchemy ativa.

        Returns:
            True se a divergência resultou em pior outcome; False caso contrário.
        """
        if forecast_accuracy_score is None or forecast_accuracy_score >= 5:
            return False

        # Check if any Decision record for this case has divergence_flag=True
        result = await session.execute(
            select(Decision)
            .where(Decision.decision_case_id == case.id)
            .where(Decision.divergence_flag.is_(True))
        )
        had_divergence = result.scalar_one_or_none() is not None
        return had_divergence

    # ── 2. Risk materialization update ────────────────────────────────────────

    @staticmethod
    async def update_risk_materialization(
        case: FinancialDecisionCase,
        risk_realization_rate: Optional[float],
        session: AsyncSession,
    ) -> int:
        """Marca financial_risks.materialized com base no risk_realization_rate.

        Heurística MVP: se mais de 50 % dos riscos se materializaram, marca todos
        como materializados (sinalização de revisão manual futura).

        Args:
            case: Caso decisório sendo fechado.
            risk_realization_rate: Percentual de riscos materializados (0–100) ou None.
            session: Sessão SQLAlchemy ativa.

        Returns:
            Número de riscos marcados como materializados (0 se regra não disparou).
        """
        if risk_realization_rate is None or risk_realization_rate <= 50.0:
            return 0

        result = await session.execute(
            select(FinancialRisk).where(FinancialRisk.decision_case_id == case.id)
        )
        risks = result.scalars().all()

        for risk in risks:
            risk.materialized = True

        return len(risks)
