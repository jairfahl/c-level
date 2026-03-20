# Mentor C-Level — Plano de Trabalho Completo
> Versão 2.0 | Março 2026 | Foco inicial: CFO

---

## Sumário

1. [Estrutura de Fases](#1-estrutura-de-fases)
2. [Conteúdo de Cada Fase](#2-conteúdo-de-cada-fase)
3. [Interdependências](#3-interdependências)
4. [Matriz RACI](#4-matriz-raci)
5. [Biblioteca de Prompts](#5-biblioteca-de-prompts)

---

## 1. Estrutura de Fases

```
FASE 0   Definição Estratégica         ████████████████████  [CONCLUÍDA]
FASE 1   Arquitetura Conceitual        ████████████████████  [CONCLUÍDA]
FASE 2   Especificação Funcional       ████████████████████  [CONCLUÍDA]
FASE 3   Arquitetura Técnica           ████████████████████  [CONCLUÍDA]
FASE 4   Core Engine Development       ████████████████████  [CONCLUÍDA]
FASE 5   MVP Simulation                ████████████████████  [CONCLUÍDA]
FASE 6   Learning Module               ████████████████████  [CONCLUÍDA]
FASE 7   Frontend React                ████████████████████  [CONCLUÍDA]
FASE 8   Knowledge Base                ████████████████████  [CONCLUÍDA]
FASE 9   Inteligência Decisória        ████████████████████  [CONCLUÍDA]
FASE 10  Anti-Terceirização Cognitiva  ████████████████████  [CONCLUÍDA]
FASE 11  KB Enhancement + API Balance ████████████████████  [CONCLUÍDA]
```

---

## 2. Conteúdo de Cada Fase

### FASE 0 — Definição Estratégica ✅

**Objetivo:** Fixar propósito, escopo e critérios de sucesso do MVP CFO.

| Entregável | Status |
|---|---|
| Escopo do domínio financeiro (APQC D9) | ✅ |
| Critérios de sucesso quantitativos e qualitativos | ✅ |
| Restrições não-funcionais | ✅ |
| Metodologia de medição de ganho cognitivo | ✅ |

---

### FASE 1 — Arquitetura Conceitual ✅

**Objetivo:** Definir o modelo híbrido (engine determinística + LLM) e os 5 módulos core.

| Entregável | Status |
|---|---|
| Modelo híbrido engine determinística + LLM | ✅ |
| 5 módulos core definidos | ✅ |
| Fluxo de dados entre módulos | ✅ |
| Diagrama textual do motor | ✅ |
| Alinhamento APQC 9.1–9.5 | ✅ |

---

### FASE 2 — Especificação Funcional ✅

**Objetivo:** Definir o modelo de dados completo, tipos de decisão e regras de validação.

| Entregável | Status |
|---|---|
| Modelo de dados FinancialDecisionCase | ✅ |
| 8 decision types mapeados | ✅ |
| Mapeamento decision_type → framework | ✅ |
| Máquina de estados (8 estados) | ✅ |
| Regras de validação do protocolo | ✅ |

---

### FASE 3 — Arquitetura Técnica ✅

**Objetivo:** Decidir stack, segurança, cache e estrutura de diretórios.

| Entregável | Status |
|---|---|
| Stack: FastAPI + PostgreSQL 15+ | ✅ |
| Schema SQL v2 completo | ✅ |
| Contrato OpenAPI 3.0 v2 em YAML | ✅ |
| Estratégia de autenticação JWT | ✅ |
| Estratégia de cache Redis | ✅ |
| Estrutura de diretórios do projeto | ✅ |

---

### FASE 4 — Core Engine Development ✅

**Objetivo:** Construir o backend funcional com engine determinística, camada LLM e API REST.

| Entregável | Status | Testes |
|---|---|---|
| Projeto FastAPI scaffolded | ✅ | — |
| Docker Compose funcional (app + postgres + redis) | ✅ | — |
| Schema v2 aplicado via Alembic | ✅ | — |
| Modelos SQLAlchemy (9 tabelas) | ✅ | — |
| Schemas Pydantic v2 (30+ schemas) | ✅ | 73 testes |
| Engine determinística completa | ✅ | 108 testes |
| Camada LLM integrada (Claude + Cache + Fallback) | ✅ | 76 testes |
| API REST todos endpoints | ✅ | 54 testes |
| Autenticação JWT | ✅ | — |
| Cache Redis | ✅ | — |
| Fluxo end-to-end | ✅ | 20 testes |
| Cobertura de testes | ✅ | 99% |

---

### FASE 5 — MVP Simulation ✅

**Objetivo:** Validar o conceito com 5 decisões financeiras históricas reais.

| Entregável | Status |
|---|---|
| 5 casos históricos documentados | ✅ |
| 5 casos processados pelo Mentor | ✅ |
| 5 Comparison Reports gerados | ✅ |
| Relatório consolidado de resultados | ✅ |
| Go/No-Go para enforcement por impacto | ✅ GO |

**Resultado:** 100% de alinhamento CFO/Mentor, 16 premissas implícitas capturadas, 0 fallbacks.

---

### FASE 6 — Learning Module ✅

**Objetivo:** Fechar o ciclo com revisão pós-decisão e registro de heurísticas.

| Entregável | Status | Testes |
|---|---|---|
| Endpoint de review funcional | ✅ | — |
| Métricas pós-decisão armazenadas | ✅ | — |
| Registro manual de heurísticas | ✅ | — |
| Geração automática de heurísticas | ✅ | — |
| Trigger de review (90 dias) | ✅ | 47 testes |
| 3 heurísticas reais aprendidas | ✅ | — |

---

### FASE 7 — Frontend React ✅

**Objetivo:** Interface web completa para o protocolo decisório.

| Entregável | Status |
|---|---|
| Login com JWT | ✅ |
| Dashboard com lista de casos + criação | ✅ |
| CaseDetail com stepper visual por estado | ✅ |
| ActionPanel com painéis por estado | ✅ |
| Multi-Framework Selection UI | ✅ |
| Heuristics management page | ✅ |
| Knowledge Base management page | ✅ |
| Admin page (pending reviews) | ✅ |
| Intelligence Dashboard com KPIs | ✅ |
| Docker service (porta 3000, proxy → app:8000) | ✅ |

**Stack:** React 18 + Vite + Tailwind CSS + TanStack Query + React Router v6

---

### FASE 8 — Knowledge Base ✅

**Objetivo:** Upload de documentos regulatórios para injeção no contexto LLM.

| Entregável | Status |
|---|---|
| Upload de documentos (PDF/DOCX/TXT) | ✅ |
| Extração automática de texto | ✅ |
| Injeção no prompt LLM por domínio/tipo | ✅ |
| CRUD completo (upload, list, detail, soft-delete) | ✅ |
| Migration 002: knowledge_documents | ✅ |
| Frontend page para gestão | ✅ |

---

### FASE 9 — Inteligência Decisória ✅

**Objetivo:** Dashboard de inteligência com KPIs, alertas e benchmark.

| Entregável | Status |
|---|---|
| Alertas heurísticos por caso | ✅ |
| Benchmark comparativo (casos similares) | ✅ |
| Dashboard KPIs consolidados | ✅ |
| Performance por domínio financeiro | ✅ |
| Resumo de aprendizado institucional (learning-summary) | ✅ |
| Tooltips explicativos nos KPI cards | ✅ |

---

### FASE 10 — Anti-Terceirização Cognitiva ✅

**Objetivo:** Prevenir aceitação passiva de recomendações da IA.

| Mecanismo | Escopo | Status |
|---|---|---|
| P1 — Hipótese pré-recomendação | Backend + Frontend | ✅ |
| P2 — Detecção de rubber-stamping (Jaccard > 0.70) | Frontend only | ✅ |
| P4 — Reconhecimento obrigatório de alertas | Frontend only | ✅ |
| Migration 003: initial_hypothesis | Backend | ✅ |
| Endpoint PUT /hypothesis | Backend | ✅ |
| Campo initial_hypothesis no response | Backend | ✅ |
| Reveal animation no frontend | Frontend | ✅ |
| Hipótese visível em CLOSED (retrospectiva) | Frontend | ✅ |

**Total de testes após Fase 10:** 378+ passando | 99% cobertura

---

### FASE 11 — KB Enhancement + API Balance ✅

**Objetivo:** Expandir formatos da base de conhecimento, validar relevância de documentos e monitorar consumo de créditos API.

| Entregável | Status |
|---|---|
| Suporte a 8 formatos (PDF, DOCX, TXT, XLSX, XLS, PPTX, CSV, MD) | ✅ |
| Extratores: openpyxl (xlsx), python-pptx (pptx), csv stdlib, md | ✅ |
| Migration 004: expand CHECK constraint file_type | ✅ |
| Validador determinístico de relevância (keywords financeiras vs off-topic) | ✅ |
| Endpoint POST /validate-relevance (stateless) | ✅ |
| Integração no upload: confirm_relevance param | ✅ |
| Prompt LLM para validação de relevância | ✅ |
| Redesign UploadModal: drag-and-drop + 2 passos (metadados → relevância) | ✅ |
| Tracking de token usage via Redis (input + output) | ✅ |
| Endpoint GET /admin/api-balance | ✅ |
| Banner de créditos API no Dashboard (âmbar/vermelho) | ✅ |
| CompletionResult com usage no LLMClient | ✅ |
| 15 testes do validador de relevância | ✅ |

**Novas dependências:** openpyxl>=3.1, python-pptx>=0.6.23

**Total de testes após Fase 11:** 405+ passando | 99% cobertura

---

## 3. Interdependências

```
FASE 0 ──────────────────────────────────────────────── BASE ✅
   │
   └──► FASE 1 ✅
             │
             └──► FASE 2 ✅
                       │
                       └──► FASE 3 ✅
                                 │
                                 └──► FASE 4 ✅ (P-01→P-07)
                                           │
                                           ├──► FASE 5 ✅ (P-08, P-09)
                                           │         │
                                           │         └──► FASE 6 ✅ (P-10)
                                           │
                                           ├──► FASE 7 ✅ (P-FE)
                                           │
                                           ├──► FASE 8 ✅ (P-KB)
                                           │
                                           ├──► FASE 9 ✅ (P-INT)
                                           │
                                           ├──► FASE 10 ✅ (P-ACT)
                                           │
                                           └──► FASE 11 ✅ (P-KB2)
```

---

## 4. Matriz RACI

> **R** = Responsável (executa) | **A** = Accountable (aprova) | **C** = Consultado | **I** = Informado

### Papéis

| Papel | Quem |
|---|---|
| **Arquiteto** | Jair (decisões de design, aprovação de arquitetura) |
| **Orquestrador** | Jair + Claude (direcionamento dos prompts, sequência) |
| **Dev Sênior** | Claude Code (implementação, código, testes) |

---

### FASE 0 — Definição Estratégica

| Atividade | Arquiteto | Orquestrador | Dev Sênior |
|---|:---:|:---:|:---:|
| Definir escopo e propósito | A | R | I |
| Definir critérios de sucesso | A | R | C |
| Validar restrições não-funcionais | A | R | I |
| Documentar especificação | I | R | C |

### FASE 4 — Core Engine Development

| Atividade | Arquiteto | Orquestrador | Dev Sênior |
|---|:---:|:---:|:---:|
| Scaffold do projeto FastAPI | I | A | R |
| Configurar Docker + Alembic | I | A | R |
| Implementar State Machine | C | A | R |
| Implementar Framework Selector (11 tipos) | C | A | R |
| Implementar Game Theory Activator | A | C | R |
| Integrar Anthropic Claude API | C | A | R |
| Implementar multi-framework selection | A | C | R |
| Implementar fallback LLM + cache Redis | C | A | R |
| Implementar endpoints API REST (25+) | C | A | R |
| Implementar autenticação JWT | C | A | R |
| Escrever testes (378+) | I | A | R |
| Revisar e aprovar código | A | I | C |

### FASES 7–10 — Frontend, Knowledge Base, Intelligence, Anti-Terceirização

| Atividade | Arquiteto | Orquestrador | Dev Sênior |
|---|:---:|:---:|:---:|
| Frontend React completo | C | A | R |
| Knowledge Base (upload + injection) | A | C | R |
| KB Enhancement (8 formatos + relevância) | A | C | R |
| Intelligence Dashboard + KPIs | A | C | R |
| Anti-terceirização cognitiva (P1+P2+P4) | A | C | R |
| Monitoramento de créditos API | A | C | R |
| Atualizar documentação e specs | A | C | R |

---

## 5. Biblioteca de Prompts

> Todos os prompts abaixo foram executados com sucesso no Claude Code Terminal.
> Cada prompt é autocontido e referencia os artefatos existentes no repositório.

| ID | Nome | Fase | Status |
|---|---|---|---|
| P-01 | Scaffold FastAPI Project | 4.1 | ✅ Executado |
| P-02 | Migrations Alembic + Schema v2 | 4.2 | ✅ Executado |
| P-03 | Schemas Pydantic | 4.3 | ✅ Executado |
| P-04 | State Machine + Engine Determinística | 4.4 | ✅ Executado |
| P-05 | Integração LLM Anthropic | 4.5 | ✅ Executado |
| P-06 | API REST Endpoints | 4.6 | ✅ Executado |
| P-07 | Testes e Validação Final | 4.7 | ✅ Executado |
| P-08 | MVP Simulation: Preparação dos Casos | 5.1 | ✅ Executado |
| P-09 | MVP Simulation: Execução + Reports | 5.2–5.3 | ✅ Executado |
| P-10 | Learning Module | 6 | ✅ Executado |
| P-11 | Documentação Final + README | Pós-6 | ✅ Executado |
| P-FE | Frontend React | 7 | ✅ Executado |
| P-KB | Knowledge Base | 8 | ✅ Executado |
| P-INT | Inteligência Decisória | 9 | ✅ Executado |
| P-ACT | Anti-Terceirização Cognitiva | 10 | ✅ Executado |
| P-KB2 | KB Enhancement + API Balance | 11 | ✅ Executado |

---

## Resumo Final

O Mentor C-Level CFO está **100% implementado** com todas as fases concluídas:

- **Backend:** 28+ endpoints REST, engine determinística com 11 frameworks, LLM integrado com fallback e tracking de uso, learning module, knowledge base (8 formatos + validação de relevância), inteligência decisória, monitoramento de créditos API
- **Frontend:** React 18 + Tailwind com dashboard (+ banner de créditos API), stepper visual, multi-framework selection, anti-terceirização cognitiva, upload modal com drag-and-drop e validação de relevância
- **Testes:** 405+ testes passando, 99% de cobertura
- **Simulação:** 5 casos MVP validados, veredicto GO para enforcement
- **Documentação:** OpenAPI 3.0 completo, arquitetura, protocolo, resultados de simulação
