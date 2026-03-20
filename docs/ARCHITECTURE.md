# Arquitetura — Mentor CFO

> Documento técnico interno | Público: engenheiros e arquitetos de software

---

## 1. Visão Geral

O Mentor CFO é uma **arquitetura híbrida** que combina dois modos de análise complementares:

| Camada | Responsabilidade | Garantia |
|---|---|---|
| **Engine Determinística** | Classificação, seleção de framework (11 tipos), scoring de impacto, multi-framework selection | 100% reproduzível, sem dependência externa |
| **Camada LLM** | Análise qualitativa, explicitação de premissas, recomendação estruturada, injeção de knowledge base | Contextualizada + fallback automático |
| **Inteligência Decisória** | Alertas heurísticos, benchmark comparativo, KPIs consolidados | Aprendizado institucional acumulado |
| **Anti-Terceirização Cognitiva** | Hipótese pré-recomendação, detecção de rubber-stamping, acknowledgment de alertas | Previne aceitação passiva de IA |

O design garante que **nenhum endpoint de análise falhe** — se o LLM estiver indisponível, o FallbackHandler gera uma resposta determinística baseada no framework selecionado.

---

## 2. Diagrama da Arquitetura

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                         Mentor CFO — Arquitetura Híbrida v3                        │
└────────────────────────────────────────────────────────────────────────────────────┘

  Frontend React (Vite + Tailwind + TanStack Query) :3000
           │
           │  Proxy /v1/* → http://app:8000
           ▼
  CFO / Cliente HTTP  (frontend · curl · integração)
           │
           │  HTTPS · Bearer JWT (HS256)
           ▼
┌────────────────────────────────────────────────────────┐
│   FastAPI 0.115 — Uvicorn ASGI  :8000                  │
│                                                        │
│   /v1/auth/token                   POST                │
│   /v1/financial-decision-cases     POST, GET, GET{id}  │
│   /v1/financial-decision-cases     PATCH reclassify    │
│   /v1/financial-decision-cases     PUT classify|       │
│                                    structure|analyze|  │
│                                    reanalyze|decide|   │
│                                    review|hypothesis   │
│   /v1/financial-decision-cases     GET suggest-methods │
│                                    suggest-reclassif.  │
│                                    heuristic-alerts    │
│                                    state-transitions   │
│   /v1/heuristics                   POST, GET, PUT      │
│   /v1/heuristics/learning-summary  GET                 │
│   /v1/knowledge-base               POST, GET, DEL      │
│   /v1/admin/pending-reviews        GET                 │
│   /v1/admin/decision-intelligence  GET                 │
│   /health                          GET                 │
└────────────┬───────────────────────────────────────────┘
             │
    ┌────────┴────────────────────────────┐
    │                                     │
    ▼                                     ▼
┌──────────────┐             ┌─────────────────────────────────────────┐
│  JWT Auth    │             │        Engine Determinística             │
│  python-jose │             │                                         │
│  HS256       │             │  FinancialImpactScorer                  │
│              │             │    exposure → impact_score (1–5)        │
│  Bearer →    │             │    score ≥ 4 → scenario_required=True   │
│  sub: str    │             │                                         │
└──────────────┘             │  FrameworkSelector                      │
                             │    decision_type + external_agents      │
                             │    → FrameworkType (11 tipos)           │
                             │    + multi-framework suggestions        │
                             │    + rationale em PT-BR                 │
                             │                                         │
                             │  GameTheoryActivator                    │
                             │    eligible_types + external → bool     │
                             │                                         │
                             │  StateMachineController                 │
                             │    VALID_TRANSITIONS grafo linear       │
                             │    → StateTransition + AuditLog         │
                             └────────────────┬────────────────────────┘
                                              │
                        ┌─────────────────────┴──────────────────────┐
                        │                                             │
                        ▼                                             ▼
             ┌──────────────────────┐               ┌───────────────────────────┐
             │      LLM Layer       │               │    PostgreSQL 15 (asyncpg) │
             │                      │               │                           │
             │  PromptBuilder       │               │  financial_decision_cases  │
             │    system_prompt     │               │  financial_assumptions    │
             │    user_prompt       │               │  financial_risks          │
             │    knowledge inject  │               │  financial_metrics_imp.   │
             │                      │               │  decisions                │
             │  LLMClient           │               │    (+ initial_hypothesis) │
             │    asyncio + httpx   │               │  reviews                  │
             │    timeout: 30s      │               │  state_transitions        │
             │                      │               │  audit_logs               │
             │  ResponseParser      │               │  financial_heuristics     │
             │    JSON → dataclass  │               │  knowledge_documents      │
             │                      │               └───────────────────────────┘
             │  LLMCache (Redis)    │
             │    SHA256 key        │
             │    TTL: 24h          │
             │                      │
             │  FallbackHandler     │
             │    determinístico    │
             │    llm_unavailable=T │
             │                      │
             │  LLMService          │
             │    orquestra tudo    │
             └──────────┬───────────┘
                        │
             ┌──────────┴───────────┐
             │                      │
             ▼                      ▼
   ┌─────────────────┐   ┌──────────────────┐
   │  Anthropic API  │   │    Redis 7        │
   │  Claude Sonnet  │   │    LLM Cache      │
   │  (async)        │   │    TTL 24h        │
   └─────────────────┘   └──────────────────┘
```

---

## 3. Fluxo de Dados — Endpoint `/analyze`

O endpoint `PUT /{id}/analyze` é o mais complexo do sistema — percorre todas as camadas:

```
Cliente HTTP
    │
    │ PUT /v1/financial-decision-cases/{id}/analyze
    │ Authorization: Bearer <JWT>
    │ Body (opcional): {"frameworks_selected": ["game_theory", "scenario_analysis"]}
    ▼
FastAPI Router (state_machine.py)
    │
    ├── 1. JWT validation (get_current_user)
    ├── 2. Load FinancialDecisionCase + assumptions + risks (selectinload)
    │
    ├── 3. StateMachineController.transition(ANALYZED)
    │       → StateTransition record
    │       → AuditLog: STATE_TRANSITION
    │
    ├── 4. GameTheoryActivator.is_active(decision_type, external_agents_present)
    │       → game_theory_active: bool
    │
    ├── 5. Multi-Framework Resolution
    │       ├── Se body com frameworks_selected → usar seleção do executivo
    │       └── Se sem body → usar framework padrão da engine
    │
    ├── 6. Knowledge Base Injection
    │       → Query knowledge_documents WHERE domain+type+active
    │       → Injetar textos relevantes no prompt como contexto adicional
    │
    ├── 7. PromptBuilder.build(PromptContext)
    │       → system_prompt (invariante)
    │       → user_prompt (decision_type + exposure + frameworks + assumptions + risks + knowledge)
    │
    ├── 8. LLMService.analyze(ctx, session, triggered_by)
    │       │
    │       ├── 8a. LLMCache.get(cache_key)  ←── SHA256 do user_prompt
    │       │       ✓ HIT  → ResponseParser.parse(cached_json) → LLMAnalysisResult
    │       │       ✗ MISS → continua
    │       │
    │       ├── 8b. LLMClient.call(system, user)  [timeout 30s]
    │       │       ✓ OK   → ResponseParser.parse(response_text)
    │       │                 AuditLog: LLM_CALLED
    │       │                 LLMCache.set(cache_key, result, ttl=86400)
    │       │       ✗ FAIL → FallbackHandler.handle(ctx)
    │       │                 AuditLog: LLM_FALLBACK
    │       │                 llm_unavailable = True
    │       │
    │       └── retorna LLMAnalysisResult
    │
    ├── 9.  Persist FinancialMetricImpacted (bulk session.add)
    ├── 10. Persist implicit FinancialAssumption (is_implicit=True)
    ├── 11. Persist Decision (recommendation)
    │
    ├── 12. StateMachineController.transition(RECOMMENDED)
    │        → StateTransition record
    │        → AuditLog: STATE_TRANSITION
    │
    └── 13. Return AnalysisResponse (HTTP 200)
            state, recommendation, framework_selected, primary_framework,
            frameworks_selected, financial_metrics_impacted, scenario_summary,
            implicit_assumptions_found, game_theory_model, llm_unavailable
```

---

## 4. Fluxo de Dados — Endpoint `/review` (Learning Module)

```
Cliente HTTP
    │
    │ PUT /v1/financial-decision-cases/{id}/review
    │ Body: { outcome_summary, forecast_accuracy_score, risk_realization_rate, ... }
    ▼
FastAPI Router (state_machine.py)
    │
    ├── 1. Se state=DECIDED → transition(UNDER_REVIEW)
    ├── 2. transition(CLOSED)
    │
    ├── 3. ReviewService.compute_divergence_outcome(case, score, session)
    │       → Query Decision WHERE divergence_flag=True
    │         SE divergence_flag=True AND forecast_accuracy_score < 5
    │         → divergence_outcome_flag = True  (divergência resultou em pior outcome)
    │
    ├── 4. ReviewService.update_risk_materialization(case, rate, session)
    │       → SE risk_realization_rate > 50%
    │         → UPDATE financial_risks SET materialized=True
    │
    ├── 5. Persist Review (outcome + métricas)
    │
    ├── 6. HeuristicsService.auto_generate(case, review, session)
    │       → Gerar heurísticas automaticamente a partir dos resultados
    │       → AuditLog: HEURISTIC_GENERATED
    │
    └── 7. Return ReviewResponse { state: CLOSED, divergence_outcome_flag, heuristics_generated }
```

---

## 5. Fluxo Anti-Terceirização Cognitiva

```
Caso atinge RECOMMENDED
    │
    ├── Frontend exibe análise (frameworks, premissas, métricas, cenários)
    │   MAS OCULTA a recomendação da IA
    │
    ├── P1 — Hipótese Pré-Recomendação
    │   │   CFO digita sua leitura inicial (mín. 30 chars)
    │   │   PUT /hypothesis → grava initial_hypothesis no Decision
    │   │   Frontend REVELA a recomendação (transição CSS opacity)
    │   │
    │   └── Reload guard: se initial_hypothesis já existe, auto-reveal
    │
    ├── P4 — Reconhecimento de Alertas
    │   │   GET /heuristic-alerts → alertas de casos similares
    │   │   Se há alertas → checkbox obrigatório antes de decidir
    │   │   "Li e considerei os alertas históricos acima"
    │   │
    │   └── Edge: sem alertas → checkbox não aparece; query falhou → não bloqueia
    │
    └── P2 — Detecção de Rubber-Stamping
        │   CFO digita executive_decision
        │   jaccardSimilarity(decision, recommendation) > 0.70 ?
        │   → Modal: "Sua decisão é muito similar à recomendação da IA."
        │     • "Sim, considerei" → prossegue
        │     • "Quero revisar" → volta ao form
        │
        └── Frontend-only (textSimilarity.js)
```

---

## 6. Modelo de Dados

```
financial_decision_cases ────────────────────────────────────────┐
  id (UUID PK)                                                    │
  title, description                                              │
  financial_domain (enum: planning|reporting|treasury|funding|risk)│
  decision_type (enum: 8 tipos)                                   │
  financial_exposure (Numeric 18,2)                               │
  time_horizon (enum: short|medium|long)                          │
  external_agents_present (bool)                                  │
  impact_score (int 1-5)                                          │
  framework_selected (enum: 11 tipos)                             │
  state (enum DecisionState: 8 estados)                           │
  created_at, updated_at (naive UTC)                              │
     │                                                            │
     ├─── financial_assumptions (1:N)                             │
     │      text, is_implicit (bool), created_at                  │
     │                                                            │
     ├─── financial_risks (1:N)                                   │
     │      text, materialized (bool), created_at                 │
     │                                                            │
     ├─── financial_metrics_impacted (1:N)                        │
     │      metric_name, created_at                               │
     │                                                            │
     ├─── decisions (1:N)                                         │
     │      recommendation (text)                                 │
     │      initial_hypothesis (text nullable) [v3]               │
     │      executive_decision (text nullable)                    │
     │      divergence_flag (bool)                                │
     │                                                            │
     ├─── reviews (1:N)                                           │
     │      outcome_summary, forecast_accuracy_score (1-10)       │
     │      risk_realization_rate (float %)                       │
     │      capital_allocation_efficiency_score (float %)         │
     │      divergence_outcome_flag (bool)                        │
     │                                                            │
     ├─── state_transitions (1:N)                                 │
     │      from_state → to_state, triggered_by, transitioned_at  │
     │                                                            │
     └─── audit_logs (1:N)                                        │
            action (enum AuditAction), payload (JSONB)            │
            created_at                                            │
                                                                  │
financial_heuristics ─────────────────────────────────────────────┘
  id (UUID PK)
  decision_type (enum), financial_domain (enum)
  heuristic_key (str), heuristic_value (JSONB)
  source_case_id (UUID FK nullable → financial_cases)
  active (bool, default True)
  created_at, updated_at
  UNIQUE(decision_type, financial_domain, heuristic_key)

knowledge_documents ──────────────────────────────────────────────
  id (UUID PK)
  title, description, original_filename
  file_type (pdf|docx|txt), file_size_bytes (≤10MB)
  extracted_text (TEXT), text_length (INT)
  financial_domain (enum), decision_type (enum nullable)
  active (bool), uploaded_by (text nullable)
  created_at, updated_at
  INDEX(financial_domain, decision_type, active)
```

**Invariantes do modelo:**
- `financial_heuristics` é **INSERT-only**: não existe `DELETE`, apenas `deactivate` (active=False)
- `state_transitions` é **append-only**: representa a trilha histórica completa
- `audit_logs` é **append-only**: nunca é modificado, apenas inserido (regras SQL: no UPDATE, no DELETE)
- `knowledge_documents` usa **soft delete**: `active=False` (nunca remove fisicamente)
- `decisions.initial_hypothesis` é registrado **antes** de revelar a recomendação ao CFO

---

## 7. Decisões Técnicas (ADRs Simplificados)

### ADR-01 — FastAPI + asyncpg (não Django, não psycopg2)

**Contexto:** API para decisões financeiras de alto valor com integração LLM.

**Decisão:** FastAPI com SQLAlchemy async + asyncpg.

**Justificativa:**
- Endpoints de análise fazem chamadas LLM com timeout de 30s — async é obrigatório para não bloquear o event loop
- FastAPI gera OpenAPI 3.1 automaticamente (compatível com o spec CFO v2)
- Pydantic v2 já integrado nativamente, sem adaptador adicional

**Consequência:** Todos os testes de integração usam `AsyncMock` para simular a sessão do banco.

---

### ADR-02 — Engine Determinística antes do LLM

**Contexto:** O LLM pode estar indisponível ou retornar respostas incoerentes.

**Decisão:** A engine determinística (ImpactScorer, FrameworkSelector, GameTheoryActivator) sempre executa **antes** da chamada LLM, e seus resultados alimentam o prompt.

**Justificativa:**
- Garante que `framework_selected`, `impact_score` e `game_theory_active` sejam sempre consistentes, independente do LLM
- O prompt é mais específico e estruturado quando parte de dados determinísticos
- Em caso de fallback, o FallbackHandler usa exatamente esses campos para gerar uma resposta coerente

**Consequência:** `llm_unavailable=True` nunca impede a transição de estado — o caso sempre avança.

---

### ADR-03 — Redis como cache LLM (não banco relacional)

**Contexto:** Prompts idênticos para o mesmo caso podem ser chamados repetidamente (retry, testes).

**Decisão:** Cache Redis com chave SHA256 do `user_prompt`, TTL de 24h.

**Justificativa:**
- Prompts LLM têm custo por token — reusar resultado em cache poupa custo sem degradar qualidade
- TTL de 24h garante que casos relevantes sejam re-analisados com o estado mais recente das premissas
- Redis é in-memory e não polui o banco relacional com dados transitórios

**Consequência:** Se o Redis estiver indisponível, `LLMCache.get()` retorna `None` silenciosamente e a chamada LLM prossegue normalmente (falha aberta, não fechada).

---

### ADR-04 — Heurísticas INSERT-only (sem DELETE)

**Contexto:** O Learning Module acumula heurísticas aprendidas de casos reais.

**Decisão:** `financial_heuristics` aceita apenas INSERT e UPDATE de `active=False`. Nunca DELETE.

**Justificativa:**
- Heurísticas representam conhecimento organizacional acumulado — deletar seria perda irreversível de aprendizado
- `active=False` permite auditoria de por que uma heurística foi desativada
- O histórico completo de heurísticas (ativas e inativas) tem valor analítico futuro

**Consequência:** A tabela cresce monotonicamente. Uma estratégia de arquivamento deve ser planejada para escala.

---

### ADR-05 — JWT sem banco de usuários (MVP)

**Contexto:** O MVP é para uso interno do CFO — não requer multi-tenancy ou gestão de usuários.

**Decisão:** JWT assinado com `JWT_SECRET_KEY` (HS256), sem tabela de usuários no banco. Endpoint `POST /auth/token` aceita qualquer username.

**Justificativa:**
- Simplifica o deploy (sem migration de `users`, sem gestão de senhas)
- Para o escopo do MVP, o `sub` do JWT identifica o ator suficientemente para fins de auditoria
- Tokens com `exp` curta (8h padrão) limitam o risco de vazamento

**Consequência:** Revogação de tokens individuais não é possível. Ao rotacionar `JWT_SECRET_KEY`, todos os tokens existentes tornam-se inválidos.

---

### ADR-06 — Pydantic v2 schemas em arquivo único

**Contexto:** ~30 schemas de request/response para o protocolo decisório.

**Decisão:** Todos os schemas em `app/schemas/__init__.py` com `__all__` explícito.

**Justificativa:**
- Facilita descoberta e manutenção — um arquivo, uma busca
- `__all__` evita importações acidentais de objetos internos
- O volume atual (~600 linhas) não justifica fragmentação em múltiplos arquivos

**Consequência:** Se o número de schemas crescer significativamente (>40), migrar para `app/schemas/` como pacote.

---

### ADR-07 — Anti-Terceirização Cognitiva (frontend-first)

**Contexto:** Risco de "obesidade de IA" — CFOs aceitando recomendações da IA sem reflexão.

**Decisão:** 3 mecanismos de fricção reflexiva:
1. **Hipótese pré-recomendação (backend):** `initial_hypothesis` registrado antes de revelar a recomendação
2. **Detecção de rubber-stamping (frontend):** Jaccard similarity > 0.70 → modal de confirmação
3. **Reconhecimento de alertas (frontend):** Checkbox obrigatório se há alertas heurísticos

**Justificativa:**
- P2 e P4 são implementados puramente no frontend para não adicionar complexidade ao backend
- P1 requer persistência (`initial_hypothesis`) para auditoria posterior ("o que eu pensava antes")
- O threshold de 0.70 no Jaccard foi calibrado empiricamente para evitar falsos positivos

**Consequência:** A recomendação fica oculta até o CFO registrar sua hipótese. O campo `initial_hypothesis` permite comparar "hipótese do CFO" vs "recomendação da IA" vs "decisão tomada" em análise retrospectiva.

---

### ADR-08 — Multi-Framework Selection (até 4)

**Contexto:** O framework único limita a análise de casos complexos.

**Decisão:** O executivo pode selecionar até 4 frameworks de um catálogo de 11 (engine sugere, executivo confirma/customiza).

**Justificativa:**
- Casos com alta exposição se beneficiam de múltiplas lentes analíticas
- O LLM sintetiza a recomendação integrando todos os frameworks selecionados
- Limite de 4 para evitar diluição da síntese

**Consequência:** O endpoint `GET /suggest-methods` retorna sugestões com rationale; `PUT /analyze` aceita opcionalmente `frameworks_selected`.

---

## 8. Stack Tecnológico

| Componente | Tecnologia | Versão |
|---|---|---|
| Framework web | FastAPI | 0.115 |
| ASGI server | Uvicorn | 0.32 |
| ORM | SQLAlchemy (async) | 2.0 |
| Driver DB | asyncpg | 0.30 |
| Banco de dados | PostgreSQL | 15 |
| Cache | Redis | 7 |
| Validação de dados | Pydantic | 2.x |
| Auth | python-jose | 3.3 |
| LLM | Claude Sonnet (Anthropic) | claude-sonnet-4-6 |
| Migrations | Alembic | 1.14 |
| Testes | pytest + pytest-asyncio | 8.x |
| Containerização | Docker + Compose | 24.x |
| Python | CPython | 3.11+ |
| Frontend | React | 18 |
| Build tool | Vite | 5.x |
| CSS | Tailwind CSS | 3.x |
| Data fetching | TanStack Query | 5.x |
| Routing | React Router | 6.x |
