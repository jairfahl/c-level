"""
Audit Logger — CFO Mentor Engine

Responsável por persistir todas as ações relevantes em audit_logs.
session.add() é síncrono em SQLAlchemy async — apenas commit/flush são async.

Ações definidas em AuditAction devem ser os únicos valores usados como `action`
para garantir rastreabilidade consistente.
"""
from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financial_decision_case import AuditLog


class AuditAction:
    """Constantes para os valores do campo `action` em audit_logs."""

    CASE_CREATED = "CASE_CREATED"
    STATE_TRANSITION = "STATE_TRANSITION"
    LLM_CALLED = "LLM_CALLED"
    LLM_FALLBACK = "LLM_FALLBACK"
    DIVERGENCE_RECORDED = "DIVERGENCE_RECORDED"
    HEURISTIC_GENERATED = "HEURISTIC_GENERATED"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    DOCUMENT_DELETED = "DOCUMENT_DELETED"


class AuditLogger:
    """Grava registros de auditoria na tabela audit_logs via session.add()."""

    @staticmethod
    def log(
        session: AsyncSession,
        action: str,
        decision_case_id: Optional[UUID] = None,
        payload: Optional[dict[str, Any]] = None,
    ) -> AuditLog:
        """Insere um AuditLog na sessão corrente.

        A persistência efetiva ocorre no próximo commit (gerenciado pelo
        middleware de sessão em app/core/database.py).

        Args:
            session: Sessão SQLAlchemy ativa.
            action: Código da ação — use as constantes de AuditAction.
            decision_case_id: UUID do caso associado (opcional para logs globais).
            payload: Metadados estruturados da ação (armazenados como JSONB).

        Returns:
            A instância AuditLog adicionada à sessão.
        """
        audit = AuditLog(
            decision_case_id=decision_case_id,
            action=action,
            payload=payload,
        )
        session.add(audit)
        return audit
