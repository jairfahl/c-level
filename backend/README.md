# Mentor CFO — Backend

API REST em FastAPI para o protocolo decisório do Mentor CFO. Gerencia o ciclo completo DRAFT → CLASSIFIED → STRUCTURED → RECOMMENDED → DECIDED → CLOSED com engine determinística, LLM integrado (Claude), módulo de aprendizado, base de conhecimento, inteligência decisória e mecanismos anti-terceirização cognitiva.

---

## Pré-requisitos

| Ferramenta | Versão mínima | Instalação |
|---|---|---|
| Docker + Compose | 24.x | [docs.docker.com](https://docs.docker.com/get-docker/) |
| Python | 3.11+ | pyenv ou sistema |
| jq | qualquer | `brew install jq` / `apt install jq` |
| Anthropic API Key | — | [console.anthropic.com](https://console.anthropic.com) |

---

## Setup Local

### 1. Configurar variáveis de ambiente

```bash
cd backend
cp .env.example .env   # ou criar manualmente

# Preencher obrigatoriamente:
# ANTHROPIC_API_KEY=sk-ant-...
# JWT_SECRET_KEY=<string aleatória, mínimo 32 chars>
```

Variáveis obrigatórias:

| Variável | Descrição | Exemplo |
|---|---|---|
| `ANTHROPIC_API_KEY` | Chave da API Anthropic | `sk-ant-api03-...` |
| `JWT_SECRET_KEY` | Secret para assinar os JWTs | `openssl rand -hex 32` |
| `DATABASE_URL` | URL asyncpg do PostgreSQL | `postgresql+asyncpg://mentor:mentor123@localhost:5432/mentor_cfo` |
| `REDIS_URL` | URL do Redis | `redis://localhost:6379/0` |

Variáveis opcionais (defaults razoáveis):

| Variável | Default | Descrição |
|---|---|---|
| `ANTHROPIC_MODEL` | `claude-sonnet-4-6` | Modelo Claude a usar |
| `ANTHROPIC_MAX_TOKENS` | `4096` | Tokens máximos por resposta |
| `ANTHROPIC_TIMEOUT` | `30` | Timeout da chamada LLM (segundos) |
| `LLM_CACHE_TTL` | `86400` | TTL do cache Redis em segundos (24h) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | Validade do token JWT (8h) |
| `APP_DEBUG` | `true` | Habilita `/docs` e `/redoc` |
| `API_CREDIT_BUDGET` | `5.0` | Orçamento total de créditos API (US$) |
| `API_CREDIT_WARNING_THRESHOLD` | `0.50` | Limiar para alerta de crédito baixo (US$) |
| `ANTHROPIC_INPUT_PRICE_PER_1M` | `3.0` | Preço por 1M tokens de input (US$) |
| `ANTHROPIC_OUTPUT_PRICE_PER_1M` | `15.0` | Preço por 1M tokens de output (US$) |

### 2. Subir a stack com Docker Compose

```bash
docker compose up -d

# Aguardar healthchecks (postgres + redis) — ~10 segundos
docker compose ps

# Rodar migrations do banco
docker compose exec app alembic upgrade head
```

Serviços Docker:

| Serviço | Porta | Descrição |
|---|---|---|
| `app` | 8000 | FastAPI backend |
| `postgres` | 5434 | PostgreSQL 15 |
| `redis` | 6380 | Redis 7 (LLM cache + token usage) |
| `frontend` | 3002 | React frontend (proxy → app:8000) |

### 3. Verificar saúde da API

```bash
curl http://localhost:8000/health
# {"status":"ok","service":"mentor-cfo","version":"3.0.0"}
```

### 4. Acessar o frontend

Abrir http://localhost:3002 — login com qualquer username.

### 5. Setup local sem Docker (para desenvolvimento)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Banco e Redis precisam estar rodando localmente ou via Docker:
docker compose up postgres redis -d
alembic upgrade head

uvicorn app.main:app --reload --port 8000
```

---

## Rodando os Testes

```bash
# Todos os testes (sem banco — mocks AsyncMock)
.venv/bin/python -m pytest tests/ -v

# Com relatório de cobertura HTML
.venv/bin/python -m pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html

# Apenas testes unitários do módulo de aprendizado
.venv/bin/python -m pytest tests/unit/test_learning.py -v

# Smoke test contra API rodando (requer stack Docker)
CFO_API_TOKEN=<jwt> ./scripts/smoke_test.sh

# Validação dos casos de simulação (sem API)
.venv/bin/python scripts/validate_cases.py
```

**Status atual:** 405+ testes passando | 99% de cobertura

---

## Referência de Endpoints

### Autenticação

```bash
# Obter token JWT (qualquer username no MVP)
curl -s -X POST http://localhost:8000/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"cfo-user"}'
# → {"access_token": "eyJ...", "token_type": "bearer"}
```

Todos os demais endpoints exigem `Authorization: Bearer <JWT>`.

### Casos Decisórios

| Método | Endpoint | Descrição | Estado → |
|---|---|---|---|
| `POST` | `/v1/financial-decision-cases` | Criar caso | `DRAFT` |
| `GET` | `/v1/financial-decision-cases` | Listar casos (paginado, filtros) | — |
| `GET` | `/v1/financial-decision-cases/{id}` | Detalhe do caso completo | — |
| `PATCH` | `/v1/financial-decision-cases/{id}/reclassify` | Reclassificar domínio/tipo | — |

### Máquina de Estados

| Método | Endpoint | Descrição | Estado → |
|---|---|---|---|
| `PUT` | `/{id}/classify` | Classificar impacto | `→ CLASSIFIED` |
| `PUT` | `/{id}/structure` | Registrar premissas e riscos | `→ STRUCTURED` |
| `GET` | `/{id}/suggest-methods` | Sugerir frameworks de análise | — |
| `GET` | `/{id}/suggest-reclassification` | Sugerir reclassificação via LLM | — |
| `PUT` | `/{id}/analyze` | Analisar (LLM + engine) | `→ RECOMMENDED` |
| `PUT` | `/{id}/reanalyze` | Reanalisar (após reclassificação) | `→ RECOMMENDED` |
| `PUT` | `/{id}/hypothesis` | Registrar hipótese pré-recomendação | — |
| `GET` | `/{id}/heuristic-alerts` | Alertas heurísticos + benchmark | — |
| `PUT` | `/{id}/decide` | Registrar decisão executiva | `→ DECIDED` |
| `PUT` | `/{id}/review` | Fechar com outcome real | `→ CLOSED` |

### Auditoria

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/v1/financial-decision-cases/{id}/state-transitions` | Trilha completa de auditoria |

### Heurísticas (Aprendizado Institucional)

| Método | Endpoint | Descrição |
|---|---|---|
| `POST` | `/v1/heuristics` | Criar heurística manual |
| `GET` | `/v1/heuristics?decision_type=X&domain=Y` | Listar ativas (com filtros) |
| `PUT` | `/v1/heuristics/{id}/deactivate` | Desativar (nunca deleta) |
| `GET` | `/v1/heuristics/learning-summary` | Resumo de aprendizado institucional |

### Base de Conhecimento

| Método | Endpoint | Descrição |
|---|---|---|
| `POST` | `/v1/knowledge-base/upload` | Upload de documento (8 formatos, ≤10MB, validação de relevância) |
| `POST` | `/v1/knowledge-base/validate-relevance` | Validar relevância de documento (stateless) |
| `GET` | `/v1/knowledge-base` | Listar documentos (com filtros) |
| `GET` | `/v1/knowledge-base/{id}` | Obter documento com texto extraído |
| `DELETE` | `/v1/knowledge-base/{id}` | Remover documento (soft delete) |

**Formatos aceitos:** PDF, DOCX, TXT, XLSX, XLS, PPTX, CSV, MD

### Admin / Inteligência Decisória

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/v1/admin/pending-reviews` | Casos DECIDED > 90 dias sem review |
| `GET` | `/v1/admin/decision-intelligence` | Dashboard de KPIs decisórios |
| `GET` | `/v1/admin/api-balance` | Saldo de créditos API (tokens consumidos, custo, restante) |

### Health

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/health` | Status da API |
| `GET` | `/docs` | Swagger UI (apenas em `APP_DEBUG=true`) |

---

## Fluxo Completo via Curl

```bash
export BASE=http://localhost:8000/v1

# ── 0. Autenticar ────────────────────────────────────────────────────────────────
TOKEN=$(curl -s -X POST "$BASE/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"username":"cfo-user"}' | jq -r '.access_token')
export H="Authorization: Bearer $TOKEN"

# ── 1. Criar ──────────────────────────────────────────────────────────────────
RESP=$(curl -s -X POST "$BASE/financial-decision-cases" \
  -H "$H" -H "Content-Type: application/json" \
  -d '{
    "title": "Aprovação de CAPEX: Nova Planta Recife R$ 18M",
    "description": "Investimento de R$ 18M com BNDES-Finem 60% e fundo PE 20%.",
    "financial_domain": "funding",
    "financial_exposure": 18000000,
    "decision_type": "investment_evaluation",
    "time_horizon": "long",
    "external_agents_present": true
  }')
ID=$(echo $RESP | jq -r '.id')

# ── 2. Classificar ────────────────────────────────────────────────────────────
curl -s -X PUT "$BASE/financial-decision-cases/$ID/classify" \
  -H "$H" -H "Content-Type: application/json" \
  -d '{"impact_score": 5}' | jq .

# ── 3. Estruturar ─────────────────────────────────────────────────────────────
curl -s -X PUT "$BASE/financial-decision-cases/$ID/structure" \
  -H "$H" -H "Content-Type: application/json" \
  -d '{
    "assumptions": [
      "Incentivo ICMS de 40% do governo de PE vigente por 15 anos",
      "BNDES-Finem mantém TJLP+2% sem aditivo de spread",
      "Mercado nordestino de proteína processada cresce 10-14% a.a."
    ],
    "risks": [
      "Revisão do incentivo ICMS por pressão fiscal estadual",
      "Fundo PE exerce opção de put antecipada em avaliação inferior ao VPL",
      "Atraso na obra civil estende prazo em 6-12 meses"
    ]
  }' | jq .

# ── 4. Consultar sugestões de framework ──────────────────────────────────────
curl -s "$BASE/financial-decision-cases/$ID/suggest-methods" -H "$H" | jq .

# ── 5. Analisar (com multi-framework) ────────────────────────────────────────
curl -s --max-time 60 -X PUT "$BASE/financial-decision-cases/$ID/analyze" \
  -H "$H" -H "Content-Type: application/json" \
  -d '{"frameworks_selected": ["game_theory", "scenario_analysis"]}' \
  | jq '{state, framework_selected, llm_unavailable, game_theory_model}'

# ── 6. Registrar hipótese (anti-terceirização cognitiva) ─────────────────────
curl -s -X PUT "$BASE/financial-decision-cases/$ID/hypothesis" \
  -H "$H" -H "Content-Type: application/json" \
  -d '{"initial_hypothesis": "Acredito que o investimento é viável dado o incentivo fiscal, mas o risco de drag-along do fundo PE precisa ser mitigado com lock-up mínimo de 36 meses."}' \
  | jq .

# ── 7. Consultar alertas heurísticos ─────────────────────────────────────────
curl -s "$BASE/financial-decision-cases/$ID/heuristic-alerts" -H "$H" | jq .

# ── 8. Decidir ────────────────────────────────────────────────────────────────
curl -s -X PUT "$BASE/financial-decision-cases/$ID/decide" \
  -H "$H" -H "Content-Type: application/json" \
  -d '{"executive_decision": "Aprovamos o investimento conforme recomendação."}' | jq .

# ── 9. Revisar (fecha o ciclo) ───────────────────────────────────────────────
curl -s -X PUT "$BASE/financial-decision-cases/$ID/review" \
  -H "$H" -H "Content-Type: application/json" \
  -d '{
    "outcome_summary": "ROIC de 18.2% alcançado no Ano 2, antes da meta do Ano 3.",
    "forecast_accuracy_score": 10,
    "risk_realization_rate": 12.0,
    "capital_allocation_efficiency_score": 96.0
  }' | jq '{state, divergence_outcome_flag, heuristics_generated}'

# ── 10. Auditar ──────────────────────────────────────────────────────────────
curl -s "$BASE/financial-decision-cases/$ID/state-transitions" -H "$H" \
  | jq '.transitions[] | "\(.from_state // "—") → \(.to_state)"'
```

---

## Estrutura do Código

```
backend/
├── app/
│   ├── main.py                     # FastAPI app + middlewares + routers
│   ├── api/routers/
│   │   ├── financial_decision_cases.py  # POST, GET, PATCH reclassify
│   │   ├── state_machine.py         # classify|structure|analyze|decide|review|hypothesis|reanalyze
│   │   ├── audit.py                 # GET state-transitions
│   │   ├── heuristics.py            # POST/GET /heuristics + deactivate + learning-summary
│   │   ├── knowledge_base.py        # POST upload, GET list/detail, DELETE
│   │   ├── admin.py                 # GET pending-reviews, decision-intelligence
│   │   └── auth.py                  # POST /auth/token
│   ├── core/
│   │   ├── state_machine.py         # StateMachineController + grafo de transições
│   │   ├── impact_scorer.py         # FinancialImpactScorer (5 faixas de exposição)
│   │   ├── framework_selector.py    # Seleção determinística + multi-framework suggestions
│   │   ├── game_theory.py           # GameTheoryActivator
│   │   ├── audit_logger.py          # AuditLogger (AuditLog + AuditAction)
│   │   ├── auth.py                  # JWT Bearer + get_current_user
│   │   ├── config.py                # Settings (pydantic-settings)
│   │   ├── database.py              # AsyncSession + get_db
│   │   └── exceptions.py            # MentorCFOException + subclasses
│   ├── llm/
│   │   ├── prompt_builder.py        # PromptBuilder + PromptContext + knowledge injection
│   │   ├── client.py                # LLMClient + CompletionResult (Anthropic asyncio)
│   │   ├── parser.py                # ResponseParser + LLMAnalysisResult
│   │   ├── cache.py                 # LLMCache (Redis, TTL 24h)
│   │   ├── fallback.py              # FallbackHandler (determinístico)
│   │   └── service.py               # LLMService (cache + client + fallback + token tracking)
│   ├── services/
│   │   ├── review_service.py        # ReviewService (divergence + risk materialization)
│   │   ├── heuristics_service.py    # HeuristicsService (CRUD + auto-generation)
│   │   ├── intelligence_service.py  # IntelligenceService (heuristic alerts + benchmark)
│   │   ├── knowledge_base_service.py # KnowledgeBaseService (upload + extraction, 8 formatos)
│   │   ├── relevance_validator.py   # RelevanceValidator (keywords financeiras vs off-topic)
│   │   └── review_trigger.py        # ReviewTrigger (casos pendentes > 90 dias)
│   ├── models/
│   │   ├── enums.py                 # Enums: DecisionState, FrameworkType, etc.
│   │   ├── base.py                  # Base declarativa SQLAlchemy
│   │   ├── financial_decision_case.py  # Todos os modelos ORM
│   │   └── knowledge_document.py    # KnowledgeDocument model
│   └── schemas/
│       └── __init__.py              # Todos os schemas Pydantic v2 (30+ schemas)
├── tests/
│   ├── unit/
│   │   ├── test_engine.py           # Engine determinística (108 testes)
│   │   ├── test_llm.py              # Camada LLM (76 testes)
│   │   ├── test_schemas.py          # Schemas Pydantic (73 testes)
│   │   ├── test_learning.py         # Learning Module (47 testes)
│   │   └── test_relevance.py        # Validador de relevância (15 testes)
│   └── integration/
│       ├── test_api.py              # Endpoints REST (54 testes)
│       └── test_flow.py             # Fluxo completo end-to-end (20 testes)
├── cases/
│   ├── simulation_cases.json        # 5 casos históricos estruturados
│   ├── simulation_cases.md          # Narrativas e fichas técnicas
│   ├── results/                     # case_01.json … case_05.json
│   ├── reports/                     # 5 Comparison Reports + consolidated
│   └── heuristics/
│       └── initial_heuristics.json  # 3 heurísticas reais aprendidas
├── scripts/
│   ├── smoke_test.sh                # Teste end-to-end via curl (8 passos)
│   ├── validate_cases.py            # Valida payloads contra schemas Pydantic
│   ├── run_simulation.py            # Executa 5 casos pela engine
│   └── generate_reports.py          # Gera Comparison Reports em Markdown
├── alembic/                         # Migrations do banco (001, 002, 003, 004)
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

---

## Documentação Interativa

Com a stack rodando:
- **Frontend:** http://localhost:3002
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
