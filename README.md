# Mentor C-Level CFO

**Governança cognitiva de decisões financeiras para CFOs.** O Mentor CFO é um sistema de protocolo decisório que estrutura, analisa e audita decisões financeiras de alto impacto — integrando frameworks analíticos determinísticos (PDCA, Teoria dos Jogos, Matriz de Riscos, Análise de Cenários, Decision Tree, SWOT, entre outros) com inteligência artificial (Claude / Anthropic) para garantir que nenhuma decisão relevante seja tomada sem premissas explícitas, riscos identificados e recomendação estruturada registrada.

O sistema inclui **mecanismos anti-terceirização cognitiva** que previnem a aceitação passiva de recomendações da IA: reflexão pré-recomendação (hipótese obrigatória), detecção de rubber-stamping e reconhecimento obrigatório de alertas históricos.

---

## Arquitetura

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          Mentor CFO — Visão Geral v3                             │
└──────────────────────────────────────────────────────────────────────────────────┘

  CFO (Frontend React · curl · docs)
        │
        │  HTTPS · Bearer JWT
        ▼
┌──────────────────────────────────────┐
│    FastAPI 0.115  :8000              │   /v1/financial-decision-cases
│    (Uvicorn ASGI)                    │   /v1/heuristics
│                                      │   /v1/knowledge-base
│   ┌──────────────────────────────┐   │   /v1/admin
│   │  Anti-Terceirização Cognitiva│   │   /v1/auth/token
│   │  • Hipótese pré-recomendação │   │
│   │  • Rubber-stamp detection    │   │
│   │  • Alert acknowledgment      │   │
│   └──────────────────────────────┘   │
└──────────┬───────────────────────────┘
           │
     ┌─────┴──────────────────┐
     │                        │
     ▼                        ▼
┌────────────────┐   ┌────────────────────────────────────┐
│  JWT Auth      │   │      Engine Determinística          │
│  python-jose   │   │  FinancialImpactScorer              │
└────────────────┘   │  FrameworkSelector (11 frameworks)  │
                     │  Multi-Framework Selection (≤4)     │
                     │  GameTheoryActivator                │
                     │  StateMachineController             │
                     └──────────────┬─────────────────────┘
                                    │
                  ┌─────────────────┴──────────────────┐
                  │                                     │
                  ▼                                     ▼
       ┌──────────────────┐               ┌────────────────────┐
       │    LLM Layer     │               │   PostgreSQL 15     │
       │  PromptBuilder   │               │   (asyncpg)        │
       │  LLMClient       │               │   financial_cases  │
       │  ResponseParser  │               │   decisions        │
       │  LLMCache (Redis)│               │   heuristics       │
       │  FallbackHandler │               │   knowledge_docs   │
       │                  │               │   audit_logs       │
       │  Knowledge Base  │               └────────────────────┘
       │  (doc injection) │
       └────────┬─────────┘
                │
       ┌────────┴──────────┐
       │                   │
       ▼                   ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────────────────┐
│  Anthropic  │   │  Redis 7    │   │  Frontend React         │
│  Claude API │   │  LLM Cache  │   │  Vite + Tailwind        │
│  (Sonnet)   │   │  Token Usage│   │  TanStack Query         │
└─────────────┘   │  TTL 24h    │   │  :3002 → proxy :8000    │
                  └─────────────┘   └─────────────────────────┘
```

---

## Quickstart (< 5 minutos)

### Pré-requisitos
- Docker + Docker Compose
- `jq` (`brew install jq`)
- Chave Anthropic API (`sk-ant-...`)

### 1. Subir a stack

```bash
git clone <repo>
cd c-level/backend

# Configurar variáveis de ambiente
cp .env.example .env          # ou editar .env diretamente
# → Preencher ANTHROPIC_API_KEY e JWT_SECRET_KEY

docker compose up -d          # sobe app + postgres + redis + frontend
docker compose exec app alembic upgrade head   # roda migrations
```

### 2. Acessar o frontend

Abrir http://localhost:3002 no navegador. Login com qualquer username.

### 3. Ou usar via API (curl)

```bash
# Obter token
TOKEN=$(curl -s -X POST http://localhost:8000/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"cfo-user"}' | jq -r '.access_token')

BASE=http://localhost:8000/v1
H="Authorization: Bearer $TOKEN"

# 1. Criar caso (DRAFT)
CASE=$(curl -s -X POST "$BASE/financial-decision-cases" \
  -H "$H" -H "Content-Type: application/json" \
  -d '{
    "title": "Reestruturação da dívida bancária R$ 52M",
    "description": "Renegociação de CCBs com sindicato de bancos — vencimento em abril.",
    "financial_domain": "funding",
    "financial_exposure": 52000000,
    "decision_type": "debt_structuring",
    "external_agents_present": true
  }')
CASE_ID=$(echo $CASE | jq -r '.id')
echo "Caso criado: $CASE_ID"

# 2. Classificar (→ CLASSIFIED | framework: game_theory | score: 5)
curl -s -X PUT "$BASE/financial-decision-cases/$CASE_ID/classify" \
  -H "$H" -H "Content-Type: application/json" \
  -d '{"impact_score": 5}' | jq '{state,framework_selected,scenario_required}'

# 3. Estruturar premissas e riscos (→ STRUCTURED)
curl -s -X PUT "$BASE/financial-decision-cases/$CASE_ID/structure" \
  -H "$H" -H "Content-Type: application/json" \
  -d '{
    "assumptions": [
      "Selic terminal em 10.0-10.5% a.a.",
      "Rating AA- (Fitch) estável durante a negociação",
      "Bancos têm incentivo racional para renegociar dado risco de concentração"
    ],
    "risks": [
      "Colisão tácita entre membros do sindicato antes da negociação bilateral",
      "Downgrade de rating encarecendo spread em 60-80bps",
      "Cláusula cross-default acionada por restructuração de outro passivo"
    ]
  }' | jq '{state,assumptions_count,risks_count}'

# 4. Analisar com o Mentor CFO (→ RECOMMENDED | chama Claude API)
curl -s -X PUT "$BASE/financial-decision-cases/$CASE_ID/analyze" -H "$H" \
  | jq '{state,framework_selected,llm_unavailable,recommendation: .recommendation[:200]}'

# 5. Registrar hipótese pré-recomendação (anti-terceirização cognitiva)
curl -s -X PUT "$BASE/financial-decision-cases/$CASE_ID/hypothesis" \
  -H "$H" -H "Content-Type: application/json" \
  -d '{"initial_hypothesis": "Acredito que a negociação bilateral com os bancos comerciais é mais vantajosa que a multilateral, dado o relacionamento operacional existente."}' \
  | jq .

# 6. Registrar decisão do CFO (→ DECIDED)
curl -s -X PUT "$BASE/financial-decision-cases/$CASE_ID/decide" \
  -H "$H" -H "Content-Type: application/json" \
  -d '{"executive_decision": "Aprovamos a renegociação conforme recomendação do Mentor."}' \
  | jq '{state,divergence_flag}'

# 7. Verificar trilha de auditoria
curl -s "$BASE/financial-decision-cases/$CASE_ID/state-transitions" -H "$H" \
  | jq '.transitions[] | "\(.from_state // "—") → \(.to_state)"'
```

### 4. Testar o smoke test completo

```bash
CFO_API_TOKEN=$TOKEN ./scripts/smoke_test.sh
```

---

## Estrutura do Repositório

```
c-level/
├── README.md                   ← este arquivo
├── WORKPLAN.md                 ← plano de fases e entregas
├── docs/
│   ├── ARCHITECTURE.md         ← arquitetura e decisões técnicas
│   ├── PROTOCOL.md             ← protocolo decisório detalhado
│   └── SIMULATION_RESULTS.md   ← resultados das 5 simulações MVP
├── CFO/                        ← especificações originais (.docx)
│   └── Corrected_v2/           ← especificações atualizadas v2/v3
│       ├── CFO_OpenAPI_v2.yaml ← contrato OpenAPI 3.0 completo
│       └── CFO_Schema_v2.sql   ← schema PostgreSQL completo
├── frontend/                   ← Frontend React (Vite + Tailwind)
│   ├── src/pages/              ← Dashboard, CaseDetail, Login, etc.
│   └── src/components/         ← ActionPanel, Stepper, Modal, etc.
└── backend/
    ├── README.md               ← setup local e referência de API
    ├── app/                    ← código-fonte FastAPI
    ├── tests/                  ← 405+ testes (99% cobertura)
    ├── cases/                  ← casos MVP + resultados + relatórios
    ├── scripts/                ← smoke_test, simulate, validate
    └── docker-compose.yml
```

---

## Documentação

| Documento | Conteúdo |
|---|---|
| [backend/README.md](backend/README.md) | Setup, testes, variáveis de ambiente, referência de endpoints |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arquitetura híbrida, ADRs, fluxo de dados |
| [docs/PROTOCOL.md](docs/PROTOCOL.md) | Protocolo decisório, máquina de estados, regras |
| [docs/SIMULATION_RESULTS.md](docs/SIMULATION_RESULTS.md) | Resultados das 5 simulações, métricas de ganho cognitivo |
| [cases/reports/consolidated_report.md](backend/cases/reports/consolidated_report.md) | Relatório consolidado do MVP — veredicto GO/NO-GO |
| [CFO/Corrected_v2/CFO_OpenAPI_v2.yaml](CFO/Corrected_v2/CFO_OpenAPI_v2.yaml) | Contrato OpenAPI 3.0 — todos os endpoints |

---

## Funcionalidades Principais

### Protocolo Decisório (8 estados)
```
DRAFT → CLASSIFIED → STRUCTURED → ANALYZED → RECOMMENDED → DECIDED → UNDER_REVIEW → CLOSED
```

### Multi-Framework Selection (até 4 frameworks)
O executivo pode selecionar até 4 frameworks analíticos para uma análise integrada:
- PDCA, Análise de Cenários, Teoria dos Jogos, Trade-Off, Matriz de Riscos
- Capital Allocation, Decision Matrix, Cost-Benefit Analysis, Decision Tree, SWOT, Delphi Method

### Anti-Terceirização Cognitiva
1. **Reflexão Pré-Recomendação (P1)** — CFO registra hipótese antes de ver a recomendação da IA
2. **Detecção de Rubber-Stamping (P2)** — Alerta quando decisão é muito similar à recomendação (Jaccard > 70%)
3. **Reconhecimento de Alertas (P4)** — Checkbox obrigatório para confirmar leitura de alertas históricos

### Base de Conhecimento
Upload de documentos regulatórios (PDF, DOCX, TXT, XLSX, XLS, PPTX, CSV, MD) com **validação de relevância** antes do upload — o sistema verifica se o conteúdo é pertinente ao domínio financeiro (determinístico + LLM). Documentos aprovados são injetados no contexto LLM para análises contextualizadas.

### Monitoramento de Créditos API
Banner no Dashboard que monitora o consumo de tokens da API Anthropic via Redis. Alerta âmbar quando o saldo restante atinge US$ 0,50 e alerta vermelho quando esgotado.

### Inteligência Decisória
Dashboard com KPIs: acurácia de forecast, taxa de divergência, eficiência de capital, materialização de riscos — com performance por domínio financeiro.

### Aprendizado Institucional
Heurísticas aprendidas de casos encerrados, alertas baseados em padrões históricos, benchmark comparativo com casos similares.

---

## Status do Projeto

| Fase | Descrição | Status |
|---|---|---|
| P-01 | Scaffold FastAPI | ✅ |
| P-02 | Modelos SQLAlchemy + Migrations | ✅ |
| P-03 | Schemas Pydantic v2 | ✅ |
| P-04 | Engine Determinística | ✅ |
| P-05 | Camada LLM (Claude + Cache + Fallback) | ✅ |
| P-06 | Endpoints REST | ✅ |
| P-07 | Suite de Testes + Validação | ✅ |
| P-08 | Preparação dos Casos MVP | ✅ |
| P-09 | Execução da Simulação + Reports | ✅ |
| P-10 | Learning Module (Heurísticas + Review) | ✅ |
| P-11 | Documentação Final | ✅ |
| P-FE | Frontend React (Vite + Tailwind) | ✅ |
| P-KB | Base de Conhecimento (Upload + LLM) | ✅ |
| P-INT | Inteligência Decisória (Dashboard + Alertas) | ✅ |
| P-ACT | Anti-Terceirização Cognitiva (P1+P2+P4) | ✅ |
| P-KB2 | KB Enhancement (8 formatos + relevância + API balance) | ✅ |

**Total:** 405+ testes | 99% cobertura | 28+ endpoints REST
