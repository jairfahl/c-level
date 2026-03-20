"""
Intelligence Service — Decision Intelligence Dashboard

Aggregates KPIs from closed cases, reviews, decisions, and heuristics
for the executive dashboard.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import DecisionState
from app.models.financial_decision_case import (
    Decision,
    FinancialDecisionCase,
    FinancialHeuristic,
    Review,
)

_DOMAIN_LABELS = {
    "planning": "Planejamento",
    "reporting": "Relatórios",
    "treasury": "Tesouraria",
    "funding": "Captação",
    "risk": "Risco",
}

_FRAMEWORK_LABELS = {
    "pdca": "PDCA",
    "scenario_analysis": "Análise de Cenários",
    "game_theory": "Teoria dos Jogos",
    "trade_off": "Trade-Off",
    "risk_matrix": "Matriz de Riscos",
    "capital_allocation": "Alocação de Capital",
    "decision_matrix": "Matriz de Decisão",
    "cost_benefit_analysis": "Análise Custo-Benefício",
    "decision_tree": "Árvore de Decisão",
    "swot_analysis": "Análise SWOT",
    "delphi_method": "Método Delphi",
}


class IntelligenceService:
    """Serviço de agregação para dashboard de inteligência decisória."""

    @staticmethod
    async def get_dashboard_data(session: AsyncSession) -> dict[str, Any]:
        """Agrega KPIs de casos fechados, reviews, decisions e heurísticas.

        Returns:
            Dict compatível com DecisionIntelligenceResponse.
        """
        # Count cases by state
        closed_count = await session.scalar(
            select(func.count(FinancialDecisionCase.id))
            .where(FinancialDecisionCase.state == DecisionState.CLOSED)
        ) or 0

        active_count = await session.scalar(
            select(func.count(FinancialDecisionCase.id))
            .where(FinancialDecisionCase.state != DecisionState.CLOSED)
        ) or 0

        # Review aggregates (from closed cases)
        review_stats = (await session.execute(
            select(
                func.avg(Review.forecast_accuracy_score),
                func.avg(Review.risk_realization_rate),
                func.avg(Review.capital_allocation_efficiency_score),
            )
        )).one()

        avg_forecast = round(float(review_stats[0]), 1) if review_stats[0] is not None else None
        avg_risk = round(float(review_stats[1]), 1) if review_stats[1] is not None else None
        avg_capital = round(float(review_stats[2]), 1) if review_stats[2] is not None else None

        # Divergence stats
        divergence_total = await session.scalar(
            select(func.count(Decision.id))
            .where(Decision.divergence_flag.is_(True))
        ) or 0

        divergence_success_count = await session.scalar(
            select(func.count(Review.id))
            .where(Review.divergence_outcome_flag.is_(False))
            .where(
                Review.decision_case_id.in_(
                    select(Decision.decision_case_id)
                    .where(Decision.divergence_flag.is_(True))
                )
            )
        ) or 0

        divergence_success_rate = (
            round(divergence_success_count * 100 / divergence_total, 1)
            if divergence_total > 0 else None
        )

        # Heuristics count
        heuristics_active = await session.scalar(
            select(func.count(FinancialHeuristic.id))
            .where(FinancialHeuristic.active.is_(True))
        ) or 0

        # Domain performance
        domain_rows = (await session.execute(
            select(
                FinancialDecisionCase.financial_domain,
                func.count(FinancialDecisionCase.id).label("cnt"),
            )
            .where(FinancialDecisionCase.state == DecisionState.CLOSED)
            .group_by(FinancialDecisionCase.financial_domain)
        )).all()

        domain_performance = []
        for row in domain_rows:
            domain_val = row[0].value if hasattr(row[0], "value") else str(row[0])
            # Get review stats for this domain
            domain_review = (await session.execute(
                select(
                    func.avg(Review.forecast_accuracy_score),
                    func.avg(Review.risk_realization_rate),
                    func.avg(Review.capital_allocation_efficiency_score),
                ).where(
                    Review.decision_case_id.in_(
                        select(FinancialDecisionCase.id)
                        .where(FinancialDecisionCase.financial_domain == row[0])
                        .where(FinancialDecisionCase.state == DecisionState.CLOSED)
                    )
                )
            )).one()

            # Divergence rate for domain
            domain_decisions = await session.scalar(
                select(func.count(Decision.id)).where(
                    Decision.decision_case_id.in_(
                        select(FinancialDecisionCase.id)
                        .where(FinancialDecisionCase.financial_domain == row[0])
                        .where(FinancialDecisionCase.state == DecisionState.CLOSED)
                    )
                )
            ) or 0
            domain_divergences = await session.scalar(
                select(func.count(Decision.id))
                .where(Decision.divergence_flag.is_(True))
                .where(
                    Decision.decision_case_id.in_(
                        select(FinancialDecisionCase.id)
                        .where(FinancialDecisionCase.financial_domain == row[0])
                        .where(FinancialDecisionCase.state == DecisionState.CLOSED)
                    )
                )
            ) or 0

            domain_performance.append({
                "domain": domain_val,
                "domain_label": _DOMAIN_LABELS.get(domain_val, domain_val),
                "cases_count": row[1],
                "avg_forecast_accuracy": round(float(domain_review[0]), 1) if domain_review[0] is not None else None,
                "avg_risk_realization": round(float(domain_review[1]), 1) if domain_review[1] is not None else None,
                "avg_capital_efficiency": round(float(domain_review[2]), 1) if domain_review[2] is not None else None,
                "divergence_rate": round(domain_divergences * 100 / domain_decisions, 1) if domain_decisions > 0 else None,
            })

        # Top frameworks from heuristics
        fw_rows = (await session.execute(
            select(FinancialHeuristic.heuristic_value)
            .where(FinancialHeuristic.active.is_(True))
        )).all()

        fw_counter: Counter = Counter()
        for row in fw_rows:
            val = row[0] if row[0] else {}
            fw = val.get("framework")
            if fw and fw != "unknown":
                fw_counter[fw] += 1

        top_frameworks = [
            {"framework": _FRAMEWORK_LABELS.get(fw, fw), "count": count}
            for fw, count in fw_counter.most_common()
        ]

        return {
            "total_cases_closed": closed_count,
            "total_cases_active": active_count,
            "avg_forecast_accuracy": avg_forecast,
            "divergence_total": divergence_total,
            "divergence_success_count": divergence_success_count,
            "divergence_success_rate": divergence_success_rate,
            "avg_risk_realization": avg_risk,
            "avg_capital_efficiency": avg_capital,
            "total_heuristics_active": heuristics_active,
            "domain_performance": domain_performance,
            "top_frameworks": top_frameworks,
        }
