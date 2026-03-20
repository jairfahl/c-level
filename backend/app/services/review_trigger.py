"""
Review Trigger — P-10 Learning Module

Identifica casos em estado DECIDED há mais de REVIEW_THRESHOLD_DAYS dias sem
que uma revisão pós-decisão tenha sido registrada.

MVP: lógica apenas — sem envio automático de notificações/email.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import DecisionState
from app.models.financial_decision_case import FinancialDecisionCase, Review

REVIEW_THRESHOLD_DAYS: int = 1


class ReviewTrigger:
    """Identifica casos que precisam de revisão pós-decisão."""

    @staticmethod
    async def get_cases_pending_review(session: AsyncSession) -> list[dict]:
        """Retorna casos DECIDED há mais de 90 dias sem review registrado.

        A query faz LEFT JOIN com a tabela reviews e filtra apenas casos cujo
        review ainda não existe (Review.id IS NULL).

        Args:
            session: Sessão SQLAlchemy ativa.

        Returns:
            Lista de dicts com metadados dos casos pendentes, ordenados pelo
            mais antigo primeiro.
        """
        threshold = datetime.now(timezone.utc) - timedelta(days=REVIEW_THRESHOLD_DAYS)
        # Convert to naive UTC for comparison with naive DB datetimes
        threshold_naive = threshold.replace(tzinfo=None)

        stmt = (
            select(FinancialDecisionCase)
            .outerjoin(Review, Review.decision_case_id == FinancialDecisionCase.id)
            .where(FinancialDecisionCase.state == DecisionState.DECIDED)
            .where(FinancialDecisionCase.updated_at < threshold_naive)
            .where(Review.id.is_(None))
            .order_by(FinancialDecisionCase.updated_at.asc())
        )

        result = await session.execute(stmt)
        cases = result.scalars().all()

        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        return [
            {
                "case_id":          str(c.id),
                "title":            c.title,
                "financial_domain": c.financial_domain.value,
                "decision_type":    c.decision_type.value,
                "financial_exposure": float(c.financial_exposure),
                "decided_at":       c.updated_at.isoformat(),
                "days_pending":     (now_naive - c.updated_at).days,
            }
            for c in cases
        ]
