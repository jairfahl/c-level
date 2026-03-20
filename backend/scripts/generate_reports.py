#!/usr/bin/env python3
"""
generate_reports.py — P-09 Comparison Report Generator

Reads cases/results/case_0X.json and cases/simulation_cases.json to
produce per-case comparison reports and a consolidated executive report.

Outputs:
  cases/reports/report_{name}.md   (5 files)
  cases/reports/consolidated_report.md

Usage:
    .venv/bin/python scripts/generate_reports.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


FRAMEWORK_LABELS = {
    "pdca":             "PDCA (Plan-Do-Check-Act)",
    "scenario_analysis":"Análise de Cenários",
    "game_theory":      "Teoria dos Jogos",
    "trade_off":        "Análise de Trade-Off",
    "risk_matrix":      "Matriz de Riscos",
    "capital_allocation":"Alocação de Capital",
}

CASE_SLUGS = {
    1: "case01_reialocacao_orcamentaria",
    2: "case02_renegociacao_ccbs",
    3: "case03_gestao_liquidez",
    4: "case04_capex_recife",
    5: "case05_revisao_forecast",
}


def _md_list(items: list[str]) -> str:
    return "\n".join(f"- {i}" for i in items) if items else "_Nenhum_"


def _currency(val: float) -> str:
    if val >= 1_000_000:
        return f"R$ {val / 1_000_000:,.1f}M"
    if val >= 1_000:
        return f"R$ {val / 1_000:,.0f}k"
    return f"R$ {val:,.2f}"


def generate_individual_report(case_num: int, sim_case: dict, result: dict) -> str:
    """Return the Markdown content for a single Comparison Report."""

    label    = sim_case.get("_label", "")
    title    = sim_case["title"]
    sim      = sim_case["_simulation"]

    analyzed  = result["analyzed"]
    classified = result["classified"]
    structured = result["structured"]
    decided    = result["decided"]
    historical = result["historical_reference"]

    framework_key   = classified["framework_selected"]
    framework_label = FRAMEWORK_LABELS.get(framework_key, framework_key)
    exposure        = sim_case["financial_exposure"]
    domain          = sim_case["financial_domain"]
    decision_type   = sim_case["decision_type"]
    external        = sim_case["external_agents_present"]
    time_horizon    = sim_case.get("time_horizon", "não especificado")
    scenario_req    = classified["scenario_required"]
    game_theory     = classified["game_theory_active"]

    recommendation  = analyzed["recommendation"]
    metrics         = analyzed["financial_metrics_impacted"]
    scenario_sum    = analyzed.get("scenario_summary")
    implicit_ass    = analyzed.get("implicit_assumptions_found", [])
    gt_model        = analyzed.get("game_theory_model")
    llm_flag        = analyzed.get("llm_unavailable", False)

    stated_assumptions = structured["assumptions"]
    stated_risks       = structured["risks"]

    original_rationale = historical.get("original_rationale", "")
    decision_taken     = historical.get("decision_taken", "")
    actual_outcome     = historical.get("actual_outcome", "")

    exec_decision = decided["executive_decision"]

    # ── Delta calculations (Section C) ───────────────────────────────────────
    # Premissas adicionais = implicit_assumptions_found by LLM
    premissas_adicionais = len(implicit_ass)
    # Riscos adicionais: we consider all structured risks as explicit;
    # no new risks from LLM in this flow (risks are CFO-supplied)
    riscos_adicionais = 0
    # Cenários gerados: 1 if scenario_summary is populated
    cenarios_gerados = 1 if scenario_sum else 0
    # Divergência: check if decision diverges from recommendation
    divergencia = decided.get("divergence_flag", False)
    # score_clareza_executivo: to be filled after reading
    score_clareza = "⬜ _Preencher após leitura (escala 1–5)_"

    llm_mode = "LLM indisponível — análise em modo determinístico" if llm_flag else "Claude (Anthropic)"

    # ── Game Theory block ─────────────────────────────────────────────────────
    gt_block = ""
    if game_theory and gt_model:
        players_list = "\n".join(f"- {p}" for p in gt_model.get("players", []))
        equilibrium  = gt_model.get("equilibrium", "N/A")
        strat_risk   = gt_model.get("strategic_risk", "N/A")
        payoffs_str  = ""
        for k, v in gt_model.get("payoffs", {}).items():
            payoffs_str += f"\n  - **{k}**: {v}"

        strategies_str = ""
        for player, strats in gt_model.get("strategies", {}).items():
            strategies_str += f"\n  - **{player}**: " + " | ".join(strats)

        gt_block = f"""
#### Modelo de Teoria dos Jogos

**Players identificados:**
{players_list}

**Estratégias por agente:**{strategies_str}

**Payoffs estimados:**{payoffs_str}

**Equilíbrio de Nash / Estratégia dominante:**
> {equilibrium}

**Risco estratégico:**
> {strat_risk}
"""

    # ── Scenario block ────────────────────────────────────────────────────────
    scenario_block = ""
    if scenario_sum:
        scenario_block = f"""
#### Análise de Cenários (scenario_required = true)

{scenario_sum}
"""

    # ── Implicit assumptions block ────────────────────────────────────────────
    implicit_block = ""
    if implicit_ass:
        implicit_list = "\n".join(f"{i+1}. {a}" for i, a in enumerate(implicit_ass))
        implicit_block = f"""
#### Premissas Implícitas Capturadas pelo Mentor

{implicit_list}
"""

    # ── Build the full report ─────────────────────────────────────────────────
    report = f"""# Comparison Report — Caso {case_num:02d}
## {title}

| Campo | Valor |
|---|---|
| Label | {label} |
| Domínio | {domain} |
| Tipo de Decisão | {decision_type} |
| Exposição Financeira | {_currency(exposure)} |
| Horizonte Temporal | {time_horizon} |
| Agentes Externos | {"Sim" if external else "Não"} |
| Framework Selecionado | {framework_label} |
| Cenário Obrigatório | {"Sim" if scenario_req else "Não"} |
| Teoria dos Jogos | {"Ativa" if game_theory else "Não ativa"} |
| Impacto Score | {classified['impact_score']}/5 |
| Modo de Análise LLM | {llm_mode} |

---

## Seção A — Racional Original (pré-Mentor)

### A.1 Justificativa Original

{original_rationale}

### A.2 Decisão Tomada (histórico)

{decision_taken}

### A.3 Resultado Real

{actual_outcome}

### A.4 Premissas Identificadas no Racional Original

As premissas abaixo foram declaradas explicitamente pelo CFO antes da estruturação pelo Mentor:

{_md_list(stated_assumptions)}

### A.5 Riscos Mencionados no Racional Original

Os riscos abaixo foram fornecidos pelo CFO como insumo da estruturação:

{_md_list(stated_risks)}

---

## Seção B — Racional Estruturado pelo Mentor CFO

### B.1 Framework Analítico Aplicado

**{framework_label}**

O framework foi selecionado automaticamente pela engine determinística com base em:
- Tipo de decisão: `{decision_type}`
- Agentes externos presentes: `{external}`
- Exposição financeira: `{_currency(exposure)}` (impact score = {classified['impact_score']}/5)

### B.2 Recomendação Estruturada

{recommendation}

### B.3 Métricas Financeiras Impactadas

{_md_list(metrics)}
{implicit_block}{scenario_block}{gt_block}
### B.4 Decisão Executiva Registrada

> {exec_decision}

**Divergência da recomendação do Mentor:** {"Sim — justificativa registrada" if divergencia else "Não — decisão alinhada com a recomendação"}

---

## Seção C — Delta de Qualidade

| Dimensão | Valor | Observação |
|---|---|---|
| Premissas adicionais identificadas pelo Mentor | **{premissas_adicionais}** | Premissas implícitas não declaradas pelo CFO |
| Riscos adicionais estruturados | **{riscos_adicionais}** | Riscos já fornecidos pelo CFO como insumo |
| Cenários gerados (pessimista/base/otimista) | **{cenarios_gerados}** | {"Análise de cenários aplicada" if cenarios_gerados else "Não obrigatório para este caso (impact_score < 4)"} |
| Divergência registrada | **{"Sim" if divergencia else "Não"}** | {"CFO divergiu da recomendação do Mentor" if divergencia else "CFO acatou a recomendação do Mentor"} |
| Score de clareza executivo (1–5) | {score_clareza} | Avaliação subjetiva do Arquiteto após leitura |

### C.1 Avaliação Qualitativa

- **Cobertura de premissas:** {len(stated_assumptions)} premissas declaradas + {premissas_adicionais} implícitas capturadas = {len(stated_assumptions) + premissas_adicionais} total
- **Rigor de riscos:** {len(stated_risks)} riscos identificados e estruturados pelo CFO
- **Profundidade analítica:** {"Alta — análise de cenários + " + ("Teoria dos Jogos" if game_theory else "framework quantitativo") if scenario_req else "Moderada — framework sem análise de cenários obrigatória"}
- **Alinhamento decisório:** {"ALINHADO — CFO acatou a recomendação integral do Mentor" if not divergencia else "DIVERGENTE — CFO registrou justificativa de divergência"}

---

_Relatório gerado automaticamente por `scripts/generate_reports.py` — {Path(__file__).name}_
_Caso ID: {result['case_id']}_
"""
    return report.strip()


def generate_consolidated_report(sim_cases: list[dict], results: list[dict]) -> str:
    """Generate the consolidated executive report with Go/No-Go."""

    total_cases = len(results)
    total_explicit_assumptions = sum(
        len(r["structured"]["assumptions"]) for r in results
    )
    total_implicit_assumptions = sum(
        len(r["analyzed"].get("implicit_assumptions_found", [])) for r in results
    )
    total_risks = sum(
        len(r["structured"]["risks"]) for r in results
    )
    total_scenarios = sum(
        1 for r in results if r["analyzed"].get("scenario_summary")
    )
    total_game_theory = sum(
        1 for r in results if r["classified"]["game_theory_active"]
    )
    divergencias = sum(
        1 for r in results if r["decided"].get("divergence_flag", False)
    )
    alignment_rate = round((total_cases - divergencias) / total_cases * 100)
    llm_fallback = sum(
        1 for r in results if r["analyzed"].get("llm_unavailable", False)
    )

    # Per-case summary rows
    case_rows = ""
    for i, (sc, res) in enumerate(zip(sim_cases, results)):
        sim       = sc["_simulation"]
        cls_      = res["classified"]
        analyzed  = res["analyzed"]
        decided   = res["decided"]
        n_implicit = len(analyzed.get("implicit_assumptions_found", []))
        framework  = FRAMEWORK_LABELS.get(cls_["framework_selected"], cls_["framework_selected"])
        diverge    = "Sim" if decided.get("divergence_flag") else "Não"
        scenario   = "Sim" if analyzed.get("scenario_summary") else "Não"
        outcome_score = sc.get("_simulation", {}).get("review_payload", {}).get("forecast_accuracy_score", "—")
        case_rows += (
            f"| {i+1:02d} | {sc['title'][:45]} | {_currency(sc['financial_exposure'])} "
            f"| {cls_['impact_score']}/5 | {framework[:30]} | {n_implicit} | {scenario} | {diverge} "
            f"| {outcome_score}/10 |\n"
        )

    # Go/No-Go decision logic
    # Criteria:
    # ✅ PASS: alignment ≥ 80%, implicit assumptions found in ≥ 3 cases, scenarios in ≥ 2 high-impact cases
    criteria_alignment    = alignment_rate >= 80
    criteria_implicit     = total_implicit_assumptions >= 3
    criteria_scenarios    = total_scenarios >= 2
    criteria_game_theory  = total_game_theory >= 1
    criteria_no_fallback  = llm_fallback == 0

    passed_criteria = sum([
        criteria_alignment, criteria_implicit, criteria_scenarios,
        criteria_game_theory, criteria_no_fallback
    ])

    if passed_criteria >= 4:
        go_no_go = "✅ GO"
        go_verdict = "O Mentor CFO demonstrou qualidade analítica suficiente para enforcement no protocolo decisório."
        go_colour  = "GO"
    elif passed_criteria == 3:
        go_no_go = "⚠️ GO CONDICIONAL"
        go_verdict = "Critérios parcialmente satisfeitos. Recomenda-se revisão manual dos casos com divergência antes do enforcement."
        go_colour  = "GO CONDICIONAL"
    else:
        go_no_go = "❌ NO-GO"
        go_verdict = "Critérios mínimos não satisfeitos. Não recomendado para enforcement sem ajustes na configuração do Mentor."
        go_colour  = "NO-GO"

    def crit(ok: bool, label: str, detail: str) -> str:
        sym = "✅" if ok else "❌"
        return f"| {sym} | {label} | {detail} |"

    criteria_table = "\n".join([
        crit(criteria_alignment,   "Alinhamento CFO ≥ 80%",                    f"{alignment_rate}% ({total_cases - divergencias}/{total_cases} casos alinhados)"),
        crit(criteria_implicit,    "Premissas implícitas capturadas (≥ 3)",     f"{total_implicit_assumptions} premissas implícitas em {total_cases} casos"),
        crit(criteria_scenarios,   "Cenários gerados em casos impact ≥ 4 (≥ 2)",f"{total_scenarios} cenários gerados"),
        crit(criteria_game_theory, "Teoria dos Jogos ativa em pelo menos 1 caso",f"{total_game_theory} casos com game_theory ativo"),
        crit(criteria_no_fallback, "LLM real sem fallback em todos os casos",   f"{'0 fallbacks' if llm_fallback == 0 else str(llm_fallback) + ' fallback(s) detectado(s)'}"),
    ])

    report = f"""# Consolidated Report — MVP Simulation
## CFO Mentor | Fases 5.2–5.3 | Execução dos 5 Casos Históricos

---

## Sumário Executivo

| Métrica | Valor |
|---|---|
| Total de casos simulados | {total_cases} |
| Casos com alinhamento CFO/Mentor | {total_cases - divergencias}/{total_cases} ({alignment_rate}%) |
| Premissas declaradas (total) | {total_explicit_assumptions} |
| Premissas implícitas capturadas pelo Mentor | {total_implicit_assumptions} |
| Riscos estruturados (total) | {total_risks} |
| Cenários gerados (cases com impact_score ≥ 4) | {total_scenarios} |
| Casos com Teoria dos Jogos ativa | {total_game_theory} |
| Divergências registradas | {divergencias} |
| Casos em fallback determinístico | {llm_fallback} |

---

## Tabela de Casos

| # | Título | Exposição | Score | Framework | Implícitas | Cenários | Divergência | Acurácia |
|---|---|---|---|---|---|---|---|---|
{case_rows}

---

## Métricas Agregadas

### Cobertura Analítica

- **Premissas totais cobertas:** {total_explicit_assumptions} declaradas + {total_implicit_assumptions} implícitas = **{total_explicit_assumptions + total_implicit_assumptions} total**
- **Taxa de captura implícita:** {total_implicit_assumptions}/{total_explicit_assumptions + total_implicit_assumptions} = {round(total_implicit_assumptions / (total_explicit_assumptions + total_implicit_assumptions) * 100)}% das premissas foram capturadas pelo Mentor sem declaração explícita do CFO
- **Rigor de riscos:** {total_risks} riscos estruturados em {total_cases} casos (média de {total_risks / total_cases:.1f} riscos/caso)
- **Profundidade analítica:** {total_scenarios}/{total_cases} casos com análise de cenários completa (pessimista/base/otimista)

### Alinhamento Decisório

- **Taxa de alinhamento CFO/Mentor:** {alignment_rate}%
- **Interpretação:** O CFO acatou a recomendação do Mentor em {total_cases - divergencias} dos {total_cases} casos — indicador de **{"alta" if alignment_rate >= 80 else "moderada" if alignment_rate >= 60 else "baixa"} qualidade de recomendação** e confiança na metodologia estruturada.

### Qualidade LLM

- **Modo de análise:** {"Claude Sonnet (Anthropic API)" if llm_fallback == 0 else f"Misto — {total_cases - llm_fallback} Claude + {llm_fallback} fallback determinístico"}
- **Fallbacks acionados:** {llm_fallback}/{total_cases}

---

## Seção C — Delta de Qualidade Agregado

| Dimensão | Resultado | Benchmark Esperado | Status |
|---|---|---|---|
| Premissas implícitas / caso | {total_implicit_assumptions / total_cases:.1f} | ≥ 2,0 | {"✅" if total_implicit_assumptions / total_cases >= 2 else "⚠️"} |
| Riscos identificados / caso | {total_risks / total_cases:.1f} | ≥ 3,0 | {"✅" if total_risks / total_cases >= 3 else "⚠️"} |
| Cenários em casos críticos | {total_scenarios}/{sum(1 for r in results if r['classified']['impact_score'] >= 4)} | 100% dos impact ≥ 4 | {"✅" if total_scenarios >= sum(1 for r in results if r['classified']['impact_score'] >= 4) else "⚠️"} |
| Taxa de alinhamento CFO | {alignment_rate}% | ≥ 80% | {"✅" if alignment_rate >= 80 else "❌"} |
| Cobertura de Game Theory | {total_game_theory}/{total_cases} | ≥ 2 casos elegíveis | {"✅" if total_game_theory >= 2 else "⚠️"} |

---

## Go/No-Go para Enforcement

### Critérios de Avaliação

| Status | Critério | Resultado |
|---|---|---|
{criteria_table}

### Veredicto Final

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│   DECISÃO DE ENFORCEMENT:  {go_colour:<28} │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**{go_no_go}** — {go_verdict}

### Recomendações para Próximas Fases

1. **Enforcement do Protocolo Decisório:** {'Habilitar o Mentor CFO como etapa obrigatória no fluxo de aprovação de decisões com exposição > R$ 2M (impact_score ≥ 4).' if go_colour == 'GO' else 'Revisar os critérios não satisfeitos antes de habilitar o enforcement.'}

2. **Score de Clareza Executivo:** Preencher o campo `score_clareza_executivo` (1–5) em cada relatório individual após leitura. Este score é o único campo que requer avaliação subjetiva do Arquiteto — todos os demais são gerados automaticamente.

3. **Calibração de Premissas Implícitas:** Com {total_implicit_assumptions} premissas implícitas capturadas em {total_cases} casos, o Mentor demonstra capacidade de explicitação além do input do CFO. Recomenda-se institucionalizar a lista de premissas implícitas como insumo para revisões de forecast.

4. **Divergências Registradas:** {f'Nenhuma divergência detectada — o CFO acatou integralmente as recomendações do Mentor em todos os casos.' if divergencias == 0 else f'{divergencias} divergência(s) detectada(s) — revisar os casos correspondentes para entender os vetores de discordância CFO/Mentor e calibrar o modelo.'}

5. **Próxima Fase (P-10):** Implementar o ciclo completo DECIDED → UNDER_REVIEW → CLOSED com preenchimento dos `review_payload` para fechar o loop de aprendizado do Mentor com dados reais de outcome.

---

_Relatório gerado automaticamente por `scripts/generate_reports.py`_
_Fase: 5.2–5.3 | Data: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')} | Casos: {total_cases}_
"""
    return report.strip()


def main() -> None:
    results_dir = ROOT / "cases" / "results"
    reports_dir = ROOT / "cases" / "reports"
    cases_path  = ROOT / "cases" / "simulation_cases.json"
    reports_dir.mkdir(parents=True, exist_ok=True)

    with cases_path.open(encoding="utf-8") as fh:
        sim_cases: list[dict] = json.load(fh)

    results = []
    for case_num in range(1, 6):
        path = results_dir / f"case_{case_num:02d}.json"
        with path.open(encoding="utf-8") as fh:
            results.append(json.load(fh))

    print(f"\033[1mCFO Mentor — Comparison Report Generator\033[0m")
    print(f"Cases   : {len(sim_cases)}")
    print(f"Reports : {reports_dir}\n")

    # ── Individual reports ────────────────────────────────────────────────────
    for i, (sc, res) in enumerate(zip(sim_cases, results)):
        case_num = sc["_case_id"]
        slug     = CASE_SLUGS[case_num]
        content  = generate_individual_report(case_num, sc, res)
        out_path = reports_dir / f"report_{slug}.md"
        out_path.write_text(content, encoding="utf-8")
        print(f"  \033[0;32m✓\033[0m {out_path.relative_to(ROOT)}")

    # ── Consolidated report ───────────────────────────────────────────────────
    consolidated = generate_consolidated_report(sim_cases, results)
    cons_path = reports_dir / "consolidated_report.md"
    cons_path.write_text(consolidated, encoding="utf-8")
    print(f"  \033[0;32m✓\033[0m {cons_path.relative_to(ROOT)}")

    print(f"\n\033[0;32m\033[1m{'═' * 54}\033[0m")
    print(f"\033[0;32m\033[1m  Reports generated: {len(sim_cases)} individual + 1 consolidated\033[0m")
    print(f"\033[0;32m\033[1m{'═' * 54}\033[0m\n")


if __name__ == "__main__":
    main()
