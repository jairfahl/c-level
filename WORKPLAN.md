# Mentor C-Level — Plano de Trabalho Completo
> Versão 1.0 | Março 2026 | Foco inicial: CFO

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
FASE 0   Definição Estratégica         ████████████░░░░░░░░░  [CONCLUÍDA]
FASE 1   Arquitetura Conceitual        ████████████░░░░░░░░░  [CONCLUÍDA]
FASE 2   Especificação Funcional       ████████████░░░░░░░░░  [CONCLUÍDA]
FASE 3   Arquitetura Técnica           ████████████░░░░░░░░░  [CONCLUÍDA]
FASE 4   Core Engine Development       ░░░░░░░░░░░░░░░░░░░░░  [PRÓXIMA]
FASE 5   MVP Simulation                ░░░░░░░░░░░░░░░░░░░░░  [PENDENTE]
FASE 6   Learning Module               ░░░░░░░░░░░░░░░░░░░░░  [PENDENTE]
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

### FASE 4 — Core Engine Development 🔵 [PRÓXIMA]
**Objetivo:** Construir o backend funcional com engine determinística, camada LLM e API REST.

#### 4.1 — Scaffold do Projeto
- Inicializar projeto FastAPI com estrutura de diretórios definida
- Configurar Docker + Docker Compose (app, postgres, redis)
- Configurar Alembic para migrations
- Setup de variáveis de ambiente (.env)

#### 4.2 — Database
- Executar schema SQL v2 via migration Alembic
- Configurar SQLAlchemy 2.0 async com PostgreSQL
- Validar todas as tabelas, ENUMs, triggers e índices

#### 4.3 — Schemas Pydantic
- Criar schemas de request/response alinhados ao OpenAPI v2
- Validações de negócio embutidas nos schemas

#### 4.4 — Engine Determinística
- State Machine Controller (validação de transições)
- Financial Impact Scorer (impact_score por faixas de exposure)
- Framework Selector (decision_type → framework_type)
- Scenario Requirement Enforcer (scenario_required)
- Game Theory Activator (critérios formais)
- Audit Logger (INSERT ONLY em audit_logs)

#### 4.5 — Camada LLM
- Integração com Anthropic Claude API
- Template de prompt estruturado (System + User)
- Parser do output JSON
- Fallback determinístico (llm_unavailable flag)
- Cache Redis para respostas idênticas

#### 4.6 — API REST
- Implementar todos os endpoints do OpenAPI v2
- Autenticação JWT (middleware)
- Error handlers padronizados
- Testes de integração dos endpoints

#### 4.7 — Testes
- Unit tests da engine determinística
- Unit tests do Framework Selector
- Unit tests da State Machine
- Integration tests dos endpoints

| Entregável | Status |
|---|---|
| Projeto FastAPI scaffolded | ⬜ |
| Docker Compose funcional | ⬜ |
| Schema v2 aplicado via Alembic | ⬜ |
| Engine determinística completa | ⬜ |
| Camada LLM integrada | ⬜ |
| API REST todos endpoints | ⬜ |
| Autenticação JWT | ⬜ |
| Cache Redis | ⬜ |
| Cobertura de testes ≥ 80% | ⬜ |

---

### FASE 5 — MVP Simulation 🔵 [PENDENTE]
**Objetivo:** Validar o conceito com 5 decisões financeiras históricas reais.

#### 5.1 — Preparação dos Casos
- Coletar 5 decisões financeiras reais (racionais originais)
- Preencher campos mínimos por caso
- Documentar resultado real de cada decisão

#### 5.2 — Execução do Protocolo
- Processar cada caso pelo Mentor CFO
- Registrar premissas, riscos e recomendação
- Capturar decisão executiva e divergência

#### 5.3 — Comparison Report
- Gerar Comparison Report para cada caso (template da Fase 5)
- Calcular delta de premissas e riscos identificados
- Coletar score de clareza do executivo (1–5)

#### 5.4 — Análise de Resultados
- Consolidar métricas dos 5 casos
- Validar critérios de sucesso da Fase 0
- Documentar aprendizados e ajustes necessários

| Entregável | Status |
|---|---|
| 5 casos históricos documentados | ⬜ |
| 5 casos processados pelo Mentor | ⬜ |
| 5 Comparison Reports gerados | ⬜ |
| Relatório consolidado de resultados | ⬜ |
| Go/No-Go para enforcement por impacto | ⬜ |

---

### FASE 6 — Learning Module 🔵 [PENDENTE]
**Objetivo:** Fechar o ciclo com revisão pós-decisão e registro de heurísticas.

#### 6.1 — Post-Decision Review
- Implementar endpoint de review
- Capturar métricas reais vs projetadas
- Calcular divergence_outcome_flag

#### 6.2 — Heuristics Registry
- Estrutura da tabela financial_heuristics
- Formato JSON das heurísticas (definido na Fase 3)
- Interface manual de registro (MVP)

#### 6.3 — Trigger de Review
- Lógica de identificação de casos prontos para review (90d)
- Notificação (email/webhook) — futuro
- Bloqueio por enforcement — futuro

| Entregável | Status |
|---|---|
| Endpoint de review funcional | ⬜ |
| Métricas pós-decisão armazenadas | ⬜ |
| Registro manual de heurísticas | ⬜ |
| Trigger de review (lógica) | ⬜ |

---

## 3. Interdependências

```
FASE 0 ──────────────────────────────────────────────── BASE
   │
   └──► FASE 1 (Arquitetura depende do escopo)
             │
             └──► FASE 2 (Dados dependem da arquitetura)
                       │
                       └──► FASE 3 (Stack depende do modelo de dados)
                                 │
                                 ├──► FASE 4.1  Scaffold
                                 │        │
                                 │        └──► FASE 4.2  Database
                                 │                  │
                                 │                  ├──► FASE 4.3  Schemas
                                 │                  │        │
                                 │                  │        └──► FASE 4.4  Engine Determinística
                                 │                  │                  │
                                 │                  │                  └──► FASE 4.5  Camada LLM
                                 │                  │                            │
                                 │                  │                            └──► FASE 4.6  API REST
                                 │                  │                                      │
                                 │                  │                                      └──► FASE 4.7  Testes
                                 │                  │
                                 │                  └──►  FASE 5  (requer API funcional)
                                 │                               │
                                 │                               └──►  FASE 6  (requer dados reais da Fase 5)
                                 │
                                 └──► FASE 3 specs já entregues (SQL + YAML) ✅
```

### Regras de Dependência

| Fase | Bloqueada por | Desbloqueia |
|---|---|---|
| Fase 1 | Fase 0 | Fase 2 |
| Fase 2 | Fase 1 | Fase 3 |
| Fase 3 | Fase 2 | Fase 4 |
| Fase 4.2 | Fase 4.1 (scaffold) | Fase 4.3, 4.4, 4.5 |
| Fase 4.4 | Fase 4.2, 4.3 | Fase 4.5 |
| Fase 4.5 | Fase 4.4 | Fase 4.6 |
| Fase 4.6 | Fase 4.5 | Fase 4.7, Fase 5 |
| Fase 5 | Fase 4.6 completa | Fase 6 |
| Fase 6 | Fase 5 (≥1 caso real) | Encerramento MVP |

### Paralelismo Possível

| Pode rodar em paralelo |
|---|
| Fase 4.3 (Schemas) + Fase 4.4 (Engine) após Fase 4.2 |
| Fase 4.7 (Testes) incrementais durante 4.4, 4.5, 4.6 |
| Fase 5.1 (coleta de casos) durante Fase 4.6 |

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

### FASE 1 — Arquitetura Conceitual

| Atividade | Arquiteto | Orquestrador | Dev Sênior |
|---|:---:|:---:|:---:|
| Definir modelo híbrido | A | R | C |
| Mapear módulos core | A | R | C |
| Definir fluxo de dados | A | C | R |
| Alinhar com APQC | A | R | I |

### FASE 2 — Especificação Funcional

| Atividade | Arquiteto | Orquestrador | Dev Sênior |
|---|:---:|:---:|:---:|
| Modelar FinancialDecisionCase | A | C | R |
| Definir decision types e frameworks | A | C | R |
| Especificar máquina de estados | A | C | R |
| Definir regras de validação | A | R | C |

### FASE 3 — Arquitetura Técnica

| Atividade | Arquiteto | Orquestrador | Dev Sênior |
|---|:---:|:---:|:---:|
| Decidir stack tecnológico | A | R | C |
| Criar schema SQL v2 | A | C | R |
| Criar contrato OpenAPI v2 | A | C | R |
| Definir estratégia de auth e cache | A | R | C |

### FASE 4 — Core Engine Development

| Atividade | Arquiteto | Orquestrador | Dev Sênior |
|---|:---:|:---:|:---:|
| Scaffold do projeto FastAPI | I | A | R |
| Configurar Docker + Alembic | I | A | R |
| Implementar State Machine | C | A | R |
| Implementar Framework Selector | C | A | R |
| Implementar Game Theory Activator | A | C | R |
| Integrar Anthropic Claude API | C | A | R |
| Implementar template de prompt LLM | A | C | R |
| Implementar fallback LLM | C | A | R |
| Implementar cache Redis | I | A | R |
| Implementar endpoints API REST | C | A | R |
| Implementar autenticação JWT | C | A | R |
| Escrever testes unitários | I | A | R |
| Escrever testes de integração | C | A | R |
| Revisar e aprovar código | A | I | C |

### FASE 5 — MVP Simulation

| Atividade | Arquiteto | Orquestrador | Dev Sênior |
|---|:---:|:---:|:---:|
| Coletar decisões históricas reais | A | R | I |
| Executar protocolo nos 5 casos | A | R | C |
| Gerar Comparison Reports | A | R | C |
| Analisar resultados consolidados | A | R | C |
| Decisão Go/No-Go enforcement | A | R | I |

### FASE 6 — Learning Module

| Atividade | Arquiteto | Orquestrador | Dev Sênior |
|---|:---:|:---:|:---:|
| Implementar endpoint de review | C | A | R |
| Implementar heuristics registry | A | C | R |
| Implementar lógica de trigger | C | A | R |
| Validar ciclo completo | A | R | C |

---

## 5. Biblioteca de Prompts

> Todos os prompts abaixo são para uso direto no **Claude no Terminal**.
> Copie o bloco markdown do prompt desejado e cole no terminal.
> Cada prompt é autocontido e referencia os artefatos já existentes no repositório.

---

### P-01 — Scaffold do Projeto FastAPI

**Objetivo:** Criar a estrutura completa do projeto FastAPI com Docker, Alembic e configuração de ambiente.

**Fase:** 4.1 | **Dependências:** Fase 3 concluída | **Entregável:** Projeto inicializado e rodando localmente

```markdown
# TASK: Scaffold Mentor CFO — FastAPI Project

## Context
Estamos construindo o backend do Mentor C-Level CFO.
Stack definido: FastAPI (Python 3.11+), PostgreSQL 15+, Redis 7+, Alembic, SQLAlchemy 2.0 async, JWT auth.
Repositório local: /Users/jairfahl/Downloads/c-level

## Objective
Criar a estrutura completa do projeto FastAPI dentro de /Users/jairfahl/Downloads/c-level/backend/

## Required Structure
```
backend/
├── app/
│   ├── api/           # routers FastAPI
│   ├── core/          # engine determinística, state machine
│   ├── llm/           # integração LLM, prompts, parser
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   └── services/      # lógica de negócio
├── alembic/
├── tests/
├── .env.example
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

## Deliverables
1. Todos os arquivos e diretórios acima criados
2. pyproject.toml com todas as dependências (fastapi, sqlalchemy, alembic, asyncpg, redis, python-jose, anthropic, pytest)
3. docker-compose.yml com services: app, postgres, redis
4. Dockerfile otimizado para Python 3.11+
5. .env.example com todas as variáveis necessárias
6. app/main.py com FastAPI app configurado, CORS, health check endpoint
7. Confirmar que `docker compose up` sobe sem erros

## Constraints
- Use async/await em todos os endpoints e queries
- Pydantic v2
- SQLAlchemy 2.0 com AsyncSession
```
```

---

### P-02 — Migrations Alembic + Schema SQL v2

**Objetivo:** Aplicar o schema SQL v2 completo via Alembic migrations, validando todas as tabelas, ENUMs e triggers.

**Fase:** 4.2 | **Dependências:** P-01 | **Entregável:** Banco de dados com schema v2 aplicado

```markdown
# TASK: Alembic Migration — CFO Schema v2

## Context
Projeto FastAPI já scaffolded em /Users/jairfahl/Downloads/c-level/backend/
Schema SQL v2 de referência: /Users/jairfahl/Downloads/c-level/CFO/Corrected_v2/CFO_Schema_v2.sql

## Objective
Criar e aplicar migration Alembic que implemente o schema SQL v2 completo.

## Required Tables (em ordem de criação)
1. ENUMs: financial_domain, decision_state, decision_type, time_horizon_type, framework_type
2. financial_decision_cases (com coluna gerada scenario_required)
3. financial_assumptions (com campo is_implicit)
4. financial_risks
5. financial_metrics_impacted
6. decisions
7. reviews (com divergence_outcome_flag)
8. state_transitions
9. audit_logs (com regras INSERT ONLY)
10. financial_heuristics

## Deliverables
1. Migration Alembic criada em alembic/versions/
2. SQLAlchemy models criados em app/models/ para cada tabela
3. Função update_updated_at() e triggers criados
4. Todos os índices aplicados
5. `alembic upgrade head` executado com sucesso
6. Validação: query em cada tabela retorna sem erro

## Constraints
- Seguir exatamente o CFO_Schema_v2.sql como fonte da verdade
- Manter COMMENTs nas tabelas e colunas críticas
- audit_logs deve ser INSERT ONLY (regras no banco)
```
```

---

### P-03 — Schemas Pydantic

**Objetivo:** Criar todos os schemas Pydantic de request/response alinhados ao contrato OpenAPI v2.

**Fase:** 4.3 | **Dependências:** P-02 | **Entregável:** Schemas validados e prontos para uso nos endpoints

```markdown
# TASK: Pydantic Schemas — CFO OpenAPI v2

## Context
Contrato de referência: /Users/jairfahl/Downloads/c-level/CFO/Corrected_v2/CFO_OpenAPI_v2.yaml
Models SQLAlchemy já criados em app/models/

## Objective
Criar todos os schemas Pydantic v2 em app/schemas/ alinhados ao OpenAPI v2.

## Required Schemas

### Request schemas
- FinancialDecisionCaseCreate
- ClassifyRequest
- StructureRequest (validar min 3 assumptions, min 3 risks)
- DecideRequest (com divergence_justification e monitoring_criteria)
- ReviewRequest

### Response schemas
- FinancialDecisionCaseResponse
- FinancialDecisionCaseFullResponse (com assumptions, risks, metrics)
- ClassifyResponse (com framework_selected e scenario_required)
- AnalysisResponse (com scenario_summary, game_theory_model, implicit_assumptions_found, llm_unavailable)
- PaginatedCasesResponse
- StateTransitionResponse
- ErrorResponse

### Enum schemas
- FinancialDomain, DecisionState, DecisionType, TimeHorizon, FrameworkType

## Deliverables
1. Arquivo app/schemas/__init__.py com todos os schemas
2. Validações de negócio embutidas (min items, min length, ranges)
3. Testes unitários dos schemas em tests/unit/test_schemas.py

## Constraints
- Pydantic v2 (model_validator, field_validator)
- Todos os campos readOnly devem ser exclude em inputs
- ErrorResponse padronizado com 'error' (código) e 'message' (descrição)
```
```

---

### P-04 — State Machine + Engine Determinística

**Objetivo:** Implementar a engine determinística completa: state machine, impact scorer, framework selector, game theory activator e audit logger.

**Fase:** 4.4 | **Dependências:** P-02, P-03 | **Entregável:** Engine determinística testada e funcional

```markdown
# TASK: Deterministic Engine — State Machine + Rules

## Context
Especificação: /Users/jairfahl/Downloads/c-level/CFO/Corrected_v2/CFO_Spec_Phase_4_Core_Engine_Development_v2.docx
State machine: 8 estados, transições definidas no OpenAPI v2.
Repositório: /Users/jairfahl/Downloads/c-level/backend/app/core/

## Objective
Implementar todos os componentes da engine determinística em app/core/

## Components

### 1. State Machine Controller (app/core/state_machine.py)
- Mapa de transições válidas
- Método transition(case, to_state, triggered_by) → valida e persiste em state_transitions
- Lança InvalidStateTransitionError (→ HTTP 409) para transições inválidas

### 2. Financial Impact Scorer (app/core/impact_scorer.py)
- Calcular impact_score baseado em financial_exposure:
  - 1: exposure < 100k
  - 2: 100k–500k
  - 3: 500k–2M
  - 4: 2M–10M
  - 5: > 10M
- Retornar score e trigger scenario_required flag

### 3. Framework Selector (app/core/framework_selector.py)
- Mapeamento decision_type + external_agents_present → framework_type
- Seguir tabela exata da Fase 2:
  - debt_structuring + external_agents=true → game_theory
  - budget_adjustment → pdca
  - forecast_revision → scenario_analysis
  - capital_allocation → capital_allocation
  - liquidity_management → risk_matrix
  - risk_hedging → risk_matrix
  - cost_reduction → trade_off
  - investment_evaluation → scenario_analysis

### 4. Game Theory Activator (app/core/game_theory.py)
- Critério: external_agents_present=true AND decision_type IN (debt_structuring, investment_evaluation, capital_allocation)
- Retorna bool is_active

### 5. Audit Logger (app/core/audit_logger.py)
- log(decision_case_id, action, payload) → INSERT em audit_logs
- Actions: CASE_CREATED, STATE_TRANSITION, LLM_CALLED, LLM_FALLBACK, DIVERGENCE_RECORDED

## Deliverables
1. Todos os 5 módulos implementados
2. Testes unitários em tests/unit/test_engine.py (cobertura ≥ 90%)
3. Testes de transições inválidas garantindo HTTP 409

## Constraints
- Engine NUNCA chama LLM diretamente — apenas prepara contexto
- Toda transição de estado persiste em state_transitions E audit_logs
- Lógica deve ser pura (sem side effects além de DB)
```
```

---

### P-05 — Integração LLM (Anthropic Claude API)

**Objetivo:** Implementar a camada LLM com template de prompt estruturado, parser de output JSON, cache Redis e fallback determinístico.

**Fase:** 4.5 | **Dependências:** P-04 | **Entregável:** Camada LLM integrada e com fallback testado

```markdown
# TASK: LLM Layer — Anthropic Claude API Integration

## Context
Template de prompt: definido na Fase 4 (CFO_Spec_Phase_4_Core_Engine_Development_v2.docx)
Camada LLM em: /Users/jairfahl/Downloads/c-level/backend/app/llm/
Engine determinística já implementada (P-04)

## Objective
Implementar a camada LLM completa em app/llm/

## Components

### 1. Prompt Builder (app/llm/prompt_builder.py)
Construir o prompt SYSTEM + USER seguindo exatamente este template:

**SYSTEM:**
"You are a structured financial decision-making mentor for CFOs.
Your role is to analyze financial decisions using rigorous methodology.
Never provide opinions without structure. Always identify risks.
Never skip assumption explicitiation.
Output must follow the exact JSON contract defined below."

**USER sections:**
- ## Context (decision_type, domain, exposure, time_horizon, framework, scenario_required, game_theory_active)
- ## Stated Assumptions (lista)
- ## Identified Risks (lista)
- ## Instructions (numbered, referenciando framework e flags)
- ## Output JSON Contract (schema exato)

### 2. LLM Client (app/llm/client.py)
- Integração com anthropic SDK (AsyncAnthropic)
- Modelo: claude-3-5-sonnet-20241022
- Max tokens: 4096
- Temperature: 0 (determinístico)
- Timeout: 30s

### 3. Response Parser (app/llm/parser.py)
- Extrair JSON do response do Claude
- Validar contra schema AnalysisResult
- Lançar LLMParseError se JSON inválido

### 4. Cache Redis (app/llm/cache.py)
- Chave: SHA256(decision_type + framework + sorted(assumptions) + sorted(risks))
- TTL: 86400s (24h)
- get(key) → AnalysisResult | None
- set(key, result, ttl)

### 5. Fallback Handler (app/llm/fallback.py)
- Retornar AnalysisResult parcial com llm_unavailable=True
- Preencher framework_selected e financial_metrics_impacted via engine determinística
- Logar action='LLM_FALLBACK' em audit_logs

### 6. LLM Service (app/llm/service.py)
- analyze(case, context) → AnalysisResult
- Fluxo: check cache → call LLM → parse → cache → return
- On error: fallback handler

## Deliverables
1. Todos os 6 módulos implementados
2. Testes unitários com mock da API Anthropic (tests/unit/test_llm.py)
3. Teste de fallback quando API indisponível

## Constraints
- Nunca expor API key no código (usar variável de ambiente ANTHROPIC_API_KEY)
- Cache DEVE ser verificado antes de chamar API
- llm_unavailable=True deve ser retornado ao frontend quando fallback ativo
```
```

---

### P-06 — API REST Endpoints

**Objetivo:** Implementar todos os endpoints FastAPI do contrato OpenAPI v2, com autenticação JWT e error handlers.

**Fase:** 4.6 | **Dependências:** P-04, P-05 | **Entregável:** API REST completa e testada

```markdown
# TASK: FastAPI REST Endpoints — CFO OpenAPI v2

## Context
Contrato de referência: /Users/jairfahl/Downloads/c-level/CFO/Corrected_v2/CFO_OpenAPI_v2.yaml
Engine determinística (P-04) e LLM layer (P-05) já implementados.

## Objective
Implementar todos os endpoints em app/api/routers/

## Endpoints a implementar

### Router: financial_decision_cases.py
- POST   /financial-decision-cases           → create case
- GET    /financial-decision-cases           → list (paginado, filtros: domain, state, type)
- GET    /financial-decision-cases/{id}      → get full case

### Router: state_machine.py
- PUT    /financial-decision-cases/{id}/classify   → DRAFT→CLASSIFIED
- PUT    /financial-decision-cases/{id}/structure  → CLASSIFIED→STRUCTURED
- PUT    /financial-decision-cases/{id}/analyze    → STRUCTURED→RECOMMENDED (chama LLM)
- PUT    /financial-decision-cases/{id}/decide     → RECOMMENDED→DECIDED
- PUT    /financial-decision-cases/{id}/review     → DECIDED→CLOSED

### Router: audit.py
- GET    /financial-decision-cases/{id}/state-transitions

## Auth Middleware (app/core/auth.py)
- Verificar Bearer JWT em todos os endpoints
- Retornar 401 para token inválido/ausente
- SECRET_KEY via variável de ambiente

## Error Handlers (app/core/exceptions.py)
- 400 → ValidationError / InsufficientAssumptionsError / InsufficientRisksError
- 401 → UnauthorizedError
- 404 → CaseNotFoundError
- 409 → InvalidStateTransitionError
- 500 → InternalError
- Todos retornam ErrorResponse(error=str, message=str)

## Deliverables
1. Todos os routers implementados
2. Middleware JWT configurado
3. Exception handlers registrados no main.py
4. Testes de integração em tests/integration/test_api.py
5. Todos os endpoints testados: happy path + casos de erro
6. `curl` examples funcionais para cada endpoint

## Constraints
- Seguir exatamente o contrato OpenAPI v2 (status codes, response schemas)
- Pagination: page + limit, retornar total
- analyze endpoint: chamar engine determinística ANTES da LLM
```
```

---

### P-07 — Testes e Validação Final

**Objetivo:** Garantir cobertura de testes ≥ 80%, rodar suite completa e validar o fluxo end-to-end.

**Fase:** 4.7 | **Dependências:** P-06 | **Entregável:** Suite de testes passando, API pronta para simulação

```markdown
# TASK: Test Suite + End-to-End Validation

## Context
Backend completo em /Users/jairfahl/Downloads/c-level/backend/
Todos os endpoints implementados (P-06)

## Objective
Garantir qualidade e rodar validação end-to-end do fluxo completo.

## Test Suite

### Unit Tests
- tests/unit/test_schemas.py       (validações Pydantic)
- tests/unit/test_engine.py        (state machine, scorer, selector)
- tests/unit/test_llm.py           (prompt builder, parser, cache, fallback)

### Integration Tests
- tests/integration/test_api.py    (todos os endpoints)
- tests/integration/test_flow.py   (fluxo completo: DRAFT→CLOSED)

### End-to-End Flow Test
Executar o seguinte fluxo completo via API:
1. POST /financial-decision-cases   → id
2. PUT  /{id}/classify               → CLASSIFIED, framework_selected, scenario_required
3. PUT  /{id}/structure              → STRUCTURED (3 assumptions, 3 risks)
4. PUT  /{id}/analyze                → RECOMMENDED (LLM chamado, recommendation gerada)
5. PUT  /{id}/decide                 → DECIDED (divergence_flag calculado)
6. GET  /{id}/state-transitions      → 5 transições registradas
7. PUT  /{id}/review                 → CLOSED

## Coverage Requirements
- Cobertura mínima: 80% geral
- Engine determinística: 90%
- State machine transitions: 100%

## Deliverables
1. `pytest tests/ -v` rodando sem falhas
2. `pytest --cov=app --cov-report=html` gerando relatório
3. Relatório de cobertura salvo em htmlcov/
4. Script de smoke test (scripts/smoke_test.sh) com curl calls do fluxo completo

## Constraints
- Usar banco de dados de teste (PostgreSQL em Docker, banco separado)
- Mockar chamadas à Anthropic API nos unit tests
- Testes de integração podem chamar LLM real (flag --integration)
```
```

---

### P-08 — MVP Simulation: Preparação dos Casos

**Objetivo:** Estruturar os 5 casos históricos de decisões financeiras reais para simulação.

**Fase:** 5.1 | **Dependências:** P-07 (API funcional) | **Entregável:** 5 casos documentados e prontos

```markdown
# TASK: MVP Simulation — Case Preparation

## Context
Template de caso: /Users/jairfahl/Downloads/c-level/CFO/Corrected_v2/CFO_Spec_Phase_5_MVP_Simulation_v2.docx
API funcionando localmente.

## Objective
Documentar os 5 casos históricos de decisões financeiras reais em formato estruturado.

## Required Format (para cada caso)
```json
{
  "title": "string",
  "description": "string",
  "financial_domain": "enum",
  "decision_type": "enum",
  "financial_exposure": number,
  "time_horizon": "short|medium|long",
  "external_agents_present": boolean,
  "original_rationale": "texto original da decisão",
  "decision_taken": "o que foi decidido",
  "actual_outcome": "resultado real (se conhecido)"
}
```

## Cases to Document
1. Realocação orçamentária (budget_adjustment / planning)
2. Renegociação de dívida (debt_structuring / funding + external_agents=true)
3. Gestão de liquidez (liquidity_management / treasury)
4. Aprovação de investimento (investment_evaluation / funding, impact≥4)
5. Revisão de forecast sob stress (forecast_revision / reporting)

## Deliverables
1. Arquivo cases/simulation_cases.json com os 5 casos estruturados
2. Documento cases/simulation_cases.md com racional original em texto livre
3. Validação: cada caso passa pela API sem erro de validação

## Constraints
- Usar dados reais ou representativos do contexto CFO
- Garantir que ao menos 2 casos tenham impact_score ≥ 4 (scenario_required=true)
- Ao menos 1 caso com external_agents_present=true (ativa Game Theory)
```
```

---

### P-09 — MVP Simulation: Execução e Comparison Reports

**Objetivo:** Executar os 5 casos pelo Mentor CFO e gerar os Comparison Reports comparando racional original vs estruturado.

**Fase:** 5.2–5.3 | **Dependências:** P-08 | **Entregável:** 5 Comparison Reports + relatório consolidado

```markdown
# TASK: MVP Simulation — Execution + Comparison Reports

## Context
5 casos preparados em cases/simulation_cases.json
API funcionando, LLM integrada.
Template Comparison Report: CFO_Spec_Phase_5_MVP_Simulation_v2.docx

## Objective
Processar os 5 casos pela API e gerar Comparison Reports automáticos.

## Execution Flow (para cada caso)
1. POST /financial-decision-cases → criar caso
2. PUT  /{id}/classify             → classificar
3. PUT  /{id}/structure            → estruturar com assumptions e risks do caso
4. PUT  /{id}/analyze              → obter recomendação do Mentor
5. PUT  /{id}/decide               → registrar decisão original
6. Salvar resposta completa em cases/results/{case_id}.json

## Comparison Report (para cada caso)
Gerar arquivo cases/reports/report_{case_name}.md com:

### Seção A — Racional Original
- Resumo da justificativa original (do simulation_cases.md)
- Premissas identificadas no racional original (manual)
- Riscos mencionados no racional original (manual)

### Seção B — Racional Estruturado pelo Mentor
- Framework aplicado
- Premissas explicitadas (incluindo implícitas capturadas pelo LLM)
- Riscos identificados
- Análise de cenários (se aplicável)
- Recomendação estruturada

### Seção C — Delta de Qualidade
- premissas_adicionais: int
- riscos_adicionais: int
- cenarios_gerados: int
- divergencia_registrada: boolean
- score_clareza_executivo: 1–5

## Deliverables
1. 5 arquivos cases/results/{case_id}.json
2. 5 arquivos cases/reports/report_{name}.md
3. cases/reports/consolidated_report.md (métricas agregadas dos 5 casos)

## Constraints
- Usar dados reais da API (não simular respostas)
- score_clareza_executivo deve ser preenchido pelo Arquiteto após leitura
- consolidated_report deve incluir Go/No-Go para enforcement
```
```

---

### P-10 — Learning Module: Post-Decision Review

**Objetivo:** Implementar o módulo de revisão pós-decisão, registro de heurísticas e trigger de review.

**Fase:** 6 | **Dependências:** P-09 (ao menos 1 caso com resultado real) | **Entregável:** Módulo de aprendizado funcional

```markdown
# TASK: Learning Module — Post-Decision Review + Heuristics

## Context
Especificação: /Users/jairfahl/Downloads/c-level/CFO/Corrected_v2/CFO_Spec_Phase_6_Learning_Module_v2.docx
Endpoint PUT /review já implementado (P-06).
Schema financial_heuristics já no banco (P-02).

## Objective
Completar o módulo de aprendizado com heuristics registry e trigger de review.

## Components

### 1. Review Service Enhancement (app/services/review_service.py)
- Ao fechar review (CLOSED), calcular automaticamente divergence_outcome_flag
- Regra: se divergence_flag=true E forecast_accuracy_score < 5 → divergence_outcome_flag=true
- Atualizar financial_risks.materialized baseado no outcome_summary (via LLM ou manual)

### 2. Heuristics Registry (app/services/heuristics_service.py)
- create_heuristic(decision_type, domain, key, value, source_case_id)
- list_heuristics(decision_type, domain) → heurísticas ativas
- deactivate_heuristic(id)
- Formato JSON de heurística conforme Fase 6

### 3. Review Trigger (app/services/review_trigger.py)
- get_cases_pending_review() → casos DECIDED há >90 dias sem review
- Retornar lista para notificação manual (MVP)
- Endpoint: GET /admin/pending-reviews

### 4. Heuristics Endpoint (app/api/routers/heuristics.py)
- POST /heuristics                → criar heurística manual
- GET  /heuristics                → listar (filtro: decision_type, domain)
- PUT  /heuristics/{id}/deactivate

## Deliverables
1. Review service completo com divergence_outcome_flag automático
2. Heuristics service implementado
3. Endpoints de heurísticas funcionais
4. Endpoint GET /admin/pending-reviews
5. Testes em tests/unit/test_learning.py
6. Documentar 3 heurísticas reais aprendidas dos casos da Fase 5

## Constraints
- Heuristics são INSERT/UPDATE only — nunca DELETE (apenas deactivate)
- MVP: criação de heurísticas é manual pelo Arquiteto
- Trigger de review: lógica apenas, sem envio automático de email no MVP
```
```

---

### P-11 — Documentação Final e README

**Objetivo:** Gerar documentação completa do projeto, README atualizado e guia de uso do MVP.

**Fase:** Pós-Fase 6 | **Dependências:** Todas as fases | **Entregável:** Repositório documentado e publicado

```markdown
# TASK: Final Documentation + README

## Context
Projeto completo em /Users/jairfahl/Downloads/c-level/
Backend funcional, simulação concluída, learning module implementado.

## Objective
Documentar o projeto completamente para uso e evolução futura.

## Deliverables

### 1. README.md (raiz do repositório)
- Visão geral do projeto (1 parágrafo)
- Arquitetura em ASCII
- Quickstart (docker compose up + primeira decisão via curl)
- Links para documentação de cada fase

### 2. backend/README.md
- Setup local (pré-requisitos, .env, docker compose up)
- Como rodar os testes
- Como usar a API (exemplos curl do fluxo completo)
- Variáveis de ambiente obrigatórias

### 3. docs/ARCHITECTURE.md
- Diagrama da arquitetura híbrida
- Fluxo de dados detalhado
- Decisões técnicas e justificativas (ADRs simplificados)

### 4. docs/PROTOCOL.md
- Protocolo decisório mandatório explicado
- Máquina de estados com exemplos
- Regras de validação
- Como registrar divergência

### 5. docs/SIMULATION_RESULTS.md
- Resultados consolidados das 5 simulações
- Métricas de ganho cognitivo
- Recomendações para enforcement

## Constraints
- README deve ter quickstart funcional em menos de 5 minutos
- Todos os exemplos curl devem funcionar com o Docker Compose local
- Documentação em português (público interno CFO)
```
```

---

## Resumo dos Prompts

| ID | Nome | Fase | Dependências |
|---|---|---|---|
| P-01 | Scaffold FastAPI Project | 4.1 | Fase 3 ✅ |
| P-02 | Migrations Alembic + Schema v2 | 4.2 | P-01 |
| P-03 | Schemas Pydantic | 4.3 | P-02 |
| P-04 | State Machine + Engine Determinística | 4.4 | P-02, P-03 |
| P-05 | Integração LLM Anthropic | 4.5 | P-04 |
| P-06 | API REST Endpoints | 4.6 | P-04, P-05 |
| P-07 | Testes e Validação Final | 4.7 | P-06 |
| P-08 | MVP Simulation: Preparação dos Casos | 5.1 | P-07 |
| P-09 | MVP Simulation: Execução + Reports | 5.2–5.3 | P-08 |
| P-10 | Learning Module | 6 | P-09 |
| P-11 | Documentação Final | Pós-6 | Todos |

---

> **Próximo passo:** executar **P-01** no Claude Terminal para iniciar a Fase 4.
