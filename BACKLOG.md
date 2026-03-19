# BACKLOG.md — Mentor C-Level

> Arquivo vivo. Registra gaps, decisões adiadas e itens pendentes de especificação.
> Atualizado a cada sessão de desenvolvimento. Lido pelo Claude Code junto ao CLAUDE.md.

---

## Status Legend

| Status | Significado |
|--------|-------------|
| `PENDENTE` | Identificado, não especificado |
| `ESPECIFICADO` | Prompt ou spec criada, aguarda dev |
| `EM DEV` | Em desenvolvimento ativo |
| `CONCLUIDO` | Implementado e validado |
| `BLOQUEADO` | Depende de outro item |

---

## Backlog Ativo

### BKL-001 — Módulo de Maturidade Decisória
**Status:** `PENDENTE`
**Prioridade:** Alta
**Origem:** Análise de benchmarking Decision Intelligence (março 2026)

O conceito de maturidade decisória está ausente das especificações atuais. Antes de aplicar o protocolo, a organização precisa ser diagnosticada em pilares como governança de dados, cultura data-driven e accountability decisória. Isso implica um módulo de onboarding diagnóstico que o Mentor C-Level ainda não tem — e deveria ter para calibrar o enforcement proporcional.

**Escopo esperado:**
- Diagnóstico por pilares (governança de dados, cultura data-driven, accountability decisória, estrutura de processos decisórios)
- Score de maturidade por pilar
- Calibração do nível de enforcement do protocolo (uso voluntário → enforcement por impacto)
- Relatório de gaps com roadmap priorizado

**Dependências:** nenhuma
**Arquivo de spec:** `prompts/backlog/BKL-001_maturity_module_spec.md` *(a criar)*

---

### BKL-002 — Quality Gate Inter-Etapas
**Status:** `PENDENTE`
**Prioridade:** Alta
**Origem:** Benchmarking TaxMind Light (março 2026)

O protocolo de 8 etapas é sequencial mas não tem gate de qualidade entre etapas. Antes de avançar para Etapa 06 (recomendação), um gate determinístico deve verificar:
- Número mínimo de premissas explicitadas (≥ 3 para impacto ELEVADO/CRITICO)
- Número mínimo de riscos mapeados (≥ 5 para CRITICO, ≥ 3 para MODERADO)
- Cenário pessimista com probabilidade ≥ 15% quando há risco bloqueador
- Premissas críticas não validadas sinalizadas como bloqueadoras

Se gate falha → sistema recusa avançar e retorna à etapa deficiente com indicação do critério não atendido.

**Dependências:** nenhuma
**Arquivo de spec:** `prompts/backlog/BKL-002_quality_gate_spec.md` *(a criar)*

---

### BKL-003 — Injeção de Fatos Verificados Pré-LLM
**Status:** `PENDENTE`
**Prioridade:** Alta
**Origem:** Benchmarking TaxMind Light — padrão `[CALCULOS VERIFICADOS]` (março 2026)

O engine determinístico deve injetar fatos calculados como contexto fixo nos prompts das Etapas 05 e 06, antes da chamada ao LLM. Isso impede que o LLM reclassifique a decisão ou ignore riscos bloqueadores já mapeados.

**Formato esperado de injeção:**
```
[FATOS VERIFICADOS PELO ENGINE — NÃO RECLASSIFICAR]
Tipo: ESTRUTURA_FINANCEIRA
Impacto: ELEVADO
Premissas não validadas: 3 (2 de criticidade ALTA)
Riscos bloqueadores: R2, R4
Risk score agregado: CRITICO
Cenário recomendado: PESSIMISTA
```

**Dependências:** BKL-002 (quality gate deve ser executado antes da injeção)
**Arquivo de spec:** `prompts/backlog/BKL-003_fact_injection_spec.md` *(a criar)*

---

### BKL-004 — Feedback Loop E08 → E01 (Calibração de Confiança)
**Status:** `PENDENTE`
**Prioridade:** Média
**Origem:** Benchmarking TaxMind Light — feedback loop por `prompt_version` (março 2026)

Desvios significativos registrados na Etapa 08 devem retroalimentar o calibrador de confiança do classificador (E01). Se o sistema declarou `nivel_confianca = ALTO` e o resultado foi `desvio.magnitude = SIGNIFICATIVO`, esse par deve ser registrado como caso de recalibração.

**Lógica esperada:**
- `desvio SIGNIFICATIVO + nivel_confianca ALTO` → flag de superestimação de confiança
- `desvio DESPREZIVEL + nivel_confianca BAIXO` → flag de subestimação
- Acúmulo de flags → ajuste nos thresholds do `classifier.py`

**Dependências:** Etapa 08 implementada + volume mínimo de decisões registradas
**Arquivo de spec:** `prompts/backlog/BKL-004_feedback_loop_spec.md` *(a criar)*

---

### BKL-005 — Corpus Decisório Vetorizado (RAG Fase 2)
**Status:** `PENDENTE`
**Prioridade:** Baixa (fase futura)
**Origem:** Benchmarking TaxMind Light — arquitetura RAG de produção (março 2026)

Quando o histórico de decisões registradas na Etapa 07 acumular volume suficiente, o banco de decisões passadas vira corpus recuperável. O LLM passa a ancorar recomendações em decisões históricas similares em vez de operar por memória de treinamento.

**Pré-requisito de ativação:** mínimo de 50 decisões registradas no sistema
**Stack esperada:** PostgreSQL + pgvector, embeddings Voyage-3, busca híbrida (dense + BM25)
**Referência técnica:** `briefing_taxmind_rag.md` (arquivo de benchmarking)

**Dependências:** volume de dados (BKL não tem data de início definida)
**Arquivo de spec:** `prompts/backlog/BKL-005_rag_corpus_spec.md` *(a criar quando pré-requisito atendido)*

---

### BKL-006 — Expansão APQC: Domínios Pós-CFO
**Status:** `PENDENTE`
**Prioridade:** Baixa (pós-MVP)
**Origem:** Decisão de escopo APQC completo (março 2026)

Após validação do MVP no Domínio 9 (CFO), expansão sequencial:

| Fase | Domínios | C-Level Alvo |
|------|----------|--------------|
| Fase 2 | 1.0, 2.0, 3.0 | CEO / COO |
| Fase 3 | 7.0 | CHRO |
| Fase 4 | 8.0 | CTO / CIO |
| Fase 5 | 11.0 | CRO |
| Fase 6 | 4.0, 5.0, 6.0, 10.0, 12.0, 13.0 | COO / demais |

Cada fase requer: atualização do classificador (novos padrões de vocabulário), novos defaults de impacto/reversibilidade por tipo de decisão, e prompts calibrados para o domínio.

**Dependências:** MVP validado com simulação retrospectiva bem-sucedida
**Arquivo de spec:** a criar por fase

---

## Itens Concluídos

| ID | Item | Data |
|----|------|------|
| — | Schema Pydantic `decision.py` | Mar/2026 |
| — | Engine classificador `classifier.py` | Mar/2026 |
| — | Prompts E01–E08 + aux_game_theory | Mar/2026 |
| — | `CLAUDE.md` + `briefing.md` | Mar/2026 |
