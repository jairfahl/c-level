"""
models/decision.py
Schema central do Mentor C-Level.
Todas as entidades do protocolo decisório são tipadas aqui.
"""

from __future__ import annotations
from enum import Enum
from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, Field, model_validator
import uuid


# ─────────────────────────────────────────────
# ENUMS — Vocabulário controlado do sistema
# ─────────────────────────────────────────────

class DecisionType(str, Enum):
    ALOCACAO_CAPITAL      = "ALOCACAO_CAPITAL"
    ESTRUTURA_FINANCEIRA  = "ESTRUTURA_FINANCEIRA"
    GESTAO_CAIXA          = "GESTAO_CAIXA"
    PLANEJAMENTO_ORCAMENTO = "PLANEJAMENTO_ORCAMENTO"
    FORECAST              = "FORECAST"
    RISCO_FINANCEIRO      = "RISCO_FINANCEIRO"
    OUTRO                 = "OUTRO"


class ImpactLevel(str, Enum):
    CRITICO  = "CRITICO"
    ELEVADO  = "ELEVADO"
    MODERADO = "MODERADO"
    BAIXO    = "BAIXO"


class Reversibility(str, Enum):
    IRREVERSIVEL             = "IRREVERSIVEL"
    PARCIALMENTE_REVERSIVEL  = "PARCIALMENTE_REVERSIVEL"
    REVERSIVEL               = "REVERSIVEL"


class TimeHorizon(str, Enum):
    CURTO_PRAZO  = "CURTO_PRAZO"   # < 3 meses
    MEDIO_PRAZO  = "MEDIO_PRAZO"   # 3–12 meses
    LONGO_PRAZO  = "LONGO_PRAZO"   # > 12 meses


class FrameworkType(str, Enum):
    PDCA                    = "PDCA"
    ANALISE_DE_CENARIOS     = "ANALISE_DE_CENARIOS"
    TRADE_OFF_ANALYSIS      = "TRADE_OFF_ANALYSIS"
    TEORIA_DOS_JOGOS        = "TEORIA_DOS_JOGOS"
    PRINCIPIO_DA_PIRAMIDE   = "PRINCIPIO_DA_PIRAMIDE"
    RISCO_SISTEMICO         = "RISCO_SISTEMICO"


class PremiseType(str, Enum):
    MACRO          = "MACRO"
    MERCADO        = "MERCADO"
    OPERACIONAL    = "OPERACIONAL"
    FINANCEIRA     = "FINANCEIRA"
    COMPORTAMENTAL = "COMPORTAMENTAL"


class ValidationStatus(str, Enum):
    VALIDADA      = "VALIDADA"
    NAO_VALIDADA  = "NAO_VALIDADA"
    QUESTIONAVEL  = "QUESTIONAVEL"


class RiskCategory(str, Enum):
    FINANCEIRO   = "FINANCEIRO"
    OPERACIONAL  = "OPERACIONAL"
    ESTRATEGICO  = "ESTRATEGICO"
    REGULATORIO  = "REGULATORIO"
    REPUTACIONAL = "REPUTACIONAL"
    SISTEMICO    = "SISTEMICO"


class Probability(str, Enum):
    ALTA  = "ALTA"
    MEDIA = "MEDIA"
    BAIXA = "BAIXA"


class MaterializationSpeed(str, Enum):
    IMEDIATA      = "IMEDIATA"
    CURTO_PRAZO   = "CURTO_PRAZO"
    MEDIO_PRAZO   = "MEDIO_PRAZO"
    LONGO_PRAZO   = "LONGO_PRAZO"


class ConfidenceLevel(str, Enum):
    ALTO  = "ALTO"
    MEDIO = "MEDIO"
    BAIXO = "BAIXO"


class DecisionStatus(str, Enum):
    RASCUNHO                    = "RASCUNHO"
    CLASSIFICADA                = "CLASSIFICADA"
    FRAMEWORK_SELECIONADO       = "FRAMEWORK_SELECIONADO"
    PREMISSAS_EXPLICITADAS      = "PREMISSAS_EXPLICITADAS"
    RISCOS_MAPEADOS             = "RISCOS_MAPEADOS"
    CENARIOS_ANALISADOS         = "CENARIOS_ANALISADOS"
    RECOMENDACAO_ESTRUTURADA    = "RECOMENDACAO_ESTRUTURADA"
    REGISTRADA                  = "REGISTRADA"
    REVISAO_PENDENTE            = "REVISAO_PENDENTE"
    CONCLUIDA                   = "CONCLUIDA"


# ─────────────────────────────────────────────
# ENTIDADES — Blocos do protocolo decisório
# ─────────────────────────────────────────────

class Classification(BaseModel):
    """Saída da Etapa 01 — Classificador."""
    tipo_decisao: DecisionType
    impacto: ImpactLevel
    reversibilidade: Reversibility
    horizonte: TimeHorizon
    interdependencia_estrategica: bool
    dominio_apqc: str = Field(description="Ex: Domínio 9 - Gestão Financeira")
    decisao_resumida: str = Field(max_length=200)
    justificativa_classificacao: str = Field(max_length=600)

    @property
    def requer_cenarios(self) -> bool:
        return self.impacto in (ImpactLevel.CRITICO, ImpactLevel.ELEVADO)

    @property
    def protocolo_abreviado(self) -> bool:
        return self.impacto == ImpactLevel.BAIXO


class SelectedFramework(BaseModel):
    """Um framework dentro da seleção da Etapa 02."""
    framework: FrameworkType
    justificativa: str = Field(max_length=400)
    parametros_obrigatorios: list[str]
    ordem_aplicacao: int = Field(ge=1)


class FrameworkSelection(BaseModel):
    """Saída da Etapa 02 — Seletor de Framework."""
    frameworks_selecionados: list[SelectedFramework]
    framework_primario: FrameworkType
    protocolo_abreviado: bool
    etapas_obrigatorias: list[int] = Field(description="Etapas 1-8 obrigatórias para esta decisão")

    @model_validator(mode="after")
    def validate_etapas(self) -> FrameworkSelection:
        invalid = [e for e in self.etapas_obrigatorias if e not in range(1, 9)]
        if invalid:
            raise ValueError(f"Etapas inválidas: {invalid}. Permitido: 1–8.")
        return self


class Premise(BaseModel):
    """Premissa declarada — Etapa 03."""
    premissa: str
    tipo: PremiseType
    status_validacao: ValidationStatus
    tensionamento: str = Field(description="Pergunta que questiona a solidez da premissa")


class ImplicitPremise(BaseModel):
    """Premissa implícita — Etapa 03."""
    premissa: str
    evidencia: str
    criticidade: ImpactLevel
    tensionamento: str


class PremiseExtraction(BaseModel):
    """Saída da Etapa 03 — Extrator de Premissas."""
    premissas_declaradas: list[Premise]
    premissas_implicitas: list[ImplicitPremise]
    premissas_criticas_nao_validadas: list[str]
    recomendacao_validacao: str = Field(max_length=600)

    @property
    def tem_bloqueadores(self) -> bool:
        return any(
            p.criticidade == ImpactLevel.CRITICO
            for p in self.premissas_implicitas
        )


class Risk(BaseModel):
    """Risco individual — Etapa 04."""
    id: str = Field(pattern=r"^R\d+$", description="Ex: R1, R2, R3")
    descricao: str
    categoria: RiskCategory
    probabilidade: Probability
    impacto_potencial: ImpactLevel
    velocidade_materializacao: MaterializationSpeed
    premissa_associada: Optional[str] = None
    indicador_monitoramento: str
    gatilho_alerta: str


class SystemicRisk(BaseModel):
    """Risco sistêmico com efeito cascata — Etapa 04."""
    descricao: str
    dominios_afetados: list[str]
    severidade: str


class RiskMap(BaseModel):
    """Saída da Etapa 04 — Identificador de Riscos."""
    riscos: list[Risk]
    riscos_sistemicos: list[SystemicRisk]
    risk_score_agregado: ImpactLevel
    riscos_bloqueadores: list[str] = Field(description="IDs dos riscos bloqueadores")
    condicoes_de_aborto: list[str]

    @model_validator(mode="after")
    def validate_risk_ids(self) -> RiskMap:
        ids_existentes = {r.id for r in self.riscos}
        invalidos = [id_ for id_ in self.riscos_bloqueadores if id_ not in ids_existentes]
        if invalidos:
            raise ValueError(f"riscos_bloqueadores referencia IDs inexistentes: {invalidos}")
        return self


class FinancialImpact(BaseModel):
    metrica_principal: str
    valor_estimado: str
    horizonte: str


class Scenario(BaseModel):
    """Cenário individual — Etapa 05."""
    nome: str
    descricao: str
    probabilidade_estimada: str
    impacto_financeiro: FinancialImpact


class BaseScenario(Scenario):
    premissas_ativas: list[str]
    riscos_materializados: list[str]
    acoes_necessarias: list[str]


class OptimisticScenario(Scenario):
    premissas_ativas: list[str]
    condicoes_necessarias: list[str]


class PessimisticScenario(Scenario):
    premissas_falhas: list[str]
    riscos_materializados: list[str]
    plano_contingencia: list[str]


class ScenarioAnalysis(BaseModel):
    """Saída da Etapa 05 — Analista de Cenários."""
    cenario_base: BaseScenario
    cenario_otimista: OptimisticScenario
    cenario_pessimista: PessimisticScenario
    cenario_recomendado_para_decisao: str = Field(pattern=r"^(BASE|OTIMISTA|PESSIMISTA)$")
    justificativa_recomendacao: str = Field(max_length=600)
    ponto_de_inflexao: str
    valor_da_opcao_de_saida: str


class SupportArgument(BaseModel):
    argumento: str
    evidencias: list[str]
    peso: str = Field(pattern=r"^(PRIMARIO|SECUNDARIO)$")


class SuccessMetric(BaseModel):
    metrica: str
    valor_alvo: str
    prazo: str
    frequencia_revisao: str


class Recommendation(BaseModel):
    """Saída da Etapa 06 — Recomendação estruturada (Pirâmide de Minto)."""
    conclusao: str
    nivel_confianca: ConfidenceLevel
    justificativa_confianca: str = Field(max_length=400)
    argumentos_suporte: list[SupportArgument]
    condicoes_de_validade: list[str]
    alternativas_avaliadas: list[dict]
    riscos_residuais_assumidos: list[str]
    metricas_de_sucesso: list[SuccessMetric]
    decisao_final_do_executivo: Optional[str] = None


class MonitoringCriteria(BaseModel):
    metrica: str
    valor_alvo: str
    prazo_verificacao: str
    responsavel_monitoramento: str


class Divergence(BaseModel):
    existe: bool
    descricao: Optional[str] = None
    racional_executivo: Optional[str] = None
    riscos_adicionais_assumidos: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_divergence_fields(self) -> Divergence:
        if self.existe and not self.descricao:
            raise ValueError("Se divergencia.existe = True, descricao é obrigatória.")
        if self.existe and not self.racional_executivo:
            raise ValueError("Se divergencia.existe = True, racional_executivo é obrigatório.")
        return self


class DecisionRegistry(BaseModel):
    """Saída da Etapa 07 — Registro formal auditável."""
    registro_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    data_registro: datetime = Field(default_factory=datetime.now)
    responsavel: str
    decisao_resumida: str
    classificacao_final: Classification
    framework_aplicado: FrameworkType
    premissas_criticas_assumidas: list[str]
    riscos_assumidos: list[str]
    cenario_base_decisao: str
    recomendacao_analitica: str
    decisao_executiva: str
    divergencia: Divergence
    criterios_monitoramento: list[MonitoringCriteria]
    gatilhos_revisao_antecipada: list[str]
    data_revisao_programada: date
    status: str = "REGISTRADO_AGUARDANDO_EXECUCAO"


class DeviationAnalysis(BaseModel):
    magnitude: str = Field(pattern=r"^(SIGNIFICATIVO|MODERADO|DESPREZIVEL)$")
    direcao: str = Field(pattern=r"^(POSITIVO|NEGATIVO|NEUTRO)$")
    descricao: str


class DeviationCause(BaseModel):
    causa: str
    origem: str
    premissa_ou_risco_associado: Optional[str] = None


class DivergenceImpact(BaseModel):
    houve_divergencia_registrada: bool
    a_divergencia_piorou_o_resultado: Optional[str] = None  # true | false | INDETERMINADO
    analise: Optional[str] = None


class Learning(BaseModel):
    aprendizado: str
    tipo: str
    aplicabilidade: str


class PostDecisionReview(BaseModel):
    """Saída da Etapa 08 — Revisão pós-decisão."""
    revisao_id: str = Field(description="Referência ao registro_id da E07")
    data_revisao: datetime = Field(default_factory=datetime.now)
    responsavel: str
    resultado_esperado: str
    resultado_real: str
    desvio: DeviationAnalysis
    causas_do_desvio: list[DeviationCause]
    premissas_invalidadas: list[str]
    riscos_que_se_materializaram: list[str]
    riscos_nao_materializados: list[str]
    impacto_da_divergencia: DivergenceImpact
    aprendizados: list[Learning]
    ajustes_recomendados_ao_modelo: list[str]
    status_final: str = Field(pattern=r"^(CONCLUIDO|REQUER_NOVA_REVISAO)$")
    nova_data_revisao: Optional[date] = None

    @model_validator(mode="after")
    def validate_nova_data(self) -> PostDecisionReview:
        if self.status_final == "REQUER_NOVA_REVISAO" and not self.nova_data_revisao:
            raise ValueError("nova_data_revisao é obrigatória quando status = REQUER_NOVA_REVISAO.")
        return self


# ─────────────────────────────────────────────
# ENTIDADE CENTRAL — Decision (agregado raiz)
# ─────────────────────────────────────────────

class Decision(BaseModel):
    """
    Agregado raiz do Mentor C-Level.
    Representa o ciclo de vida completo de uma decisão executiva.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    criado_em: datetime = Field(default_factory=datetime.now)
    atualizado_em: datetime = Field(default_factory=datetime.now)
    status: DecisionStatus = DecisionStatus.RASCUNHO
    input_original: str = Field(description="Texto livre da decisão conforme inserido pelo executivo")
    responsavel: str

    # Etapas do protocolo — preenchidas sequencialmente
    classificacao: Optional[Classification] = None           # E01
    frameworks: Optional[FrameworkSelection] = None          # E02
    premissas: Optional[PremiseExtraction] = None            # E03
    riscos: Optional[RiskMap] = None                         # E04
    cenarios: Optional[ScenarioAnalysis] = None              # E05
    recomendacao: Optional[Recommendation] = None            # E06
    registro: Optional[DecisionRegistry] = None              # E07
    revisao: Optional[PostDecisionReview] = None             # E08

    def avancar_status(self) -> None:
        """Avança o status com base nas etapas preenchidas."""
        if self.revisao:
            self.status = DecisionStatus.CONCLUIDA
        elif self.registro:
            self.status = DecisionStatus.REVISAO_PENDENTE
        elif self.recomendacao:
            self.status = DecisionStatus.RECOMENDACAO_ESTRUTURADA
        elif self.cenarios:
            self.status = DecisionStatus.CENARIOS_ANALISADOS
        elif self.riscos:
            self.status = DecisionStatus.RISCOS_MAPEADOS
        elif self.premissas:
            self.status = DecisionStatus.PREMISSAS_EXPLICITADAS
        elif self.frameworks:
            self.status = DecisionStatus.FRAMEWORK_SELECIONADO
        elif self.classificacao:
            self.status = DecisionStatus.CLASSIFICADA
        self.atualizado_em = datetime.now()

    @property
    def proxima_etapa(self) -> Optional[int]:
        """Retorna o número da próxima etapa a executar."""
        mapa = {
            DecisionStatus.RASCUNHO: 1,
            DecisionStatus.CLASSIFICADA: 2,
            DecisionStatus.FRAMEWORK_SELECIONADO: 3,
            DecisionStatus.PREMISSAS_EXPLICITADAS: 4,
            DecisionStatus.RISCOS_MAPEADOS: 5,
            DecisionStatus.CENARIOS_ANALISADOS: 6,
            DecisionStatus.RECOMENDACAO_ESTRUTURADA: 7,
            DecisionStatus.REVISAO_PENDENTE: 8,
            DecisionStatus.CONCLUIDA: None,
        }
        return mapa.get(self.status)
