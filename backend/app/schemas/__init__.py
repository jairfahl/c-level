"""
Pydantic v2 schemas — CFO Mentor API (OpenAPI v2)

Convenções:
- Request schemas: campos readOnly ausentes (id, state, framework_selected, scenario_required, *_at)
- Response schemas: from_attributes=True onde o ORM mapeia diretamente
- Campos de resposta que requerem join/agregação (financial_metrics_impacted,
  recommendation, executive_decision, divergence_flag) são populados pela camada
  de serviço — não pelo from_attributes direto.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import (
    DecisionState,
    DecisionType,
    FinancialDomain,
    FrameworkType,
    TimeHorizon,
)

__all__ = [
    # Enums (re-exportados)
    "FinancialDomain",
    "DecisionState",
    "DecisionType",
    "TimeHorizon",
    "FrameworkType",
    # Request
    "FinancialDecisionCaseCreate",
    "ClassifyRequest",
    "StructureRequest",
    "DecideRequest",
    "ReviewRequest",
    # Response — objetos aninhados
    "AssumptionResponse",
    "RiskResponse",
    "GameTheoryModel",
    "StateTransitionResponse",
    # Response — casos decisórios
    "CaseCreatedResponse",
    "FinancialDecisionCaseResponse",
    "FinancialDecisionCaseFullResponse",
    # Response — transições de estado
    "ClassifyResponse",
    "StructureResponse",
    "AnalysisResponse",
    "DecideResponse",
    "ReviewResponse",
    # Response — listagens e auditoria
    "PaginatedCasesResponse",
    "StateTransitionsListResponse",
    # Erro padronizado
    "ErrorResponse",
]


# ─────────────────────────────────────────────────────────────────────────────
#  REQUEST SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class FinancialDecisionCaseCreate(BaseModel):
    """POST /financial-decision-cases — cria novo caso decisório (estado inicial = DRAFT)."""

    title: str = Field(
        ...,
        min_length=5,
        description="Título do caso decisório",
        examples=["Reestruturação da dívida bancária de longo prazo"],
    )
    description: str = Field(
        ...,
        min_length=20,
        description="Descrição detalhada do caso",
    )
    financial_domain: FinancialDomain
    financial_exposure: float = Field(
        ...,
        ge=0.01,
        description="Exposição financeira em BRL",
        examples=[45000000.00],
    )
    time_horizon: Optional[TimeHorizon] = None
    external_agents_present: bool = Field(
        default=False,
        description="true = há contraparte externa (banco, competidor, regulador)",
    )
    decision_type: DecisionType


class ClassifyRequest(BaseModel):
    """PUT /financial-decision-cases/{id}/classify — DRAFT → CLASSIFIED."""

    impact_score: int = Field(
        ...,
        ge=1,
        le=5,
        description="1=baixo … 5=crítico",
    )


class StructureRequest(BaseModel):
    """PUT /financial-decision-cases/{id}/structure — CLASSIFIED → STRUCTURED.

    Mínimo 3 premissas e 3 riscos obrigatórios.
    """

    assumptions: list[str] = Field(
        ...,
        description="Premissas financeiras (mínimo 3)",
        examples=[
            [
                "Taxa Selic se mantém em 10,5% ao longo do horizon",
                "Receita crescerá 8% no próximo exercício",
                "Linha de crédito rotativo permanece disponível",
            ]
        ],
    )
    risks: list[str] = Field(
        ...,
        description="Riscos financeiros identificados (mínimo 3)",
        examples=[
            [
                "Reversão do ciclo de afrouxamento monetário",
                "Deterioração do rating de crédito",
                "Concentração de vencimentos em janela curta",
            ]
        ],
    )

    @field_validator("assumptions")
    @classmethod
    def validate_assumptions_count(cls, v: list[str]) -> list[str]:
        if len(v) < 3:
            raise ValueError(
                f"São necessárias no mínimo 3 premissas financeiras. Fornecidas: {len(v)}"
            )
        return v

    @field_validator("risks")
    @classmethod
    def validate_risks_count(cls, v: list[str]) -> list[str]:
        if len(v) < 3:
            raise ValueError(
                f"São necessários no mínimo 3 riscos financeiros. Fornecidos: {len(v)}"
            )
        return v


class DecideRequest(BaseModel):
    """PUT /financial-decision-cases/{id}/decide — RECOMMENDED → DECIDED."""

    executive_decision: str = Field(
        ...,
        min_length=10,
        description="Decisão executiva registrada pelo CFO",
        examples=["Optamos por renegociar apenas 60% da dívida neste momento."],
    )
    divergence_justification: Optional[str] = Field(
        default=None,
        description="Justificativa obrigatória quando a decisão diverge da recomendação do Mentor",
    )
    monitoring_criteria: Optional[list[str]] = Field(
        default=None,
        description="Critérios de monitoramento definidos pelo executivo ao divergir",
    )


class ReviewRequest(BaseModel):
    """PUT /financial-decision-cases/{id}/review — DECIDED/UNDER_REVIEW → CLOSED."""

    outcome_summary: str = Field(
        ...,
        min_length=20,
        description="Resultado real da decisão para aprendizado e calibração",
    )
    forecast_accuracy_score: Optional[int] = Field(
        default=None,
        ge=1,
        le=10,
        description="1=muito abaixo do previsto … 10=exatamente conforme previsto",
    )
    risk_realization_rate: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Percentual de riscos identificados que se concretizaram",
    )
    capital_allocation_efficiency_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )
    divergence_outcome_flag: Optional[bool] = Field(
        default=None,
        description="true = a divergência do executivo resultou em pior resultado",
    )


# ─────────────────────────────────────────────────────────────────────────────
#  RESPONSE SCHEMAS — objetos aninhados
# ─────────────────────────────────────────────────────────────────────────────

class AssumptionResponse(BaseModel):
    """Premissa financeira associada ao caso."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    text: str
    is_implicit: bool = Field(
        description="true = premissa implícita capturada pelo Mentor"
    )


class RiskResponse(BaseModel):
    """Risco financeiro associado ao caso."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    text: str
    materialized: bool = Field(
        description="Atualizado na revisão pós-decisão"
    )


class GameTheoryModel(BaseModel):
    """Modelo de teoria dos jogos — preenchido quando framework = game_theory."""

    players: list[str]
    strategies: dict[str, list[str]]
    payoffs: dict[str, str]
    equilibrium: Optional[str] = None
    strategic_risk: str


class StateTransitionResponse(BaseModel):
    """Registro de uma transição de estado na trilha de auditoria."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    from_state: Optional[DecisionState] = None
    to_state: DecisionState
    transitioned_at: datetime
    triggered_by: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
#  RESPONSE SCHEMAS — casos decisórios
# ─────────────────────────────────────────────────────────────────────────────

class CaseCreatedResponse(BaseModel):
    """Resposta do POST /financial-decision-cases (HTTP 201)."""

    id: UUID
    state: DecisionState


class FinancialDecisionCaseResponse(BaseModel):
    """Representação resumida de um caso decisório (usado na listagem paginada)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    financial_domain: FinancialDomain
    impact_score: Optional[int] = None
    financial_exposure: float
    time_horizon: Optional[TimeHorizon] = None
    external_agents_present: bool
    decision_type: DecisionType
    # readOnly — definidos pelo sistema
    framework_selected: Optional[FrameworkType] = None
    scenario_required: bool
    state: DecisionState
    created_at: datetime
    updated_at: datetime


class FinancialDecisionCaseFullResponse(FinancialDecisionCaseResponse):
    """Representação completa do caso (GET /financial-decision-cases/{id}).

    Os campos abaixo são populados pela camada de serviço via agregação:
    - financial_metrics_impacted: extraído de FinancialMetricImpacted.metric_name
    - recommendation, executive_decision, divergence_flag: extraído de Decision
    """

    assumptions: list[AssumptionResponse] = Field(default_factory=list)
    risks: list[RiskResponse] = Field(default_factory=list)
    financial_metrics_impacted: list[str] = Field(default_factory=list)
    recommendation: Optional[str] = None
    executive_decision: Optional[str] = None
    divergence_flag: Optional[bool] = None


# ─────────────────────────────────────────────────────────────────────────────
#  RESPONSE SCHEMAS — transições de estado (state machine)
# ─────────────────────────────────────────────────────────────────────────────

class ClassifyResponse(BaseModel):
    """Resposta do PUT /classify — DRAFT → CLASSIFIED."""

    state: DecisionState
    framework_selected: FrameworkType
    scenario_required: bool


class StructureResponse(BaseModel):
    """Resposta do PUT /structure — CLASSIFIED → STRUCTURED."""

    state: DecisionState
    assumptions_count: int
    risks_count: int


class AnalysisResponse(BaseModel):
    """Resposta do PUT /analyze — STRUCTURED → ANALYZED → RECOMMENDED."""

    state: DecisionState
    recommendation: str
    framework_selected: FrameworkType
    financial_metrics_impacted: list[str]
    scenario_summary: Optional[str] = Field(
        default=None,
        description="Preenchido apenas quando scenario_required = true",
    )
    implicit_assumptions_found: list[str] = Field(
        default_factory=list,
        description="Premissas implícitas detectadas pelo LLM durante a análise",
    )
    game_theory_model: Optional[GameTheoryModel] = Field(
        default=None,
        description="Preenchido apenas quando framework = game_theory",
    )
    llm_unavailable: bool = Field(
        default=False,
        description="true = LLM indisponível; análise em modo determinístico puro (fallback)",
    )


class DecideResponse(BaseModel):
    """Resposta do PUT /decide — RECOMMENDED → DECIDED."""

    state: DecisionState
    divergence_flag: bool


class ReviewResponse(BaseModel):
    """Resposta do PUT /review — DECIDED/UNDER_REVIEW → CLOSED."""

    state: DecisionState


# ─────────────────────────────────────────────────────────────────────────────
#  RESPONSE SCHEMAS — listagens e auditoria
# ─────────────────────────────────────────────────────────────────────────────

class PaginatedCasesResponse(BaseModel):
    """Resposta paginada do GET /financial-decision-cases."""

    items: list[FinancialDecisionCaseResponse]
    total: int
    page: int = Field(ge=1)
    limit: int = Field(ge=1, le=100)


class StateTransitionsListResponse(BaseModel):
    """Resposta do GET /financial-decision-cases/{id}/state-transitions."""

    decision_case_id: UUID
    transitions: list[StateTransitionResponse]


# ─────────────────────────────────────────────────────────────────────────────
#  ERRO PADRONIZADO
# ─────────────────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Envelope de erro padronizado para todos os endpoints (4xx / 5xx)."""

    error: str = Field(
        ...,
        description="Código de erro legível por máquina (ex: CASE_NOT_FOUND)",
        examples=["CASE_NOT_FOUND"],
    )
    message: str = Field(
        ...,
        description="Descrição legível por humano",
        examples=["Nenhum caso encontrado com o ID informado"],
    )
    details: Optional[dict[str, Any]] = Field(
        default=None,
        description="Metadados adicionais de diagnóstico (opcional)",
    )
