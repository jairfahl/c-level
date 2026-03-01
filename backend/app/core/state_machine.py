"""
State Machine Controller — CFO Mentor Engine

Impõe as transições de estado do protocolo decisório financeiro.
Qualquer tentativa de transição inválida levanta InvalidStateTransitionError (→ HTTP 409).

Tabela de transições válidas (alinhada ao OpenAPI v2):
  DRAFT           → CLASSIFIED      (PUT /classify)
  CLASSIFIED      → STRUCTURED      (PUT /structure)
  STRUCTURED      → ANALYZED        (PUT /analyze — fase 1)
  ANALYZED        → RECOMMENDED     (PUT /analyze — fase 2, automático)
  RECOMMENDED     → DECIDED         (PUT /decide)
  DECIDED         → UNDER_REVIEW    (job automático após 90 dias)
  UNDER_REVIEW    → CLOSED          (PUT /review)
  CLOSED          → (nenhum)        estado terminal
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_logger import AuditAction, AuditLogger
from app.core.exceptions import InvalidStateTransitionError
from app.models.enums import DecisionState
from app.models.financial_decision_case import FinancialDecisionCase, StateTransition

# ---------------------------------------------------------------------------
# Mapa de transições válidas
# Chave: estado atual | Valor: conjunto de estados de destino permitidos
# ---------------------------------------------------------------------------
VALID_TRANSITIONS: dict[DecisionState, frozenset[DecisionState]] = {
    DecisionState.DRAFT:        frozenset({DecisionState.CLASSIFIED}),
    DecisionState.CLASSIFIED:   frozenset({DecisionState.STRUCTURED}),
    DecisionState.STRUCTURED:   frozenset({DecisionState.ANALYZED}),
    DecisionState.ANALYZED:     frozenset({DecisionState.RECOMMENDED}),
    DecisionState.RECOMMENDED:  frozenset({DecisionState.DECIDED}),
    DecisionState.DECIDED:      frozenset({DecisionState.UNDER_REVIEW}),
    DecisionState.UNDER_REVIEW: frozenset({DecisionState.CLOSED}),
    DecisionState.CLOSED:       frozenset(),  # estado terminal — nenhuma transição válida
}


class StateMachineController:
    """Controla e valida transições de estado do ciclo decisório.

    Responsabilidades:
    - Validar que a transição solicitada é permitida.
    - Persistir o registro em `state_transitions`.
    - Atualizar `case.state` na instância ORM (sem flush imediato).
    - Delegar o log de auditoria ao AuditLogger.

    O caller (service layer) é responsável pelo commit da sessão.
    """

    async def transition(
        self,
        case: FinancialDecisionCase,
        to_state: DecisionState,
        session: AsyncSession,
        triggered_by: Optional[str] = None,
    ) -> StateTransition:
        """Executa e registra uma transição de estado.

        Args:
            case: Caso decisório a ser transicionado (instância ORM carregada).
            to_state: Estado de destino desejado.
            session: Sessão SQLAlchemy ativa.
            triggered_by: Identificador do ator que acionou a transição
                          (ex: "user:uuid", "scheduler:auto_review").

        Returns:
            A instância StateTransition criada e adicionada à sessão.

        Raises:
            InvalidStateTransitionError: Se `to_state` não é permitido a partir
                                         do estado atual do caso (HTTP 409).
        """
        from_state = case.state
        allowed = VALID_TRANSITIONS.get(from_state, frozenset())

        if to_state not in allowed:
            raise InvalidStateTransitionError(from_state.value, to_state.value)

        # 1. Persiste o registro histórico da transição
        transition = StateTransition(
            decision_case_id=case.id,
            from_state=from_state,
            to_state=to_state,
            triggered_by=triggered_by,
        )
        session.add(transition)

        # 2. Atualiza o estado na instância ORM (persistido no próximo commit)
        case.state = to_state

        # 3. Grava no audit_log
        AuditLogger.log(
            session=session,
            action=AuditAction.STATE_TRANSITION,
            decision_case_id=case.id,
            payload={
                "from_state": from_state.value,
                "to_state": to_state.value,
                "triggered_by": triggered_by,
            },
        )

        return transition
