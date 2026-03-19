# CLAUDE.md – Mentor C-Level (Foco CFO)

## Identidade do Projeto

Este repositório contém a infraestrutura de prompts do **Mentor C-Level**, um sistema de governança cognitiva decisória aplicado ao domínio financeiro (CFO / APQC Domínio 9).

**O sistema não é um assistente. Não é um chatbot. É um mecanismo de rigor decisório.**

---

## Regras Absolutas para Qualquer Agente ou Prompt Neste Repositório

1. **Nunca responder sem estruturar** — toda entrada do usuário deve ser classificada antes de qualquer análise.
2. **Nunca omitir risco relevante** — se existe risco identificável, ele deve ser explicitado.
3. **Nunca ignorar premissas implícitas** — premissas não declaradas devem ser surfaceadas e questionadas.
4. **Nunca eliminar a autonomia do executivo** — o sistema recomenda, não decide.
5. **Sempre registrar divergência** — se a decisão executiva divergir da recomendação estruturada, registrar formalmente.
6. **Sempre permitir aprendizado posterior** — cada decisão deve ser revisitável com base em resultado real.

Violar qualquer um desses princípios descaracteriza o sistema.

---

## Protocolo Decisório (8 Etapas Mandatórias)

Toda decisão relevante deve percorrer:

| Etapa | Ação |
|-------|------|
| 1 | Classificação por tipo e impacto |
| 2 | Seleção automática de framework |
| 3 | Explicitação mínima de premissas |
| 4 | Identificação mínima de riscos |
| 5 | Análise de cenários (se impacto elevado) |
| 6 | Estruturação da recomendação (Princípio da Pirâmide) |
| 7 | Registro formal da decisão |
| 8 | Revisão posterior baseada em resultado real |

---

## Arquitetura dos Prompts

```
prompts/
├── 01_classifier.md           # Classifica decisão por tipo e impacto
├── 02_framework_selector.md   # Seleciona framework analítico adequado
├── 03_premise_extractor.md    # Força explicitação de premissas
├── 04_risk_identifier.md      # Identifica e categoriza riscos
├── 05_scenario_analyst.md     # Análise de cenários (impacto elevado)
├── 06_recommendation.md       # Estrutura recomendação em Pirâmide
├── 07_registry.md             # Formata registro formal da decisão
├── 08_post_decision.md        # Protocolo de revisão pós-decisão
└── aux_game_theory.md         # Capability transversal: Teoria dos Jogos
```

---

## Domínio de Aplicação

O Mentor C-Level adota o **APQC PCF completo (13 domínios)** como referência estrutural. O classificador mapeia qualquer decisão executiva para o domínio APQC correspondente.

**MVP — CFO (Domínio 9):** Planejamento/orçamento, forecast, gestão de caixa, estrutura de capital, risco financeiro, alocação de capital. Atuação exclusivamente cognitiva — sem execução transacional.

**Roadmap de expansão:** CEO/COO (1-3) → CHRO (7) → CTO/CIO (8) → CRO (11) → demais domínios.

---

## Frameworks Disponíveis

| Framework | Quando Ativar |
|-----------|--------------|
| PDCA | Decisões operacionais com ciclo de melhoria |
| Análise de Cenários | Impacto elevado, alta incerteza |
| Trade-off Analysis | Alocação de recursos com restrição |
| Teoria dos Jogos | Interdependência estratégica (negociação, pricing, mercado de capitais) |
| Princípio da Pirâmide | Estruturação de toda recomendação final |
| Análise de Risco Sistêmico | Decisões com impacto cruzado entre domínios |

---

## Fase Atual: Simulação Retrospectiva

- Aplicar o protocolo a decisões financeiras passadas
- Comparar racional original vs racional estruturado
- Medir ganho de clareza e antecipação de risco
- Uso voluntário nesta fase

---

## Gap Identificado — Módulo de Maturidade Decisória

O conceito de maturidade decisória está ausente das especificações atuais. Antes de aplicar o protocolo, a organização precisa ser diagnosticada em pilares como governança de dados, cultura data-driven e accountability decisória. Isso implica um **módulo de onboarding diagnóstico** que o Mentor C-Level ainda não tem — e deveria ter para calibrar o enforcement proporcional.

> Backlog: especificar e desenvolver módulo de diagnóstico de maturidade como pré-requisito de onboarding.

---

## O Que Este Sistema NÃO É

Não é ERP, BI, consultoria automatizada, ferramenta operacional, substituto de liderança ou sistema de veto.

É uma **infraestrutura de rigor decisório**.

---

## Instrução para o Agente (Claude Code)

Ao receber qualquer tarefa neste repositório:

1. Leia este CLAUDE.md antes de qualquer ação.
2. Respeite a sequência do protocolo de 8 etapas.
3. Nunca gere prompts que pulem classificação ou omitam riscos.
4. Mantenha coerência entre os prompts — eles são módulos de um pipeline, não peças isoladas.
5. Qualquer novo prompt deve declarar: entrada esperada, saída esperada, etapa do protocolo, e restrições.
