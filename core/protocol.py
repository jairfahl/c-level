"""
core/protocol.py  —  Orchestrator do Protocolo Decisório
Integra: classifier → quality_gate → fact_injector → feedback_loop

Fluxo de execução:
    1. Recebe input do executivo
    2. Classifica deterministicamente (classifier.py)
    3. Antes de cada transição: executa Quality Gate (quality_gate.py)
    4. Antes de E05/E06: injeta fatos verificados (fact_injector.py)
    5. Após E08: processa feedback de calibração (feedback_loop.py)

O LLM é chamado apenas nas etapas que exigem análise qualitativa.
O engine determinístico controla o fluxo — nunca o LLM.
"""

from __future__ import annotations
import json
from pathlib import Path
from models.decision import Decision, DecisionStatus, Classification
from core.classifier import DecisionClassifier
from core.quality_gate import QualityGate, ProtocolGateError, GateStatus
from core.fact_injector import FactInjector, InjectionTarget
from core.feedback_loop import FeedbackLoop

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class ProtocolOrchestrator:
    """
    Ponto de entrada único do sistema.
    Gerencia o ciclo de vida completo de uma decisão.

    Uso CLI (MVP):
        orch = ProtocolOrchestrator()
        decision = orch.iniciar("Precisamos emitir debêntures...", responsavel="CFO")
        decision = orch.executar_etapa(decision, etapa=1, llm_output={...})
    """

    def __init__(self):
        self.classifier  = DecisionClassifier()
        self.gate        = QualityGate()
        self.injector    = FactInjector()
        self.feedback    = FeedbackLoop()

    # ─────────────────────────────────────────
    # INICIALIZAÇÃO
    # ─────────────────────────────────────────

    def iniciar(self, input_text: str, responsavel: str) -> Decision:
        """
        Cria a Decision, pré-classifica com o engine determinístico
        e retorna pronta para execução da E01 (LLM).
        """
        decision = Decision(input_original=input_text, responsavel=responsavel)

        # Pré-classificação determinística (sem LLM)
        raw = self.classifier.classify(input_text)

        # Expõe o resultado como metadado para o LLM completar
        decision._pre_classification = raw   # type: ignore[attr-defined]

        return decision

    # ─────────────────────────────────────────
    # EXECUÇÃO DE ETAPA
    # ─────────────────────────────────────────

    def executar_etapa(self, decision: Decision, etapa: int,
                       llm_output: dict) -> Decision:
        """
        Recebe o JSON retornado pelo LLM para a etapa indicada,
        valida o gate de saída e avança o status da decisão.

        Raises ProtocolGateError se o gate bloquear.
        """
        # Aplica o output do LLM à etapa correspondente
        self._apply_llm_output(decision, etapa, llm_output)

        # Determina próxima etapa
        proxima = self._proxima_etapa(decision, etapa)
        if proxima is None:
            decision.avancar_status()
            return decision

        # Executa Quality Gate
        gate_result = self.gate.check(decision, from_etapa=etapa, to_etapa=proxima)

        if gate_result.status == GateStatus.VERMELHO:
            raise ProtocolGateError(gate_result)

        if gate_result.alertas or any(
            v.severidade == "ALERTA" for v in gate_result.violations
        ):
            decision._gate_warnings = gate_result  # type: ignore[attr-defined]

        decision.avancar_status()
        return decision

    # ─────────────────────────────────────────
    # GERAÇÃO DE PROMPT PARA ETAPA
    # ─────────────────────────────────────────

    def gerar_prompt(self, decision: Decision, etapa: int) -> str:
        """
        Lê o prompt template da etapa e injeta fatos verificados
        quando aplicável (E05, E06).
        """
        prompt_map = {
            1: "01_classifier.md",
            2: "02_framework_selector.md",
            3: "03_premise_extractor.md",
            4: "04_risk_identifier.md",
            5: "05_scenario_analyst.md",
            6: "06_recommendation.md",
            7: "07_registry.md",
            8: "08_post_decision.md",
        }
        filename = prompt_map.get(etapa)
        if not filename:
            raise ValueError(f"Etapa {etapa} não tem prompt definido.")

        prompt_path = PROMPTS_DIR / filename
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt não encontrado: {prompt_path}")

        template = prompt_path.read_text(encoding="utf-8")

        # Extrai o bloco de prompt interno do arquivo Markdown
        prompt_block = self._extract_prompt_block(template)

        # Injeta fatos verificados para E05 e E06
        if etapa == 5:
            return self.injector.inject_into_prompt(
                prompt_block, decision, InjectionTarget.E05_CENARIOS)
        if etapa == 6:
            return self.injector.inject_into_prompt(
                prompt_block, decision, InjectionTarget.E06_RECOMENDACAO)

        # Substitui placeholders de contexto
        return self._fill_context_placeholders(prompt_block, decision)

    # ─────────────────────────────────────────
    # PÓS-DECISÃO: PROCESSA FEEDBACK
    # ─────────────────────────────────────────

    def processar_revisao(self, decision: Decision) -> dict:
        """
        Chamado após E08 ser preenchida.
        Processa feedback, persiste e retorna relatório de calibração.
        """
        record = self.feedback.process(decision)
        report = self.feedback.calibration_report()

        if record and record.signals:
            report["sinais_desta_revisao"] = record.signals
            report["ajustes_recomendados_desta_revisao"] = record.ajustes_recomendados

        return report

    # ─────────────────────────────────────────
    # ESTADO DA DECISÃO
    # ─────────────────────────────────────────

    def status_summary(self, decision: Decision) -> dict:
        """
        Retorna resumo do estado atual da decisão para exibição CLI.
        """
        etapas_concluidas = []
        if decision.classificacao:    etapas_concluidas.append(1)
        if decision.frameworks:       etapas_concluidas.append(2)
        if decision.premissas:        etapas_concluidas.append(3)
        if decision.riscos:           etapas_concluidas.append(4)
        if decision.cenarios:         etapas_concluidas.append(5)
        if decision.recomendacao:     etapas_concluidas.append(6)
        if decision.registro:         etapas_concluidas.append(7)
        if decision.revisao:          etapas_concluidas.append(8)

        raw = self.classifier.classify(decision.input_original)

        return {
            "decision_id": decision.id,
            "status": decision.status.value,
            "responsavel": decision.responsavel,
            "proxima_etapa": decision.proxima_etapa,
            "etapas_concluidas": etapas_concluidas,
            "confianca_classificador": raw.confianca,
            "flags_classificador": raw.flags,
            "tipo_pre_classificado": raw.tipo_decisao.value,
            "protocolo_abreviado": (
                decision.frameworks.protocolo_abreviado
                if decision.frameworks else False
            ),
            "tem_riscos_bloqueadores": bool(
                decision.riscos and decision.riscos.riscos_bloqueadores
            ),
        }

    # ─────────────────────────────────────────
    # HELPERS INTERNOS
    # ─────────────────────────────────────────

    def _proxima_etapa(self, decision: Decision, etapa_atual: int) -> int | None:
        """Determina a próxima etapa considerando protocolo abreviado."""
        if etapa_atual == 4:
            # Verificar se pode pular E05
            clf = decision.classificacao
            fw  = decision.frameworks
            rm  = decision.riscos
            pode_abreviar = (
                fw and fw.protocolo_abreviado
                and clf and clf.impacto.value in ("MODERADO", "BAIXO")
                and (not rm or not rm.riscos_bloqueadores)
            )
            return 6 if pode_abreviar else 5

        mapa = {1: 2, 2: 3, 3: 4, 5: 6, 6: 7, 7: 8, 8: None}
        return mapa.get(etapa_atual)

    def _apply_llm_output(self, decision: Decision, etapa: int, output: dict) -> None:
        """Parseia e aplica o JSON do LLM ao campo correto da Decision."""
        from models.decision import (
            Classification, FrameworkSelection, PremiseExtraction,
            RiskMap, ScenarioAnalysis, Recommendation,
            DecisionRegistry, PostDecisionReview,
        )

        parsers = {
            1: lambda o: setattr(decision, "classificacao", Classification(**o)),
            2: lambda o: setattr(decision, "frameworks", FrameworkSelection(**o)),
            3: lambda o: setattr(decision, "premissas", PremiseExtraction(**o)),
            4: lambda o: setattr(decision, "riscos", RiskMap(**o)),
            5: lambda o: setattr(decision, "cenarios", ScenarioAnalysis(**o)),
            6: lambda o: setattr(decision, "recomendacao", Recommendation(**o)),
            7: lambda o: setattr(decision, "registro", DecisionRegistry(**o)),
            8: lambda o: setattr(decision, "revisao", PostDecisionReview(**o)),
        }
        parser = parsers.get(etapa)
        if parser:
            try:
                parser(output)
            except Exception as e:
                raise ValueError(
                    f"Erro ao parsear output do LLM para Etapa {etapa:02d}: {e}\n"
                    f"Output recebido: {json.dumps(output, ensure_ascii=False, indent=2)}"
                ) from e

    def _extract_prompt_block(self, markdown_content: str) -> str:
        """Extrai o bloco de código do prompt dentro do arquivo Markdown."""
        import re
        match = re.search(r"```\n(.*?)```", markdown_content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return markdown_content

    def _fill_context_placeholders(self, prompt: str, decision: Decision) -> str:
        """Substitui placeholders de contexto com dados das etapas anteriores."""
        replacements = {
            "{DECISAO}": decision.input_original,
            "{JSON_CLASSIFICACAO}": (
                decision.classificacao.model_dump_json(indent=2)
                if decision.classificacao else "{}"
            ),
            "{JSON_FRAMEWORKS}": (
                decision.frameworks.model_dump_json(indent=2)
                if decision.frameworks else "{}"
            ),
            "{JSON_PREMISSAS}": (
                decision.premissas.model_dump_json(indent=2)
                if decision.premissas else "{}"
            ),
            "{JSON_RISCOS}": (
                decision.riscos.model_dump_json(indent=2)
                if decision.riscos else "{}"
            ),
            "{JSON_CENARIOS}": (
                decision.cenarios.model_dump_json(indent=2)
                if decision.cenarios else "{}"
            ),
            "{JSON_RECOMENDACAO}": (
                decision.recomendacao.model_dump_json(indent=2)
                if decision.recomendacao else "{}"
            ),
        }
        for placeholder, value in replacements.items():
            prompt = prompt.replace(placeholder, value)
        return prompt
