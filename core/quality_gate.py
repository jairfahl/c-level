"""
core/quality_gate.py
BKL-002 — Quality Gate inter-etapas

Validação determinística antes de avançar entre etapas do protocolo.
Se o gate falha (VERMELHO), o protocolo não avança.
Zero delegação ao LLM. Regras explícitas e auditáveis.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from models.decision import (
    Decision, ImpactLevel, ConfidenceLevel,
    DecisionType, Reversibility, TimeHorizon,
)


# ─────────────────────────────────────────────
# THRESHOLDS
# ─────────────────────────────────────────────

MIN_PREMISSAS: dict[ImpactLevel, int] = {
    ImpactLevel.CRITICO:  5,
    ImpactLevel.ELEVADO:  3,
    ImpactLevel.MODERADO: 2,
    ImpactLevel.BAIXO:    1,
}

MIN_RISCOS: dict[ImpactLevel, int] = {
    ImpactLevel.CRITICO:  5,
    ImpactLevel.ELEVADO:  3,
    ImpactLevel.MODERADO: 2,
    ImpactLevel.BAIXO:    1,
}

MIN_PROB_PESSIMISTA_COM_BLOQUEADOR = 15   # %
MIN_CONFIANCA_CLASSIFICADOR = 0.50
MIN_PALAVRAS_INPUT = 15


# ─────────────────────────────────────────────
# RESULTADO DO GATE
# ─────────────────────────────────────────────

class GateStatus(str, Enum):
    VERDE    = "VERDE"
    AMARELO  = "AMARELO"
    VERMELHO = "VERMELHO"


@dataclass
class GateViolation:
    codigo: str
    criterio: str
    valor_atual: str
    valor_esperado: str
    severidade: str          # BLOQUEADOR | ALERTA
    etapa_afetada: int
    acao_corretiva: str


@dataclass
class GateResult:
    etapa_validada: int
    proxima_etapa: int
    status: GateStatus = GateStatus.VERDE
    violations: list[GateViolation] = field(default_factory=list)
    alertas: list[str] = field(default_factory=list)

    @property
    def pode_avancar(self) -> bool:
        return not any(v.severidade == "BLOQUEADOR" for v in self.violations)

    def _recalc_status(self):
        if not self.pode_avancar:
            self.status = GateStatus.VERMELHO
        elif self.violations or self.alertas:
            self.status = GateStatus.AMARELO
        else:
            self.status = GateStatus.VERDE

    def add_bloqueador(self, codigo, criterio, atual, esperado, etapa, acao):
        self.violations.append(GateViolation(
            codigo=codigo, criterio=criterio,
            valor_atual=atual, valor_esperado=esperado,
            severidade="BLOQUEADOR", etapa_afetada=etapa, acao_corretiva=acao
        ))
        self._recalc_status()

    def add_alerta(self, codigo, criterio, atual, esperado, etapa, acao):
        self.violations.append(GateViolation(
            codigo=codigo, criterio=criterio,
            valor_atual=atual, valor_esperado=esperado,
            severidade="ALERTA", etapa_afetada=etapa, acao_corretiva=acao
        ))
        self._recalc_status()

    @property
    def resumo(self) -> str:
        tag = f"Gate E{self.etapa_validada:02d}→E{self.proxima_etapa:02d}"
        if self.status == GateStatus.VERDE:
            return f"{tag}: VERDE — sem violações."
        elif self.status == GateStatus.AMARELO:
            return f"{tag}: AMARELO — {len(self.violations)} alerta(s). Avança com ressalvas."
        else:
            n = sum(1 for v in self.violations if v.severidade == "BLOQUEADOR")
            return f"{tag}: VERMELHO — {n} bloqueador(es). Retornar à etapa {self.etapa_validada}."


# ─────────────────────────────────────────────
# QUALITY GATE ENGINE
# ─────────────────────────────────────────────

class QualityGate:
    """
    Valida condições de avanço entre etapas do protocolo.
    Chamado pelo orchestrator (protocol.py) antes de cada transição.

    Exemplo:
        gate = QualityGate()
        result = gate.check(decision, from_etapa=3, to_etapa=4)
        if not result.pode_avancar:
            raise ProtocolGateError(result)
    """

    def check(self, decision: Decision, from_etapa: int, to_etapa: int) -> GateResult:
        r = GateResult(etapa_validada=from_etapa, proxima_etapa=to_etapa)

        dispatch = {
            (1, 2): self._e01_to_e02,
            (2, 3): self._e02_to_e03,
            (3, 4): self._e03_to_e04,
            (4, 5): self._e04_to_e05,
            (4, 6): self._e04_to_e06_abreviado,
            (5, 6): self._e05_to_e06,
            (6, 7): self._e06_to_e07,
            (7, 8): self._e07_to_e08,
        }

        handler = dispatch.get((from_etapa, to_etapa))
        if handler:
            handler(decision, r)
        else:
            r.alertas.append(
                f"Transição E{from_etapa:02d}→E{to_etapa:02d} sem gate definido. Avançando sem validação."
            )
        return r

    # ── E01 → E02 ─────────────────────────────

    def _e01_to_e02(self, d: Decision, r: GateResult) -> None:
        if d.classificacao is None:
            r.add_bloqueador("GV-001",
                "Classificação obrigatória antes de selecionar framework",
                "None", "Classification preenchida", 1,
                "Execute a Etapa 01 (classificador) antes de prosseguir.")
            return

        # Re-classifica para obter score de confiança
        from core.classifier import DecisionClassifier
        raw = DecisionClassifier().classify(d.input_original)
        if raw.confianca < MIN_CONFIANCA_CLASSIFICADOR:
            r.add_alerta("GV-002",
                f"Confiança do classificador >= {MIN_CONFIANCA_CLASSIFICADOR}",
                str(raw.confianca), f">= {MIN_CONFIANCA_CLASSIFICADOR}", 1,
                "Enriqueça a descrição da decisão com mais contexto.")

        if len(d.input_original.split()) < MIN_PALAVRAS_INPUT:
            r.add_alerta("GV-003",
                f"Input com mínimo de {MIN_PALAVRAS_INPUT} palavras",
                f"{len(d.input_original.split())} palavras",
                f">= {MIN_PALAVRAS_INPUT} palavras", 1,
                "Detalhe a decisão para garantir classificação precisa.")

    # ── E02 → E03 ─────────────────────────────

    def _e02_to_e03(self, d: Decision, r: GateResult) -> None:
        if d.frameworks is None:
            r.add_bloqueador("GV-004",
                "Seleção de framework obrigatória antes de extrair premissas",
                "None", "FrameworkSelection preenchida", 2,
                "Execute a Etapa 02 (framework selector) antes de prosseguir.")

    # ── E03 → E04 ─────────────────────────────

    def _e03_to_e04(self, d: Decision, r: GateResult) -> None:
        if d.premissas is None:
            r.add_bloqueador("GV-005",
                "Extração de premissas obrigatória antes de mapear riscos",
                "None", "PremiseExtraction preenchida", 3,
                "Execute a Etapa 03 (premise extractor) antes de prosseguir.")
            return

        impacto = d.classificacao.impacto if d.classificacao else ImpactLevel.MODERADO
        min_p = MIN_PREMISSAS[impacto]
        total = (len(d.premissas.premissas_declaradas)
                 + len(d.premissas.premissas_implicitas))

        if total < min_p:
            sev = ("BLOQUEADOR" if impacto in (ImpactLevel.CRITICO, ImpactLevel.ELEVADO)
                   else "ALERTA")
            (r.add_bloqueador if sev == "BLOQUEADOR" else r.add_alerta)(
                "GV-006",
                f"Mínimo de {min_p} premissas para impacto {impacto.value}",
                f"{total} premissas identificadas",
                f">= {min_p} premissas", 3,
                "Retorne à Etapa 03 e explicite mais premissas — especialmente as implícitas.")

        # Premissas implícitas de alta criticidade sem validação
        criticas = [p for p in d.premissas.premissas_implicitas
                    if p.criticidade in (ImpactLevel.CRITICO, ImpactLevel.ELEVADO)]
        if criticas:
            r.alertas.append(
                f"{len(criticas)} premissa(s) implícita(s) de criticidade ALTA/CRITICA não validadas. "
                "Considere validá-las antes de mapear riscos.")

    # ── E04 → E05 ─────────────────────────────

    def _e04_to_e05(self, d: Decision, r: GateResult) -> None:
        self._validar_riscos(d, r, etapa=4)

        if d.classificacao and d.classificacao.impacto not in (
                ImpactLevel.CRITICO, ImpactLevel.ELEVADO):
            r.alertas.append(
                f"Impacto {d.classificacao.impacto.value}: E05 (cenários) é opcional. "
                "Pode usar protocolo abreviado E04→E06.")

    # ── E04 → E06 protocolo abreviado ─────────

    def _e04_to_e06_abreviado(self, d: Decision, r: GateResult) -> None:
        self._validar_riscos(d, r, etapa=4)

        if d.classificacao and d.classificacao.impacto in (
                ImpactLevel.CRITICO, ImpactLevel.ELEVADO):
            r.add_bloqueador("GV-010",
                "Protocolo abreviado não permitido para impacto CRITICO ou ELEVADO",
                f"impacto = {d.classificacao.impacto.value}",
                "impacto = MODERADO ou BAIXO", 4,
                "Execute a Etapa 05 (análise de cenários) antes de prosseguir para E06.")

        if d.riscos and d.riscos.riscos_bloqueadores:
            r.add_bloqueador("GV-011",
                "Protocolo abreviado não permitido com riscos bloqueadores mapeados",
                f"Bloqueadores: {d.riscos.riscos_bloqueadores}",
                "Nenhum risco bloqueador", 4,
                "Execute a Etapa 05 — riscos bloqueadores exigem análise de cenários completa.")

    # ── E05 → E06 ─────────────────────────────

    def _e05_to_e06(self, d: Decision, r: GateResult) -> None:
        if d.cenarios is None:
            r.add_bloqueador("GV-012",
                "Análise de cenários obrigatória antes da recomendação",
                "None", "ScenarioAnalysis preenchida", 5,
                "Execute a Etapa 05 (scenario analyst) antes de prosseguir.")
            return

        if d.riscos and d.riscos.riscos_bloqueadores:
            prob_str = (d.cenarios.cenario_pessimista.probabilidade_estimada
                        .replace("%", "").strip())
            try:
                prob = float(prob_str.split("-")[0])
                if prob < MIN_PROB_PESSIMISTA_COM_BLOQUEADOR:
                    r.add_bloqueador("GV-013",
                        f"Prob. cenário pessimista >= {MIN_PROB_PESSIMISTA_COM_BLOQUEADOR}% com riscos bloqueadores",
                        f"{prob_str}%",
                        f">= {MIN_PROB_PESSIMISTA_COM_BLOQUEADOR}%", 5,
                        "Revise a probabilidade do cenário pessimista na Etapa 05.")
            except (ValueError, IndexError):
                r.alertas.append(
                    "Probabilidade do cenário pessimista em formato não numérico. Validação ignorada.")

    # ── E06 → E07 ─────────────────────────────

    def _e06_to_e07(self, d: Decision, r: GateResult) -> None:
        if d.recomendacao is None:
            r.add_bloqueador("GV-014",
                "Recomendação estruturada obrigatória antes do registro",
                "None", "Recommendation preenchida", 6,
                "Execute a Etapa 06 (recommendation) antes de prosseguir.")
            return

        if d.recomendacao.nivel_confianca == ConfidenceLevel.BAIXO:
            r.add_alerta("GV-015",
                "Recomendação com confiança BAIXA requer validação adicional de premissas",
                "nivel_confianca = BAIXO", "MEDIO ou ALTO", 6,
                "Revise premissas não validadas (E03) antes de registrar a decisão.")

        if not d.recomendacao.metricas_de_sucesso:
            r.add_bloqueador("GV-016",
                "Mínimo de 1 métrica de sucesso obrigatória para registro formal",
                "0 métricas definidas", ">= 1 métrica", 6,
                "Defina ao menos uma métrica de sucesso com valor-alvo e prazo na Etapa 06.")

    # ── E07 → E08 ─────────────────────────────

    def _e07_to_e08(self, d: Decision, r: GateResult) -> None:
        if d.registro is None:
            r.add_bloqueador("GV-017",
                "Registro formal obrigatório antes da revisão pós-decisão",
                "None", "DecisionRegistry preenchido", 7,
                "Execute a Etapa 07 (registry) antes de prosseguir.")
            return

        if (d.registro.divergencia.existe
                and not d.registro.divergencia.riscos_adicionais_assumidos):
            r.add_bloqueador("GV-018",
                "Divergência registrada exige riscos adicionais explícitos",
                "riscos_adicionais_assumidos = []", "Lista preenchida", 7,
                "Retorne ao registro (E07) e explicite os riscos assumidos ao divergir da recomendação.")

    # ── Helper ────────────────────────────────

    def _validar_riscos(self, d: Decision, r: GateResult, etapa: int) -> None:
        if d.riscos is None:
            r.add_bloqueador("GV-007",
                "Mapeamento de riscos obrigatório",
                "None", "RiskMap preenchido", etapa,
                "Execute a Etapa 04 (risk identifier) antes de prosseguir.")
            return

        impacto = d.classificacao.impacto if d.classificacao else ImpactLevel.MODERADO
        min_r = MIN_RISCOS[impacto]
        if len(d.riscos.riscos) < min_r:
            sev = ("BLOQUEADOR" if impacto in (ImpactLevel.CRITICO, ImpactLevel.ELEVADO)
                   else "ALERTA")
            (r.add_bloqueador if sev == "BLOQUEADOR" else r.add_alerta)(
                "GV-008",
                f"Mínimo de {min_r} riscos para impacto {impacto.value}",
                f"{len(d.riscos.riscos)} riscos mapeados",
                f">= {min_r} riscos", etapa,
                "Retorne à Etapa 04 e mapeie mais riscos.")

        if (d.riscos.risk_score_agregado == ImpactLevel.CRITICO
                and not d.riscos.riscos_sistemicos):
            r.add_bloqueador("GV-009",
                "Risk score CRITICO exige ao menos 1 risco sistêmico mapeado",
                "0 riscos sistêmicos", ">= 1 risco sistêmico", etapa,
                "Retorne à Etapa 04 e mapeie riscos com efeito cascata em múltiplos domínios.")


# ─────────────────────────────────────────────
# EXCEPTION
# ─────────────────────────────────────────────

class ProtocolGateError(Exception):
    def __init__(self, gate_result: GateResult):
        self.gate_result = gate_result
        msg = f"\n{gate_result.resumo}\n"
        for v in (x for x in gate_result.violations if x.severidade == "BLOQUEADOR"):
            msg += f"\n[{v.codigo}] {v.criterio}\n  Atual: {v.valor_atual}\n  → {v.acao_corretiva}\n"
        super().__init__(msg)
