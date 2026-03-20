"""
Heuristics Service — P-10 Learning Module

Registra e recupera heurísticas financeiras aprendidas de casos históricos.

Princípios (Fase 6):
  - Heurísticas são INSERT/UPDATE only — nunca DELETE (apenas deactivate)
  - Criação automática via generate_from_review() no fechamento do caso
  - Criação manual pelo Arquiteto continua disponível
  - Listagem filtra por active=True por padrão
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_logger import AuditAction, AuditLogger
from app.core.exceptions import HeuristicNotFoundError
from app.models.enums import DecisionState, DecisionType, FinancialDomain
from app.models.financial_decision_case import Decision, FinancialDecisionCase, FinancialHeuristic, Review

if TYPE_CHECKING:
    from app.llm.cache import LLMCache
    from app.llm.service import LLMService
    from app.schemas import LearningSummaryResponse

_SUMMARY_KEY_PREFIX = "llm:learning_summary:"


_DOMAIN_LABELS = {
    "planning": "Planejamento", "reporting": "Relatórios",
    "treasury": "Tesouraria", "funding": "Captação", "risk": "Risco",
}

_TYPE_LABELS = {
    "budget_adjustment": "Ajuste de Orçamento", "forecast_revision": "Revisão de Forecast",
    "capital_allocation": "Alocação de Capital", "debt_structuring": "Estruturação de Dívida",
    "liquidity_management": "Gestão de Liquidez", "risk_hedging": "Hedge de Risco",
    "cost_reduction": "Redução de Custos", "investment_evaluation": "Avaliação de Investimento",
}

_HEURISTIC_TYPE_LABELS = {
    "high_accuracy": "Alta acurácia de forecast",
    "divergence_risk": "Risco de divergência",
    "divergence_success": "Divergência bem-sucedida",
    "high_risk_materialization": "Alta materialização de riscos",
    "capital_efficient": "Eficiência de capital",
}


def _format_heuristic_for_prompt(h: "FinancialHeuristic") -> str:
    """Formata uma heurística como texto legível para injeção no prompt LLM (max 300 chars)."""
    val = h.heuristic_value or {}
    htype = val.get("type", h.heuristic_key)
    label = _HEURISTIC_TYPE_LABELS.get(htype, htype)
    domain = _DOMAIN_LABELS.get(h.financial_domain.value, h.financial_domain.value) if h.financial_domain else "?"
    dt = h.decision_type.value if h.decision_type else "?"
    fw = val.get("framework", "?")
    confidence = val.get("confidence", "?")

    parts = [f"[{label}]"]
    parts.append(f"Domínio: {domain}, Tipo: {dt}, Framework: {fw}")
    parts.append(f"Confiança: {confidence}")

    # Add specific metric if available
    if "forecast_accuracy_score" in val:
        parts.append(f"Acurácia: {val['forecast_accuracy_score']}/10")
    if "risk_realization_rate" in val:
        parts.append(f"Realização de riscos: {val['risk_realization_rate']}%")
    if "capital_allocation_efficiency_score" in val:
        parts.append(f"Eficiência: {val['capital_allocation_efficiency_score']}%")

    text = " | ".join(parts)
    return text[:300]


class HeuristicsService:
    """Serviço de registro de heurísticas — sem estado (métodos estáticos)."""

    @staticmethod
    async def query_all_for_analysis(session: AsyncSession) -> list[str]:
        """Busca TODAS as heurísticas ativas (max 20) e formata para injeção no prompt LLM.

        Returns:
            Lista de strings formatadas, uma por heurística.
        """
        stmt = (
            select(FinancialHeuristic)
            .where(FinancialHeuristic.active.is_(True))
            .order_by(FinancialHeuristic.created_at.desc())
            .limit(20)
        )
        result = await session.execute(stmt)
        heuristics = result.scalars().all()
        return [_format_heuristic_for_prompt(h) for h in heuristics]

    @staticmethod
    async def create_heuristic(
        session: AsyncSession,
        decision_type: DecisionType,
        financial_domain: FinancialDomain,
        heuristic_key: str,
        heuristic_value: dict,
        source_case_id: Optional[UUID] = None,
    ) -> FinancialHeuristic:
        """Cria uma nova heurística financeira.

        Args:
            session: Sessão SQLAlchemy ativa.
            decision_type: Tipo de decisão à qual a heurística se aplica.
            financial_domain: Domínio financeiro da heurística.
            heuristic_key: Chave identificadora (ex: 'bilateral_negotiation_preferred').
            heuristic_value: Payload JSONB com padrão aprendido.
            source_case_id: ID do caso que originou a heurística (opcional).

        Returns:
            Instância FinancialHeuristic persistida.
        """
        heuristic = FinancialHeuristic(
            decision_type=decision_type,
            financial_domain=financial_domain,
            heuristic_key=heuristic_key,
            heuristic_value=heuristic_value,
            source_case_id=source_case_id,
            active=True,
        )
        session.add(heuristic)
        return heuristic

    @staticmethod
    async def generate_from_review(
        session: AsyncSession,
        case: FinancialDecisionCase,
        forecast_accuracy_score: Optional[int],
        risk_realization_rate: Optional[float],
        capital_allocation_efficiency_score: Optional[float],
        divergence_outcome: bool,
    ) -> list[FinancialHeuristic]:
        """Gera heurísticas automaticamente a partir dos dados do review.

        Aplica 5 regras determinísticas em sequência. Regras 2 e 3 são
        mutuamente exclusivas. Máximo prático: 3-4 heurísticas por caso.

        Args:
            session: Sessão SQLAlchemy ativa.
            case: Caso decisório sendo fechado.
            forecast_accuracy_score: Score de acurácia do forecast (1-10).
            risk_realization_rate: Percentual de riscos materializados (0-100).
            capital_allocation_efficiency_score: Score de eficiência (0-100).
            divergence_outcome: True se divergência resultou em pior outcome.

        Returns:
            Lista de FinancialHeuristic criadas (pode ser vazia).
        """
        generated: list[FinancialHeuristic] = []
        dt = case.decision_type
        domain = case.financial_domain
        framework = case.framework_selected

        # Rule 1: Alta acurácia — forecast_accuracy_score >= 8
        if forecast_accuracy_score is not None and forecast_accuracy_score >= 8:
            fw_key = framework.value if framework else "unknown"
            h = await HeuristicsService.create_heuristic(
                session,
                decision_type=dt,
                financial_domain=domain,
                heuristic_key=f"high_accuracy_{fw_key}_{dt.value}",
                heuristic_value={
                    "type": "high_accuracy",
                    "decision_type": dt.value,
                    "financial_domain": domain.value,
                    "framework": fw_key,
                    "forecast_accuracy_score": forecast_accuracy_score,
                    "confidence": round(forecast_accuracy_score / 10, 2),
                },
                source_case_id=case.id,
            )
            generated.append(h)

        # Check if there was a divergence (Decision.divergence_flag=True)
        result = await session.execute(
            select(Decision)
            .where(Decision.decision_case_id == case.id)
            .where(Decision.divergence_flag.is_(True))
        )
        had_divergence = result.scalar_one_or_none() is not None

        # Rules 2 and 3 are mutually exclusive
        if divergence_outcome:
            # Rule 2: Divergência negativa — divergence_outcome == True
            h = await HeuristicsService.create_heuristic(
                session,
                decision_type=dt,
                financial_domain=domain,
                heuristic_key=f"divergence_risk_{dt.value}_{domain.value}",
                heuristic_value={
                    "type": "divergence_risk",
                    "decision_type": dt.value,
                    "financial_domain": domain.value,
                    "framework": framework.value if framework else "unknown",
                    "divergence_outcome": True,
                    "confidence": 0.8,
                },
                source_case_id=case.id,
            )
            generated.append(h)
        elif (
            had_divergence
            and forecast_accuracy_score is not None
            and forecast_accuracy_score >= 7
            and not divergence_outcome
        ):
            # Rule 3: Divergência bem-sucedida
            h = await HeuristicsService.create_heuristic(
                session,
                decision_type=dt,
                financial_domain=domain,
                heuristic_key=f"divergence_success_{dt.value}_{domain.value}",
                heuristic_value={
                    "type": "divergence_success",
                    "decision_type": dt.value,
                    "financial_domain": domain.value,
                    "framework": framework.value if framework else "unknown",
                    "forecast_accuracy_score": forecast_accuracy_score,
                    "confidence": round(forecast_accuracy_score / 10, 2),
                },
                source_case_id=case.id,
            )
            generated.append(h)

        # Rule 4: Materialização de riscos — risk_realization_rate > 50
        if risk_realization_rate is not None and risk_realization_rate > 50:
            h = await HeuristicsService.create_heuristic(
                session,
                decision_type=dt,
                financial_domain=domain,
                heuristic_key=f"high_risk_materialization_{dt.value}_{domain.value}",
                heuristic_value={
                    "type": "high_risk_materialization",
                    "decision_type": dt.value,
                    "financial_domain": domain.value,
                    "framework": framework.value if framework else "unknown",
                    "risk_realization_rate": float(risk_realization_rate),
                    "confidence": round(min(risk_realization_rate / 100, 1.0), 2),
                },
                source_case_id=case.id,
            )
            generated.append(h)

        # Rule 5: Eficiência de capital — capital_allocation_efficiency_score >= 80
        if (
            capital_allocation_efficiency_score is not None
            and capital_allocation_efficiency_score >= 80
        ):
            h = await HeuristicsService.create_heuristic(
                session,
                decision_type=dt,
                financial_domain=domain,
                heuristic_key=f"capital_efficient_{dt.value}_{domain.value}",
                heuristic_value={
                    "type": "capital_efficient",
                    "decision_type": dt.value,
                    "financial_domain": domain.value,
                    "framework": framework.value if framework else "unknown",
                    "capital_allocation_efficiency_score": float(
                        capital_allocation_efficiency_score
                    ),
                    "confidence": round(
                        capital_allocation_efficiency_score / 100, 2
                    ),
                },
                source_case_id=case.id,
            )
            generated.append(h)

        # Audit log if any heuristics were generated
        if generated:
            AuditLogger.log(
                session=session,
                action=AuditAction.HEURISTIC_GENERATED,
                decision_case_id=case.id,
                payload={
                    "count": len(generated),
                    "keys": [h.heuristic_key for h in generated],
                },
            )

        return generated

    @staticmethod
    async def list_heuristics(
        session: AsyncSession,
        decision_type: Optional[DecisionType] = None,
        financial_domain: Optional[FinancialDomain] = None,
    ) -> list[FinancialHeuristic]:
        """Lista heurísticas ativas, com filtros opcionais.

        Args:
            session: Sessão SQLAlchemy ativa.
            decision_type: Filtra por tipo de decisão (opcional).
            financial_domain: Filtra por domínio financeiro (opcional).

        Returns:
            Lista de FinancialHeuristic ativas, ordenadas pela mais recente.
        """
        stmt = (
            select(FinancialHeuristic)
            .where(FinancialHeuristic.active.is_(True))
            .order_by(FinancialHeuristic.created_at.desc())
        )
        if decision_type is not None:
            stmt = stmt.where(FinancialHeuristic.decision_type == decision_type)
        if financial_domain is not None:
            stmt = stmt.where(FinancialHeuristic.financial_domain == financial_domain)

        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def deactivate_heuristic(
        session: AsyncSession,
        heuristic_id: UUID,
    ) -> FinancialHeuristic:
        """Desativa uma heurística (active=False). Nunca deleta.

        Args:
            session: Sessão SQLAlchemy ativa.
            heuristic_id: UUID da heurística a desativar.

        Returns:
            Heurística atualizada com active=False.

        Raises:
            HeuristicNotFoundError: Se a heurística não existir.
        """
        result = await session.execute(
            select(FinancialHeuristic).where(FinancialHeuristic.id == heuristic_id)
        )
        heuristic = result.scalar_one_or_none()
        if heuristic is None:
            raise HeuristicNotFoundError()

        heuristic.active = False
        return heuristic

    @staticmethod
    async def generate_alerts_for_case(
        session: AsyncSession,
        case: FinancialDecisionCase,
    ) -> list[dict]:
        """Gera alertas proativos baseados em heurísticas com mesmo decision_type OU financial_domain.

        Returns:
            Lista de dicts compatíveis com HeuristicAlertItem.
        """
        from sqlalchemy import or_

        stmt = (
            select(FinancialHeuristic)
            .where(FinancialHeuristic.active.is_(True))
            .where(
                or_(
                    FinancialHeuristic.decision_type == case.decision_type,
                    FinancialHeuristic.financial_domain == case.financial_domain,
                )
            )
            .order_by(FinancialHeuristic.created_at.desc())
            .limit(50)
        )
        result = await session.execute(stmt)
        heuristics = result.scalars().all()

        if not heuristics:
            return []

        # Group by type
        groups: dict[str, list[FinancialHeuristic]] = defaultdict(list)
        for h in heuristics:
            htype = (h.heuristic_value or {}).get("type", h.heuristic_key)
            groups[htype].append(h)

        alerts: list[dict] = []
        dt_label = _TYPE_LABELS.get(case.decision_type.value, case.decision_type.value)
        domain_label = _DOMAIN_LABELS.get(case.financial_domain.value, case.financial_domain.value)

        if "divergence_risk" in groups:
            items = groups["divergence_risk"]
            avg_conf = sum((h.heuristic_value or {}).get("confidence", 0.5) for h in items) / len(items)
            alerts.append({
                "alert_type": "divergence_risk",
                "severity": "high",
                "message": f"Em casos similares de {dt_label}, divergências resultaram em pior outcome (conf. {avg_conf:.0%})",
                "confidence": round(avg_conf, 2),
                "source_heuristic_ids": [str(h.id) for h in items],
            })

        if "high_risk_materialization" in groups:
            items = groups["high_risk_materialization"]
            avg_rate = sum((h.heuristic_value or {}).get("risk_realization_rate", 50) for h in items) / len(items)
            alerts.append({
                "alert_type": "high_risk_materialization",
                "severity": "high",
                "message": f"Alta materialização de riscos ({avg_rate:.0f}%) em casos de {domain_label} anteriores",
                "confidence": round(min(avg_rate / 100, 1.0), 2),
                "source_heuristic_ids": [str(h.id) for h in items],
            })

        if "capital_efficient" in groups:
            items = groups["capital_efficient"]
            avg_eff = sum((h.heuristic_value or {}).get("capital_allocation_efficiency_score", 80) for h in items) / len(items)
            alerts.append({
                "alert_type": "capital_efficient",
                "severity": "low",
                "message": f"Decisões de {dt_label} tiveram {avg_eff:.0f}% de eficiência de capital",
                "confidence": round(avg_eff / 100, 2),
                "source_heuristic_ids": [str(h.id) for h in items],
            })

        if "divergence_success" in groups:
            items = groups["divergence_success"]
            alerts.append({
                "alert_type": "divergence_success",
                "severity": "medium",
                "message": f"Em {len(items)} caso(s) similar(es), divergência do executivo resultou em bom outcome",
                "confidence": round(sum((h.heuristic_value or {}).get("confidence", 0.5) for h in items) / len(items), 2),
                "source_heuristic_ids": [str(h.id) for h in items],
            })

        if "high_accuracy" in groups:
            items = groups["high_accuracy"]
            avg_acc = sum((h.heuristic_value or {}).get("forecast_accuracy_score", 8) for h in items) / len(items)
            fw_vals = [(h.heuristic_value or {}).get("framework", "?") for h in items]
            fw_mode = Counter(fw_vals).most_common(1)[0][0]
            alerts.append({
                "alert_type": "high_accuracy",
                "severity": "low",
                "message": f"Framework {fw_mode} teve alta acurácia ({avg_acc:.1f}/10) em casos de {dt_label}",
                "confidence": round(avg_acc / 10, 2),
                "source_heuristic_ids": [str(h.id) for h in items],
            })

        return alerts

    @staticmethod
    async def compute_benchmark(
        session: AsyncSession,
        case: FinancialDecisionCase,
    ) -> dict | None:
        """Computa benchmark comparando com casos CLOSED similares.

        Returns:
            Dict compatível com DecisionBenchmark, ou None se sem casos similares.
        """
        from sqlalchemy import or_, func as sa_func

        # Find closed cases with same decision_type OR financial_domain (excluding this case)
        stmt = (
            select(FinancialDecisionCase)
            .where(FinancialDecisionCase.state == DecisionState.CLOSED)
            .where(FinancialDecisionCase.id != case.id)
            .where(
                or_(
                    FinancialDecisionCase.decision_type == case.decision_type,
                    FinancialDecisionCase.financial_domain == case.financial_domain,
                )
            )
        )
        result = await session.execute(stmt)
        similar_cases = result.scalars().all()

        if not similar_cases:
            return None

        case_ids = [c.id for c in similar_cases]

        # Get decisions for these cases
        dec_result = await session.execute(
            select(Decision).where(Decision.decision_case_id.in_(case_ids))
        )
        decisions = dec_result.scalars().all()

        followed = sum(1 for d in decisions if not d.divergence_flag)
        diverged = sum(1 for d in decisions if d.divergence_flag)
        total_decisions = len(decisions)

        # Get reviews for these cases
        rev_result = await session.execute(
            select(Review).where(Review.decision_case_id.in_(case_ids))
        )
        reviews = rev_result.scalars().all()

        # Compute averages from reviews
        acc_scores = [r.forecast_accuracy_score for r in reviews if r.forecast_accuracy_score is not None]
        risk_rates = [float(r.risk_realization_rate) for r in reviews if r.risk_realization_rate is not None]
        cap_scores = [float(r.capital_allocation_efficiency_score) for r in reviews if r.capital_allocation_efficiency_score is not None]

        # Divergence success: reviews where divergence_outcome_flag=False AND decision had divergence
        diverged_case_ids = {d.decision_case_id for d in decisions if d.divergence_flag}
        diverged_reviews = [r for r in reviews if r.decision_case_id in diverged_case_ids]
        diverged_success = sum(1 for r in diverged_reviews if not r.divergence_outcome_flag)

        # Most effective framework
        fw_counter = Counter(c.framework_selected.value for c in similar_cases if c.framework_selected)
        most_effective = fw_counter.most_common(1)[0][0] if fw_counter else None

        messages: list[str] = []
        total = len(similar_cases)

        if total_decisions > 0:
            messages.append(
                f"Em {total} caso(s) similar(es), {followed} ({followed * 100 // total_decisions}%) "
                "seguiram a recomendação do Mentor"
            )

        if diverged > 0 and diverged_reviews:
            rate = diverged_success * 100 // len(diverged_reviews) if diverged_reviews else 0
            messages.append(
                f"Taxa de acerto quando divergiu: {rate}% ({diverged_success} de {len(diverged_reviews)} divergência(s))"
            )

        if acc_scores:
            avg_acc = sum(acc_scores) / len(acc_scores)
            messages.append(f"Acurácia média de forecast: {avg_acc:.1f}/10")

        if cap_scores:
            avg_cap = sum(cap_scores) / len(cap_scores)
            messages.append(f"Eficiência média de capital: {avg_cap:.1f}%")

        return {
            "total_similar_cases": total,
            "followed_recommendation_count": followed,
            "followed_recommendation_pct": round(followed * 100 / total_decisions, 1) if total_decisions else None,
            "diverged_count": diverged,
            "diverged_success_rate": round(diverged_success * 100 / len(diverged_reviews), 1) if diverged_reviews else None,
            "avg_forecast_accuracy": round(sum(acc_scores) / len(acc_scores), 1) if acc_scores else None,
            "avg_risk_realization": round(sum(risk_rates) / len(risk_rates), 1) if risk_rates else None,
            "avg_capital_efficiency": round(sum(cap_scores) / len(cap_scores), 1) if cap_scores else None,
            "most_effective_framework": most_effective,
            "messages": messages,
        }

    @staticmethod
    async def build_learning_summary(
        session: AsyncSession,
        llm_service: "LLMService",
        cache: "LLMCache",
    ) -> "LearningSummaryResponse":
        """Gera resumo executivo consolidado dos aprendizados.

        Fluxo:
          1. Busca heurísticas ativas
          2. Se 0 → retorna summary vazio
          3. Verifica cache Redis
          4. Se miss → chama LLM ou gera fallback determinístico
          5. Cacheia resultado (TTL 24h)
        """
        from app.schemas import FrameworkUsageItem, LearningSummaryResponse

        _FRAMEWORK_LABELS = {
            "pdca": "PDCA", "scenario_analysis": "Análise de Cenários",
            "game_theory": "Teoria dos Jogos", "trade_off": "Trade-Off",
            "risk_matrix": "Matriz de Riscos", "capital_allocation": "Alocação de Capital",
            "decision_matrix": "Matriz de Decisão", "cost_benefit_analysis": "Análise Custo-Benefício",
            "decision_tree": "Árvore de Decisão", "swot_analysis": "Análise SWOT",
            "delphi_method": "Método Delphi",
        }

        heuristics = await HeuristicsService.list_heuristics(session)
        if not heuristics:
            return LearningSummaryResponse(
                summary="",
                heuristics_count=0,
                llm_generated=False,
            )

        # Serializar para cache key + prompt
        heuristics_data = [
            {
                "type": (h.heuristic_value or {}).get("type", h.heuristic_key),
                "domain": h.financial_domain.value if h.financial_domain else "unknown",
                "decision_type": h.decision_type.value if h.decision_type else "unknown",
                "framework": (h.heuristic_value or {}).get("framework", "unknown"),
                "confidence": (h.heuristic_value or {}).get("confidence"),
            }
            for h in heuristics
        ]

        # Contar frameworks mais aplicados
        fw_counter = Counter(
            item["framework"] for item in heuristics_data
            if item["framework"] != "unknown"
        )
        top_frameworks = [
            FrameworkUsageItem(
                framework=_FRAMEWORK_LABELS.get(fw, fw),
                count=count,
            )
            for fw, count in fw_counter.most_common()
        ]

        # Cache key baseada no hash das heurísticas ativas
        canonical = json.dumps(heuristics_data, sort_keys=True, ensure_ascii=True)
        digest = hashlib.sha256(canonical.encode()).hexdigest()
        cache_key = f"{_SUMMARY_KEY_PREFIX}{digest}"

        # Verificar cache
        try:
            redis = await cache._get_redis()
            cached = await redis.get(cache_key)
            if cached is not None:
                data = json.loads(cached)
                return LearningSummaryResponse(**data)
        except Exception:
            pass  # cache miss silencioso

        # Chamar LLM
        now = datetime.now(timezone.utc).isoformat()
        llm_summary = await llm_service.generate_learning_summary(heuristics_data)

        if llm_summary:
            result = LearningSummaryResponse(
                summary=llm_summary,
                heuristics_count=len(heuristics),
                top_frameworks=top_frameworks,
                last_updated=now,
                llm_generated=True,
            )
        else:
            # Fallback determinístico: agrupar por tipo
            groups: dict[str, list[dict]] = defaultdict(list)
            for item in heuristics_data:
                groups[item["type"]].append(item)

            _FALLBACK_LABELS = {
                "high_accuracy": "Alta acurácia de forecast",
                "divergence_risk": "Risco de divergência",
                "divergence_success": "Divergência bem-sucedida",
                "high_risk_materialization": "Alta materialização de riscos",
                "capital_efficient": "Eficiência de capital",
            }

            _DOMAIN_LABELS = {
                "planning": "Planejamento", "reporting": "Relatórios",
                "treasury": "Tesouraria", "funding": "Captação", "risk": "Risco",
            }

            bullets: list[str] = []
            for htype, items in sorted(groups.items()):
                label = _FALLBACK_LABELS.get(htype, htype)
                domains = ", ".join(sorted({_DOMAIN_LABELS.get(i["domain"], i["domain"]) for i in items}))
                bullets.append(f"• {label}: {len(items)} padrão(ões) (domínios: {domains})")

            result = LearningSummaryResponse(
                summary="\n".join(bullets),
                heuristics_count=len(heuristics),
                top_frameworks=top_frameworks,
                last_updated=now,
                llm_generated=False,
            )

        # Cachear resultado (TTL 24h)
        try:
            redis = await cache._get_redis()
            await redis.setex(cache_key, 86400, result.model_dump_json())
        except Exception:
            pass  # cache write silencioso

        return result

    @staticmethod
    async def _invalidate_learning_summary_cache(cache: "LLMCache") -> None:
        """Deleta todas as chaves de cache de learning summary."""
        try:
            redis = await cache._get_redis()
            keys = []
            async for key in redis.scan_iter(f"{_SUMMARY_KEY_PREFIX}*"):
                keys.append(key)
            if keys:
                await redis.delete(*keys)
        except Exception:
            pass  # falha silenciosa
