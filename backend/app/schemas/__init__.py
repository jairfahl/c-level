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
    "ClassificationSuggestionResponse",
    "ReclassifyRequest",
    "StructureRequest",
    "HypothesisRequest",
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
    "MethodSuggestionResponse",
    "MethodSelectionRequest",
    "AnalysisResponse",
    "DecideResponse",
    "ReviewResponse",
    # Response — listagens e auditoria
    "PaginatedCasesResponse",
    "StateTransitionsListResponse",
    # P-10 — Learning Module
    "HeuristicCreate",
    "HeuristicResponse",
    "HeuristicListResponse",
    "PendingReviewCaseResponse",
    "PendingReviewsResponse",
    # Learning Summary
    "FrameworkUsageItem",
    "LearningSummaryResponse",
    # Knowledge Base
    "KnowledgeDocumentUploadResponse",
    "KnowledgeDocumentResponse",
    "KnowledgeDocumentSummaryResponse",
    "KnowledgeDocumentListResponse",
    "RelevanceCheckResponse",
    # Intelligence & Alerts
    "HeuristicAlertItem",
    "DecisionBenchmark",
    "HeuristicAlertsResponse",
    "DomainPerformanceItem",
    "DecisionIntelligenceResponse",
    # Framework Catalog
    "FrameworkCatalogEntry",
    "FrameworkCatalogResponse",
    "FrameworkSuggestionDetail",
    # API Balance
    "ApiBalanceResponse",
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


class ClassificationSuggestionResponse(BaseModel):
    """Resposta do GET /suggest-classification — sugestão de reclassificação pré-análise."""

    reclassification_needed: bool
    suggested_domain: Optional[FinancialDomain] = None
    suggested_decision_type: Optional[DecisionType] = None
    confidence: float = 0.0
    reason: str = ""


class ReclassifyRequest(BaseModel):
    """Body do PUT /reclassify — reclassificação de domínio e tipo de decisão."""

    financial_domain: FinancialDomain
    decision_type: DecisionType


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


class HypothesisRequest(BaseModel):
    """PUT /financial-decision-cases/{id}/hypothesis — registra hipótese pré-recomendação."""

    initial_hypothesis: str = Field(
        ...,
        min_length=30,
        description="Hipótese inicial do CFO antes de ver a recomendação da IA (mínimo 30 caracteres)",
    )


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
    initial_hypothesis: Optional[str] = None
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


class FrameworkCatalogEntry(BaseModel):
    """Entrada do catálogo de frameworks com metadata rica."""
    framework: FrameworkType
    name: str
    description: str
    icon_label: str
    rationale: str
    complexity: str
    recommended_for: list[DecisionType]
    pairs_well_with: list[FrameworkType]


class FrameworkCatalogResponse(BaseModel):
    """Resposta do GET /framework-catalog."""
    frameworks: list[FrameworkCatalogEntry]


class FrameworkSuggestionDetail(BaseModel):
    """Sugestão de framework com metadata rica e justificativa contextual."""
    framework: FrameworkType
    name: str
    description: str
    icon_label: str
    complexity: str
    is_primary: bool
    why_suggested: str
    pairs_well_with: list[FrameworkType]
    recommended_for: list[DecisionType]


class MethodSuggestionResponse(BaseModel):
    """Resposta do GET /suggest-methods — sugestões de frameworks pré-análise."""
    primary_framework: FrameworkType = Field(
        description="Framework principal — obrigatório, não pode ser removido pelo executivo."
    )
    suggested_frameworks: list[FrameworkType] = Field(
        description="Lista sugerida pelo engine (primary first). Ponto de partida para customização."
    )
    suggestions_rationale: dict[str, str] = Field(
        description="Justificativa por framework (chave=valor do enum, valor=razão em 1 linha PT-BR)."
    )
    available_frameworks: list[FrameworkType] = Field(
        description="Todos os frameworks disponíveis para adição manual pelo executivo."
    )
    suggestion_details: list[FrameworkSuggestionDetail] = Field(
        default_factory=list,
        description="Sugestões com metadata rica e justificativa contextual por framework."
    )
    available_catalog: list[FrameworkCatalogEntry] = Field(
        default_factory=list,
        description="Catálogo completo de frameworks disponíveis com metadata rica."
    )


class MethodSelectionRequest(BaseModel):
    """Body opcional do PUT /analyze — seleção customizada de frameworks pelo executivo."""
    frameworks_selected: list[FrameworkType] = Field(
        min_length=1,
        max_length=4,
        description="Lista confirmada pelo executivo. Mín. 1 (principal), máx. 4.",
    )


class AnalysisResponse(BaseModel):
    """Resposta do PUT /analyze — STRUCTURED → ANALYZED → RECOMMENDED."""

    state: DecisionState
    recommendation: str
    framework_selected: FrameworkType = Field(
        description="Framework principal (mantido por compatibilidade — equivale a primary_framework)."
    )
    primary_framework: FrameworkType = Field(
        default=None,
        description="Framework principal aplicado (índice 0 da lista frameworks_selected).",
    )
    frameworks_selected: list[FrameworkType] = Field(
        default_factory=list,
        description="Lista completa de frameworks aplicados na análise, na ordem de aplicação.",
    )
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
    divergence_outcome_flag: bool = Field(
        default=False,
        description="true = divergência do executivo resultou em pior outcome (auto-calculado)",
    )
    heuristics_generated: int = Field(
        default=0,
        description="Número de heurísticas geradas automaticamente no fechamento",
    )


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
#  P-10 — LEARNING MODULE SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class HeuristicCreate(BaseModel):
    """POST /heuristics — cria uma heurística financeira manualmente."""

    decision_type: DecisionType
    financial_domain: FinancialDomain
    heuristic_key: str = Field(
        ...,
        min_length=3,
        description="Chave identificadora (ex: 'bilateral_negotiation_preferred')",
    )
    heuristic_value: dict[str, Any] = Field(
        ...,
        description="Payload JSONB com o padrão aprendido (trigger, always_check, etc.)",
    )
    source_case_id: Optional[UUID] = Field(
        default=None,
        description="ID do caso histórico que originou esta heurística",
    )


class HeuristicResponse(BaseModel):
    """Representação de uma heurística financeira."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    decision_type: DecisionType
    financial_domain: FinancialDomain
    heuristic_key: str
    heuristic_value: dict[str, Any]
    source_case_id: Optional[UUID] = None
    active: bool
    created_at: datetime
    updated_at: datetime


class HeuristicListResponse(BaseModel):
    """Resposta do GET /heuristics."""

    heuristics: list[HeuristicResponse]
    total: int


class FrameworkUsageItem(BaseModel):
    """Contagem de uso de um framework/método de decisão."""

    framework: str = Field(description="Nome legível do framework")
    count: int = Field(description="Quantidade de vezes aplicado")


class LearningSummaryResponse(BaseModel):
    """Resumo executivo consolidado dos aprendizados."""

    summary: str = Field(description="Texto estruturado do resumo executivo")
    heuristics_count: int = Field(description="Total de heurísticas ativas consideradas")
    top_frameworks: list[FrameworkUsageItem] = Field(
        default_factory=list,
        description="Métodos de decisão mais aplicados, ordenados por frequência",
    )
    last_updated: Optional[str] = Field(default=None, description="Timestamp da última atualização")
    llm_generated: bool = Field(default=False, description="True = gerado pelo LLM, False = fallback determinístico")


class PendingReviewCaseResponse(BaseModel):
    """Metadados de um caso pendente de revisão pós-decisão."""

    case_id: str
    title: str
    financial_domain: str
    decision_type: str
    financial_exposure: float
    decided_at: str
    days_pending: int


class PendingReviewsResponse(BaseModel):
    """Resposta do GET /admin/pending-reviews."""

    pending: list[PendingReviewCaseResponse]
    total: int
    threshold_days: int


# ─────────────────────────────────────────────────────────────────────────────
#  KNOWLEDGE BASE SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class KnowledgeDocumentUploadResponse(BaseModel):
    """Resposta do POST /knowledge-base/upload (HTTP 201) — sem extracted_text."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: Optional[str] = None
    original_filename: str
    file_type: str
    file_size_bytes: int
    text_length: int
    financial_domain: FinancialDomain
    decision_type: Optional[DecisionType] = None
    uploaded_by: Optional[str] = None
    created_at: datetime


class KnowledgeDocumentResponse(BaseModel):
    """GET /knowledge-base/{id} — com extracted_text para preview."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: Optional[str] = None
    original_filename: str
    file_type: str
    file_size_bytes: int
    extracted_text: str
    text_length: int
    financial_domain: FinancialDomain
    decision_type: Optional[DecisionType] = None
    active: bool
    uploaded_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class KnowledgeDocumentSummaryResponse(BaseModel):
    """Listagem — sem extracted_text (leve)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: Optional[str] = None
    original_filename: str
    file_type: str
    file_size_bytes: int
    text_length: int
    financial_domain: FinancialDomain
    decision_type: Optional[DecisionType] = None
    active: bool
    uploaded_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class KnowledgeDocumentListResponse(BaseModel):
    """Wrapper: documents + total."""

    documents: list[KnowledgeDocumentSummaryResponse]
    total: int


class RelevanceCheckResponse(BaseModel):
    """Resposta do POST /knowledge-base/validate-relevance — resultado da validação de relevância."""

    verdict: str = Field(description="relevant | borderline | irrelevant")
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    domain_keywords_found: list[str] = Field(default_factory=list)
    off_topic_keywords_found: list[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
#  INTELLIGENCE, ALERTS & BENCHMARK SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class HeuristicAlertItem(BaseModel):
    """Alerta proativo derivado de heurísticas históricas."""

    alert_type: str = Field(description="Tipo: divergence_risk, high_risk, capital_efficiency, etc.")
    severity: str = Field(description="low, medium, high")
    message: str = Field(description="Mensagem contextual em PT-BR")
    confidence: Optional[float] = None
    source_heuristic_ids: list[str] = Field(default_factory=list)


class DecisionBenchmark(BaseModel):
    """Comparação com casos similares encerrados."""

    total_similar_cases: int = 0
    followed_recommendation_count: int = 0
    followed_recommendation_pct: Optional[float] = None
    diverged_count: int = 0
    diverged_success_rate: Optional[float] = None
    avg_forecast_accuracy: Optional[float] = None
    avg_risk_realization: Optional[float] = None
    avg_capital_efficiency: Optional[float] = None
    most_effective_framework: Optional[str] = None
    messages: list[str] = Field(default_factory=list)


class HeuristicAlertsResponse(BaseModel):
    """Alertas proativos + benchmark para a tela de decisão."""

    alerts: list[HeuristicAlertItem] = Field(default_factory=list)
    total: int = 0
    benchmark: Optional[DecisionBenchmark] = None


class DomainPerformanceItem(BaseModel):
    """Performance por domínio financeiro."""

    domain: str
    domain_label: str
    cases_count: int
    avg_forecast_accuracy: Optional[float] = None
    avg_risk_realization: Optional[float] = None
    avg_capital_efficiency: Optional[float] = None
    divergence_rate: Optional[float] = None


class DecisionIntelligenceResponse(BaseModel):
    """Dashboard de inteligência decisória — KPIs agregados."""

    total_cases_closed: int = 0
    total_cases_active: int = 0
    avg_forecast_accuracy: Optional[float] = None
    divergence_total: int = 0
    divergence_success_count: int = 0
    divergence_success_rate: Optional[float] = None
    avg_risk_realization: Optional[float] = None
    avg_capital_efficiency: Optional[float] = None
    total_heuristics_active: int = 0
    domain_performance: list[DomainPerformanceItem] = Field(default_factory=list)
    top_frameworks: list[FrameworkUsageItem] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
#  API BALANCE
# ─────────────────────────────────────────────────────────────────────────────

class ApiBalanceResponse(BaseModel):
    """Saldo estimado de créditos da API Anthropic."""

    budget: float = Field(description="Orçamento total configurado (USD)")
    cost: float = Field(description="Custo estimado acumulado (USD)")
    remaining: float = Field(description="Saldo restante estimado (USD)")
    threshold: float = Field(description="Limite para alerta (USD)")
    warning: bool = Field(description="true = saldo abaixo do limite de alerta")
    input_tokens: int = Field(description="Total de tokens de entrada consumidos")
    output_tokens: int = Field(description="Total de tokens de saída consumidos")


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
