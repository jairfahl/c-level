"""
core/fact_injector.py  —  BKL-003
Injeção de fatos verificados pré-LLM.

O engine injeta um bloco fixo nos prompts das Etapas 05 e 06
antes da chamada ao LLM. O LLM não reclassifica, não ignora
riscos bloqueadores, não redefine cenários.

Princípio TaxMind: [CALCULOS VERIFICADOS] -> [FATOS VERIFICADOS PELO ENGINE]
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from models.decision import Decision, ImpactLevel, ConfidenceLevel


class InjectionTarget(str, Enum):
    E05_CENARIOS     = "E05_CENARIOS"
    E06_RECOMENDACAO = "E06_RECOMENDACAO"


@dataclass
class InjectedFacts:
    target: InjectionTarget
    bloco: str
    warnings: list[str]


class FactInjector:
    """
    Constrói o bloco [FATOS VERIFICADOS PELO ENGINE] para E05 e E06.

    Uso:
        injector = FactInjector()
        facts = injector.build(decision, InjectionTarget.E05_CENARIOS)
        prompt_final = facts.bloco + prompt_template
    """

    HDR = (
        "╔══════════════════════════════════════════════════════╗\n"
        "║  FATOS VERIFICADOS PELO ENGINE — NÃO RECLASSIFICAR  ║\n"
        "║  Calculados deterministicamente. Não questione.     ║\n"
        "╚══════════════════════════════════════════════════════╝\n"
    )
    FTR = "══════════ FIM DOS FATOS VERIFICADOS ══════════\n"

    def build(self, decision: Decision, target: InjectionTarget) -> InjectedFacts:
        warnings: list[str] = []
        L: list[str] = [self.HDR]

        # BLOCO 1 — Classificação
        L.append("[ CLASSIFICAÇÃO ]")
        if decision.classificacao:
            c = decision.classificacao
            L += [
                f"  Tipo:              {c.tipo_decisao.value}",
                f"  Impacto:           {c.impacto.value}",
                f"  Reversibilidade:   {c.reversibilidade.value}",
                f"  Horizonte:         {c.horizonte.value}",
                f"  Interdep. Estrat.: {'SIM' if c.interdependencia_estrategica else 'NAO'}",
                f"  Domínio APQC:      {c.dominio_apqc}",
                f"  Resumo:            {c.decisao_resumida}",
            ]
            if c.impacto == ImpactLevel.CRITICO:
                warnings.append("IMPACTO CRÍTICO: protocolo completo obrigatório. Não simplificar E05/E06.")
        else:
            L.append("  [AUSENTE — classificação não executada]")
            warnings.append("Classificação ausente. Validade desta etapa reduzida.")
        L.append("")

        # BLOCO 2 — Frameworks
        L.append("[ FRAMEWORKS SELECIONADOS ]")
        if decision.frameworks:
            fw = decision.frameworks
            L.append(f"  Primário: {fw.framework_primario.value}  |  Abreviado: {'SIM' if fw.protocolo_abreviado else 'NAO'}")
            for s in fw.frameworks_selecionados:
                L.append(f"  [{s.ordem_aplicacao}] {s.framework.value}: {s.justificativa}")
        else:
            L.append("  [AUSENTE]")
        L.append("")

        # BLOCO 3 — Premissas críticas
        L.append("[ PREMISSAS CRÍTICAS NÃO VALIDADAS ]")
        if decision.premissas:
            pr = decision.premissas
            if pr.premissas_criticas_nao_validadas:
                for i, p in enumerate(pr.premissas_criticas_nao_validadas, 1):
                    L.append(f"  {i}. {p}")
                warnings.append(
                    f"{len(pr.premissas_criticas_nao_validadas)} premissa(s) crítica(s) não validada(s). "
                    "Cenários e recomendações têm validade condicional à confirmação dessas premissas.")
            else:
                L.append("  Nenhuma — todas as premissas críticas foram validadas.")
            impl_altas = [p for p in pr.premissas_implicitas
                          if p.criticidade in (ImpactLevel.CRITICO, ImpactLevel.ELEVADO)]
            if impl_altas:
                L.append(f"  Premissas implícitas de alta criticidade ({len(impl_altas)}):")
                for p in impl_altas:
                    L.append(f"    - {p.premissa}")
        else:
            L.append("  [AUSENTE]")
        L.append("")

        # BLOCO 4 — Riscos
        L.append("[ MAPA DE RISCOS ]")
        if decision.riscos:
            rm = decision.riscos
            L += [
                f"  Risk score agregado: {rm.risk_score_agregado.value}",
                f"  Total de riscos:     {len(rm.riscos)}",
                f"  Riscos sistêmicos:   {len(rm.riscos_sistemicos)}",
            ]
            if rm.riscos_bloqueadores:
                L.append(f"  BLOQUEADORES:        {rm.riscos_bloqueadores}")
                warnings.append(
                    f"RISCOS BLOQUEADORES: {rm.riscos_bloqueadores}. "
                    "Endereçar explicitamente em toda análise. Não omitir.")
            if rm.condicoes_de_aborto:
                L.append(f"  Condições de aborto: {rm.condicoes_de_aborto}")
            if rm.risk_score_agregado == ImpactLevel.CRITICO:
                warnings.append(
                    "RISK SCORE CRÍTICO: cenário pessimista deve ter prob. >= 15%. "
                    "Não simplificar análise de cenários.")
        else:
            L.append("  [AUSENTE]")
            warnings.append("Mapa de riscos ausente. Análise sem base de risco estruturada.")
        L.append("")

        # BLOCO 5 — Cenários (só E06)
        if target == InjectionTarget.E06_RECOMENDACAO and decision.cenarios:
            sc = decision.cenarios
            L.append("[ CENÁRIOS ANALISADOS ]")
            L.append(f"  Base:       {sc.cenario_base.probabilidade_estimada} — {sc.cenario_base.descricao[:100]}")
            L.append(f"  Otimista:   {sc.cenario_otimista.probabilidade_estimada} — {sc.cenario_otimista.descricao[:100]}")
            L.append(f"  Pessimista: {sc.cenario_pessimista.probabilidade_estimada} — {sc.cenario_pessimista.descricao[:100]}")
            L.append(f"  Recomendado para calibração: {sc.cenario_recomendado_para_decisao}")
            L.append(f"  Ponto de inflexão: {sc.ponto_de_inflexao}")
            L.append("")

        # BLOCO 6 — Instrução de compliance
        L += [
            "[ INSTRUÇÃO DE COMPLIANCE AO AGENTE LLM ]",
            "  1. NÃO reclassifique tipo, impacto ou reversibilidade.",
            "  2. NÃO ignore riscos bloqueadores listados acima.",
            "  3. NÃO subestime probabilidade do cenário pessimista com riscos bloqueadores.",
            "  4. NÃO omita premissas críticas não validadas.",
            "  5. Se divergir dos fatos acima, declare explicitamente o motivo.",
            "  6. A decisão final pertence ao executivo. Estruture — não decida.",
            "",
        ]

        if warnings:
            L.append("[ ALERTAS — EXIBIR AO EXECUTIVO ]")
            for w in warnings:
                L.append(f"  ⚠  {w}")
            L.append("")

        L.append(self.FTR)
        return InjectedFacts(target=target, bloco="\n".join(L), warnings=warnings)

    def inject_into_prompt(self, prompt_template: str, decision: Decision,
                           target: InjectionTarget) -> str:
        facts = self.build(decision, target)
        placeholder = "{FATOS_VERIFICADOS}"
        if placeholder in prompt_template:
            return prompt_template.replace(placeholder, facts.bloco)
        return facts.bloco + "\n\n" + prompt_template
