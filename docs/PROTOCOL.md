# Protocolo Decisório — Mentor CFO

> Documento de processo interno | Público: CFOs, diretores financeiros e analistas sênior

---

## 1. Fundamento

O Mentor CFO impõe um **protocolo decisório mandatório** para decisões financeiras de alto impacto. Nenhuma decisão relevante deve ser tomada sem:

1. **Premissas explícitas** — o que precisa ser verdade para que a decisão faça sentido
2. **Riscos identificados** — o que pode dar errado e qual o grau de materialização
3. **Análise multi-framework** — até 4 frameworks analíticos combinados (PDCA, Game Theory, Risk Matrix, Cenários, Decision Tree, SWOT, Delphi, etc.)
4. **Hipótese pré-recomendação** — o CFO registra sua leitura antes de ver a recomendação da IA (anti-terceirização cognitiva)
5. **Recomendação registrada** — orientação formal do Mentor antes da decisão executiva
6. **Alertas heurísticos reconhecidos** — padrões aprendidos de casos anteriores confirmados pelo CFO
7. **Decisão auditada** — o que o CFO decidiu, com justificativa se divergir da recomendação
8. **Revisão pós-decisão** — resultado real vs projetado, alimentando o aprendizado institucional

---

## 2. Ciclo de Vida de uma Decisão

Toda decisão percorre obrigatoriamente os seguintes estados, nesta ordem:

```
  ┌─────────┐
  │  DRAFT  │  Caso criado, sem análise
  └────┬────┘
       │  PUT /classify  (impact_score obrigatório)
       ▼
┌────────────┐
│ CLASSIFIED │  Framework analítico selecionado automaticamente
└─────┬──────┘
      │  PUT /structure  (mínimo 3 premissas + 3 riscos)
      ▼
┌────────────┐
│ STRUCTURED │  Premissas e riscos registrados
└─────┬──────┘
      │  GET /suggest-methods (opcional: ver frameworks sugeridos)
      │  PUT /analyze  (chama engine + LLM com multi-framework)
      ▼
┌──────────┐
│ ANALYZED │  Fase intermediária automática (análise em processamento)
└────┬─────┘
     │  automático (ao fim do /analyze)
     ▼
┌─────────────┐
│ RECOMMENDED │  Recomendação do Mentor disponível
└──────┬──────┘
       │  PUT /hypothesis  (hipótese do CFO ANTES de ver a recomendação)
       │  GET /heuristic-alerts  (alertas + benchmark de casos similares)
       │  PUT /decide  (decisão executiva obrigatória)
       ▼
┌─────────┐
│ DECIDED │  CFO registrou a decisão tomada
└────┬────┘
     │  Automático após 90 dias (ReviewTrigger)
     ▼
┌──────────────┐
│ UNDER_REVIEW │  Caso marcado para revisão de outcome
└──────┬───────┘
       │  PUT /review  (resultado real da decisão)
       ▼
┌────────┐
│ CLOSED │  Ciclo completo — aprendizado registrado
└────────┘
```

**Regras do grafo:**
- Cada estado tem **exatamente um** sucessor permitido
- Qualquer tentativa de pular estados retorna HTTP 409 (Conflict)
- `CLOSED` é **terminal** — nenhuma transição adicional é aceita
- A transição `DECIDED → UNDER_REVIEW` é acionada automaticamente pelo `ReviewTrigger` após 90 dias

---

## 3. Etapas em Detalhe

### Etapa 1 — DRAFT (Criar o caso)

**Endpoint:** `POST /v1/financial-decision-cases`

**Campos obrigatórios:**
| Campo | Tipo | Descrição |
|---|---|---|
| `title` | string (5+ chars) | Título descritivo da decisão |
| `description` | string (20+ chars) | Contexto e motivação |
| `financial_domain` | enum | Domínio financeiro (ver tabela abaixo) |
| `financial_exposure` | float > 0 | Valor em BRL exposto à decisão |
| `decision_type` | enum | Tipo de decisão (ver tabela abaixo) |

**Campos opcionais:**
| Campo | Tipo | Default |
|---|---|---|
| `time_horizon` | enum | — |
| `external_agents_present` | bool | `false` |

**Domínios financeiros (`financial_domain`):**

| Valor | Descrição |
|---|---|
| `planning` | Planejamento orçamentário |
| `reporting` | Controladoria e reporting financeiro |
| `treasury` | Tesouraria e gestão de caixa |
| `funding` | Captação e estrutura de capital |
| `risk` | Gestão de riscos financeiros |

**Tipos de decisão (`decision_type`):**

| Valor | Framework padrão | Game Theory elegível? |
|---|---|---|
| `budget_adjustment` | PDCA | Não |
| `forecast_revision` | Análise de Cenários | Não |
| `capital_allocation` | Capital Allocation | Sim |
| `debt_structuring` | Trade-Off | Sim |
| `liquidity_management` | Matriz de Riscos | Não |
| `risk_hedging` | Matriz de Riscos | Não |
| `cost_reduction` | Trade-Off | Não |
| `investment_evaluation` | Análise de Cenários | Sim |

---

### Etapa 2 — CLASSIFIED (Classificar o impacto)

**Endpoint:** `PUT /v1/financial-decision-cases/{id}/classify`

**Body:**
```json
{ "impact_score": 5 }
```

**Faixas de impacto:**

| Score | Classificação | Faixa de Exposição (BRL) | Cenários obrigatórios? |
|---|---|---|---|
| 1 | Baixo | < R$ 100 mil | Não |
| 2 | Moderado | R$ 100 mil – R$ 500 mil | Não |
| 3 | Relevante | R$ 500 mil – R$ 2 milhões | Não |
| 4 | Alto | R$ 2 milhões – R$ 10 milhões | **Sim** |
| 5 | Crítico | > R$ 10 milhões | **Sim** |

**Seleção de framework:** Automática e determinística.

- Se `external_agents_present=true` **e** `decision_type ∈ {debt_structuring, investment_evaluation, capital_allocation}` → **Teoria dos Jogos** (sobrescreve o mapeamento base)
- Caso contrário → mapeamento base por `decision_type` (ver tabela acima)

**Sugestão de reclassificação:** Após classificar, o sistema pode sugerir reclassificação via LLM:
- `GET /{id}/suggest-reclassification` → analisa descrição vs classificação atual
- `PATCH /{id}/reclassify` → aplica reclassificação se aceita

---

### Etapa 3 — STRUCTURED (Registrar premissas e riscos)

**Endpoint:** `PUT /v1/financial-decision-cases/{id}/structure`

**Regras de validação (obrigatórias):**
- Mínimo **3 premissas** financeiras explícitas
- Mínimo **3 riscos** financeiros identificados

**Dica de qualidade:** Premissas devem ser **falsificáveis** — preferir "Selic estável em 10,75% no semestre" a "juros estáveis". Riscos devem ser **mensuráveis** — preferir "queda de 3pp de market share em Q3" a "perda de clientes".

---

### Etapa 3.5 — Multi-Framework Selection (opcional)

**Endpoint:** `GET /v1/financial-decision-cases/{id}/suggest-methods`

Após estruturar o caso, o executivo pode visualizar as sugestões de frameworks:

```json
{
  "primary_framework": "game_theory",
  "suggested_frameworks": ["game_theory", "scenario_analysis"],
  "suggestions_rationale": {
    "game_theory": "Agentes externos presentes + tipo debt_structuring → modelar interações estratégicas.",
    "scenario_analysis": "Exposição > R$ 2M com cenários obrigatórios — quantificar impacto em 3 cenários."
  },
  "available_frameworks": ["pdca", "trade_off", "risk_matrix", "capital_allocation", ...]
}
```

O executivo pode adicionar/remover frameworks (máximo 4, mínimo 1 — o principal é obrigatório) e enviar a seleção no body do `/analyze`.

**11 frameworks disponíveis:**
- `pdca` — Plan-Do-Check-Act
- `scenario_analysis` — Análise de Cenários (Pessimista/Base/Otimista)
- `game_theory` — Teoria dos Jogos (players, strategies, payoffs, Nash)
- `trade_off` — Análise de Trade-Off
- `risk_matrix` — Matriz de Riscos (probabilidade × impacto)
- `capital_allocation` — Alocação de Capital
- `decision_matrix` — Matriz de Decisão (critérios ponderados)
- `cost_benefit_analysis` — Análise Custo-Benefício
- `decision_tree` — Árvore de Decisão (EMV)
- `swot_analysis` — SWOT (Forças, Fraquezas, Oportunidades, Ameaças)
- `delphi_method` — Método Delphi (consenso estruturado)

---

### Etapa 4 — ANALYZED → RECOMMENDED (Análise do Mentor)

**Endpoint:** `PUT /v1/financial-decision-cases/{id}/analyze`

**Body (opcional):**
```json
{ "frameworks_selected": ["game_theory", "scenario_analysis"] }
```

Se omitido, usa o framework padrão da engine.

**O que o Mentor faz:**
1. Monta o prompt com os frameworks selecionados, premissas, riscos e contexto financeiro
2. Injeta documentos relevantes da Base de Conhecimento (se existirem para o domínio/tipo)
3. Ativa Teoria dos Jogos se elegível (adiciona players, strategies, payoffs, equilibrium ao prompt)
4. Chama Claude Sonnet (Anthropic API) com cache Redis de 24h
5. Em caso de falha do LLM: FallbackHandler gera análise determinística (llm_unavailable=True)
6. Persiste premissas implícitas identificadas pelo LLM (is_implicit=True)
7. Persiste métricas financeiras impactadas
8. Cria registro `Decision` com a recomendação

**Reanálise:** Se o caso precisar ser reanalisado (ex: após reclassificação), usar `PUT /{id}/reanalyze`.

---

### Etapa 4.5 — Anti-Terceirização Cognitiva

Quando o caso atinge `RECOMMENDED`, três mecanismos de fricção reflexiva são ativados:

#### P1 — Hipótese Pré-Recomendação

**Endpoint:** `PUT /v1/financial-decision-cases/{id}/hypothesis`

```json
{ "initial_hypothesis": "Acredito que a negociação bilateral é mais vantajosa dado o relacionamento operacional existente com os bancos comerciais." }
```

- Mínimo 30 caracteres
- Registrado ANTES de o CFO ver a recomendação da IA
- No frontend, a recomendação fica oculta até a hipótese ser registrada
- Permite comparação retrospectiva: "o que eu pensava" vs "o que a IA disse" vs "o que eu decidi"

#### P4 — Reconhecimento de Alertas

**Endpoint:** `GET /v1/financial-decision-cases/{id}/heuristic-alerts`

Retorna alertas baseados em heurísticas de casos similares (mesmo domínio + tipo):

```json
{
  "alerts": [
    {
      "alert_type": "pattern_warning",
      "severity": "high",
      "message": "Em 3 casos similares de debt_structuring, a negociação multilateral resultou em spread 40bps maior que a bilateral.",
      "confidence": 0.87,
      "source_heuristic_ids": ["uuid-1"]
    }
  ],
  "total": 1,
  "benchmark": {
    "total_similar_cases": 5,
    "followed_recommendation_count": 4,
    "followed_recommendation_pct": 80.0,
    "avg_forecast_accuracy": 8.8
  }
}
```

No frontend, se há alertas, o CFO deve marcar um checkbox confirmando que os leu antes de poder decidir.

#### P2 — Detecção de Rubber-Stamping

Implementado no frontend. Se a decisão executiva tem similaridade > 70% (Jaccard) com a recomendação, um modal é exibido:

> "Sua decisão é muito similar à recomendação da IA. Você considerou cenários alternativos?"

O CFO pode confirmar ("Sim, considerei") ou revisar ("Quero revisar").

---

### Etapa 5 — DECIDED (Registrar a decisão executiva)

**Endpoint:** `PUT /v1/financial-decision-cases/{id}/decide`

**Body mínimo (alinhamento total):**
```json
{
  "executive_decision": "Aprovamos a renegociação conforme recomendação do Mentor."
}
```

**Body com divergência:**
```json
{
  "executive_decision": "Optamos por apenas 60% da reestruturação recomendada.",
  "divergence_justification": "Contexto geopolítico exige postura conservadora no curto prazo.",
  "monitoring_criteria": [
    "DRE trimestral vs. projeção base",
    "Covenant de DSCR mínimo 1,2x",
    "Rating Fitch — qualquer mudança de outlook"
  ]
}
```

**Como registrar divergência:**
- Forneça `divergence_justification` com a razão da divergência
- `divergence_flag=True` é registrado automaticamente quando `divergence_justification` está presente
- `monitoring_criteria` lista as métricas que o CFO se compromete a monitorar
- Divergências geram `AuditLog` com `action=DIVERGENCE_RECORDED`

---

### Etapa 6 — CLOSED (Registrar o outcome real)

**Endpoint:** `PUT /v1/financial-decision-cases/{id}/review`

Pode ser chamado a partir de `DECIDED` ou `UNDER_REVIEW`. Se o estado for `DECIDED`, a transição `DECIDED → UNDER_REVIEW → CLOSED` ocorre automaticamente.

**Body:**
```json
{
  "outcome_summary": "Redução do custo médio de 14,9% para 12,4% a.a. DSCR de 1,18x → 1,41x.",
  "forecast_accuracy_score": 9,
  "risk_realization_rate": 10.0,
  "capital_allocation_efficiency_score": 94.0
}
```

**Campos do review:**

| Campo | Tipo | Escala | Descrição |
|---|---|---|---|
| `outcome_summary` | string | — | Resumo qualitativo do resultado real |
| `forecast_accuracy_score` | int | 1–10 | Precisão das premissas: 10 = totalmente acuradas |
| `risk_realization_rate` | float | 0–100% | % dos riscos identificados que se materializaram |
| `capital_allocation_efficiency_score` | float | 0–100% | Eficiência da alocação de capital realizada |

**Cálculo automático do `divergence_outcome_flag`:**
- `True` quando: `divergence_flag=True` no `Decision` E `forecast_accuracy_score < 5`
- Indica que a divergência piorou o outcome

**Materialização automática de riscos:**
- Se `risk_realization_rate > 50%` → todos os riscos do caso são marcados como `materialized=True`

**Geração automática de heurísticas:**
- Ao fechar o review, heurísticas são geradas automaticamente a partir dos resultados
- O campo `heuristics_generated` na resposta indica quantas foram criadas

---

## 4. Trilha de Auditoria

**Endpoint:** `GET /v1/financial-decision-cases/{id}/state-transitions`

Retorna o histórico completo de todas as transições de estado.

---

## 5. Base de Conhecimento

O Mentor CFO permite upload de documentos regulatórios e políticas internas que são injetados no contexto LLM para análises mais contextualizadas.

### Upload de documento

```bash
curl -X POST "$BASE/knowledge-base/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@politica_risco.pdf" \
  -F "title=Política de Gestão de Riscos 2026" \
  -F "financial_domain=risk" \
  -F "decision_type=risk_hedging"
```

Tipos aceitos: PDF, DOCX, TXT. Limite: 10 MB por arquivo.

### Listagem e consulta

```bash
# Listar documentos ativos
curl "$BASE/knowledge-base?domain=risk" -H "Authorization: Bearer $TOKEN"

# Obter documento com texto extraído
curl "$BASE/knowledge-base/{id}" -H "Authorization: Bearer $TOKEN"
```

---

## 6. Learning Module — Heurísticas

O Mentor CFO aprende com as decisões fechadas e armazena heurísticas reutilizáveis.

### Resumo de aprendizado

```bash
curl "$BASE/heuristics/learning-summary" -H "Authorization: Bearer $TOKEN"
```

### Criar/consultar/desativar heurísticas

```bash
# Criar heurística manual
curl -X POST "$BASE/heuristics" -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "decision_type": "debt_structuring",
    "financial_domain": "funding",
    "heuristic_key": "bilateral_negotiation_over_syndicate",
    "heuristic_value": {
      "pattern": {"trigger": "external_agents_present=true AND num_creditors >= 3"},
      "confidence": 0.87
    }
  }'

# Listar heurísticas por contexto
curl "$BASE/heuristics?decision_type=debt_structuring&domain=funding" \
  -H "Authorization: Bearer $TOKEN"

# Desativar
curl -X PUT "$BASE/heuristics/{id}/deactivate" -H "Authorization: Bearer $TOKEN"
```

**Regra invariante:** Heurísticas **nunca são deletadas**. `deactivate` marca `active=False`.

---

## 7. Inteligência Decisória

### Dashboard de KPIs

```bash
curl "$BASE/admin/decision-intelligence" -H "Authorization: Bearer $TOKEN"
```

Retorna:
- Acurácia média de forecast
- Taxa de divergência bem-sucedida
- Materialização de riscos
- Eficiência de capital
- Performance por domínio financeiro
- Frameworks mais utilizados

### Casos pendentes de review

```bash
curl "$BASE/admin/pending-reviews" -H "Authorization: Bearer $TOKEN"
```

Lista casos `DECIDED` há mais de 90 dias sem review.

---

## 8. Erros e Códigos HTTP

| Código | `error` (machine) | Situação |
|---|---|---|
| 401 | `UNAUTHORIZED` | Token JWT ausente, inválido ou expirado |
| 404 | `CASE_NOT_FOUND` | ID do caso não existe |
| 404 | `HEURISTIC_NOT_FOUND` | ID da heurística não existe |
| 404 | `DOCUMENT_NOT_FOUND` | ID do documento não existe |
| 409 | `INVALID_STATE_TRANSITION` | Tentativa de transição inválida |
| 413 | `DOCUMENT_TOO_LARGE` | Documento excede 10 MB |
| 415 | `UNSUPPORTED_FILE_TYPE` | Tipo de arquivo não suportado |
| 422 | `INSUFFICIENT_ASSUMPTIONS` | Menos de 3 premissas no `/structure` |
| 422 | `INSUFFICIENT_RISKS` | Menos de 3 riscos no `/structure` |
| 422 | `DOCUMENT_EXTRACTION_ERROR` | Falha ao extrair texto do documento |

**Formato do erro:**
```json
{
  "error": "INVALID_STATE_TRANSITION",
  "message": "Transição inválida: DRAFT → DECIDED"
}
```
