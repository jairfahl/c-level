# Casos de Simulação MVP — CFO Mentor C-Level
**Versão:** 2.0 | **Data:** Março 2026 | **Empresa:** Vértice Alimentos S.A. (representativa)

> Empresa de referência: mid-size agroindústria brasileira, ~R$ 480M de receita anual,
> listada no Novo Mercado da B3, com operações no Centro-Oeste e Nordeste.

---

## Sumário dos Casos

| # | Título | Domínio | Tipo | Exposição (R$) | Score | Agentes Ext. | Framework |
|---|--------|---------|------|---------------|-------|--------------|-----------|
| 1 | Realocação Orçamentária Q2 | planning | budget_adjustment | 380.000 | 2 | Não | PDCA |
| 2 | Renegociação CCB Sindicato | funding | debt_structuring | 52.000.000 | 5 | **Sim** | **Game Theory** |
| 3 | Gap de Liquidez Q4 | treasury | liquidity_management | 3.800.000 | 4 | Não | Risk Matrix |
| 4 | CAPEX Planta Recife | funding | investment_evaluation | 18.000.000 | 5 | **Sim** | **Game Theory** |
| 5 | Revisão Forecast Q3 | reporting | forecast_revision | 1.200.000 | 3 | Não | Scenario Analysis |

**Restrições satisfeitas:**
- ✅ Casos com impact_score ≥ 4 (scenario_required=true): Casos 2, 3, 4 (3 de 5)
- ✅ Casos com external_agents_present=true: Casos 2 e 4 (Game Theory ativada)

---

## Caso 1 — Realocação Orçamentária Q2: COGS vs. Marketing

### Ficha Técnica
```
financial_domain  : planning
decision_type     : budget_adjustment
financial_exposure: R$ 380.000
time_horizon      : short
external_agents   : false
impact_score      : 2
framework         : PDCA
scenario_required : false
```

### Seção A — Racional Original

Email da Diretoria de Operações, maio do exercício corrente. O COGS de proteína animal registrou overrun de R$ 380k no acumulado do semestre, causado pela estiagem no Centro-Oeste que elevou o farelo de soja em 22% vs. orçamento original aprovado em dezembro.

O CFO convocou reunião de revisão orçamentária mid-year para realocar verba. **Alternativas avaliadas:** (a) corte de headcount — descartado por risco operacional; (b) postergação de capex menor — aprovado parcialmente; (c) corte de ativações de trade marketing no varejo regional. O diretor de marketing resistiu à opção (c), argumentando com o pipeline de Q3 no Nordeste.

**Decisão tomada:** Realocação de R$ 380k do budget de trade marketing regional para cobertura integral do overrun. Campanhas de Q3 no Nordeste postergadas para Q1 do exercício seguinte. Revisão de preços de tabela em +2,5% aprovada concomitantemente para recuperação parcial de margem.

**Resultado real:** EBITDA margin encerrou o semestre em 13,4%, vs. 13,1% projetado pós-realocação. A postergação das ativações gerou queda de 1,8pp de market share no canal regional em Q3, recuperado em Q1 seguinte conforme planejado.

### Premissas Identificadas no Racional Original
1. O preço do farelo de soja estabiliza no patamar atual
2. A postergação das ativações não gera perda permanente de shelf space
3. O reajuste de +2,5% é absorvido pelo canal sem perda relevante de volume

### Riscos Mencionados no Racional Original
1. Nova alta de commodities pode ampliar o overrun além dos R$ 380k
2. Perda de market share para concorrentes durante ausência das ativações

---

## Caso 2 — Renegociação de CCBs: Sindicato de Bancos R$ 52M

### Ficha Técnica
```
financial_domain  : funding
decision_type     : debt_structuring
financial_exposure: R$ 52.000.000
time_horizon      : long
external_agents   : true  ← Itaú BBA, Bradesco BBI, BTG Pactual
impact_score      : 5
framework         : game_theory  ← ativado por debt_structuring + external_agents
scenario_required : true
```

### Seção A — Racional Original

Apresentação ao Comitê de Finanças, setembro. Três Cédulas de Crédito Bancário (CCBs) totalizando R$ 52M com vencimento concentrado em abril, contratadas em ambiente de Selic a 13,75% a.a. Com a Selic em trajetória de queda para 10,5%, o CFO identificou janela de refinanciamento.

**Cenário de negociação:** O BTG Pactual sinalizou interesse em estruturar debenture simples como alternativa. O Itaú BBA propôs roll-over com redução de spread de 30bps. O Bradesco BBI apresentou proposta combinada de novação + amortização parcial. A posição de cada banco no sindicato criava assimetrias de informação típicas de jogos não-cooperativos.

**Risco de não negociar:** manutenção de custo de 14,9% a.a. por mais 12 meses, pressionando o DSCR abaixo do covenant de 1,2x no vencimento.

**Decisão tomada:** Renegociação em duas tranches: (1) R$ 31,2M via nova CCB com Itaú+Bradesco a CDI+1,1%, 36 meses; (2) R$ 20,8M via debenture não conversível com BTG, IPCA+5,8%, 48 meses, com cláusula de amortização acelerada (EBITDA/Receita > 15%).

**Resultado real:** Custo médio reduziu de 14,9% para 12,4% a.a., economia anual de R$ 1,3M. DSCR subiu de 1,18x para 1,41x. BTG exerceu cláusula de amortização acelerada no Ano 2.

### Premissas Identificadas no Racional Original
1. A Selic encerra o ciclo em 10,0%-10,5%
2. Os bancos têm incentivo para renegociar (risco de concentração de carteira)
3. Rating da empresa se mantém em 'AA-' durante o processo

### Riscos Mencionados no Racional Original
1. BTG pode usar posição de credor junior para exigir covenants mais restritivos
2. Reversão do afrouxamento monetário pode encarecer spread antes do fechamento
3. Downgrade de rating pode encarecer a debenture em 60-80bps
4. Desalinhamento entre bancos pode paralisar a negociação
5. Cláusula cross-default pode ser acionada em qualquer reestruturação paralela

---

## Caso 3 — Gestão de Liquidez: Gap de Caixa R$ 3,8M — Janela 90 dias

### Ficha Técnica
```
financial_domain  : treasury
decision_type     : liquidity_management
financial_exposure: R$ 3.800.000
time_horizon      : short
external_agents   : false
impact_score      : 4
framework         : risk_matrix
scenario_required : true
```

### Seção A — Racional Original

Flash report do Tesoureiro, outubro. O PMR (prazo médio de recebimento) subiu de 42 para 60 dias nas três maiores redes varejistas (Carrefour, GPA, Atacadão), gerando R$ 3,1M de déficit de recebíveis vs. planejado. Somado ao vencimento de CCR de R$ 700k não orçada, o gap projetado na janela de 90 dias foi de R$ 3,8M.

**Alternativas avaliadas:** (a) saque da linha de crédito rotativo (R$ 5M disponíveis, CDI+2,2%); (b) desconto de duplicatas/FIDC a 1,1% a.m.; (c) redução acelerada de estoque de matérias-primas via vendas à vista com desconto; (d) prazo adicional junto a fornecedores-chave.

**Decisão tomada:** Abordagem híbrida — saque de R$ 2,5M do crédito rotativo + desconto de R$ 1,0M em duplicatas via FIDC + R$ 300k via prazo adicional com 2 fornecedores de embalagem. Custo total estimado: R$ 68k no período.

**Resultado real:** Gap coberto em 78 dias (vs. 90 projetados). Custo efetivo R$ 52k. Sem violação de covenants. PMR normalizou para 46 dias em Q1 após renegociação de SLAs com as redes.

### Premissas Identificadas no Racional Original
1. As redes varejistas honrarão os pagamentos dentro de 60 dias
2. A linha rotativa permanece disponível sem renegociação de covenant
3. O FIDC manterá taxa de 1,0%-1,1% a.m. sem deterioração do portfólio
4. Fornecedores aceitarão prazo adicional sem cobrança de juros

### Riscos Mencionados no Racional Original
1. Deterioração adicional do PMR pode ampliar o gap além do limite rotativo
2. Alta do CDI pode encarecer o crédito rotativo acima do projetado
3. Recusa dos fornecedores de embalagem
4. Sinalização de fragilidade de liquidez ao mercado

---

## Caso 4 — Aprovação de CAPEX: Nova Linha de Produção Recife R$ 18M

### Ficha Técnica
```
financial_domain  : funding
decision_type     : investment_evaluation
financial_exposure: R$ 18.000.000
time_horizon      : long
external_agents   : true  ← BNDES-Finem, fundo de PE coinvestidor
impact_score      : 5
framework         : game_theory  ← ativado por investment_evaluation + external_agents
scenario_required : true
```

### Seção A — Racional Original

Apresentação do Board, novembro. O mercado nordestino de proteína animal processada cresceu 14% no triênio anterior com penetração de apenas 3,2% da empresa. O governo de Pernambuco concedeu incentivo ICMS de 40% para agroindústrias com validade de 15 anos.

**Estrutura de capital proposta:** BNDES-Finem financia 60% (R$ 10,8M) a TJLP+2%. Um fundo de PE regional sinalizou coinvestimento de 20% (R$ 3,6M) via equity em SPE, diluindo 8% do capital. Recursos próprios: 20% (R$ 3,6M).

**Análise financeira:** TIR com incentivo = 21,4%. VPL a 15,3% de WACC = R$ 6,2M positivo. Payback sem incentivo = 7 anos; com incentivo = 4,5 anos. Meta de ROIC Ano 3 = 18%.

**Complexidade de negociação:** O PE coinvestidor tentou impor cláusula de drag-along e meta de saída em 4 anos. O BNDES exigiu DSCR mínimo de 1,3x na SPE. A negociação simultânea com três agentes com incentivos distintos demandou abordagem game-theoretic.

**Decisão tomada:** Investimento aprovado com as condições originalmente propostas. Cláusula de drag-along do PE substituída por tag-along com trigger de ROIC de 15%. Prazo de conclusão: 18 meses.

**Resultado real:** Linha operacional em 10 meses. ROIC de 18,2% no Ano 2. PE exerceu tag-along no Ano 3 com múltiplo 2,1x. BNDES sem renegociação.

### Premissas Identificadas no Racional Original
1. Crescimento do mercado nordestino mantido entre 10%-15% a.a.
2. Incentivo ICMS permanece vigente por todo o período projetado
3. BNDES mantém condições de TJLP+2% sem aditivo de spread
4. PE não exercerá opção de put antes do Ano 3
5. Mão de obra disponível na região a custo 15% inferior ao de SP

### Riscos Mencionados no Racional Original
1. Revisão ou extinção do incentivo ICMS por mudança política
2. Atraso na obra civil ou fornecimento de equipamentos
3. PE exercendo drag-along desfavorável
4. Concorrente anunciando expansão na região antes da planta atingir capacidade plena
5. Alta de TJLP encarecendo serviço da dívida BNDES (impacto de até R$ 1,4M no VPL)

---

## Caso 5 — Revisão de Forecast Q3: Impacto Cambial e Inflação de Insumos

### Ficha Técnica
```
financial_domain  : reporting
decision_type     : forecast_revision
financial_exposure: R$ 1.200.000
time_horizon      : short
external_agents   : false
impact_score      : 3
framework         : scenario_analysis
scenario_required : false
```

### Seção A — Racional Original

Relatório do Planejamento Financeiro, julho. O BRL depreciou 15% vs. USD no Q2 (de R$4,90 para R$5,64), impactando embalagens importadas (23% do COGS). O modelo de sensibilidade calculou erosão de R$ 1,2M na margem EBITDA do Q3, reduzindo-a de 14,2% para 12,8%.

**Três cenários analisados:** base (câmbio estabiliza em R$5,64, impacto R$ 1,2M), otimista (apreciação para R$5,30, impacto R$ 600k), pessimista (depreciação para R$6,00, impacto R$ 1,9M). A tese de hedge via NDF foi levantada como mitigante para Q4.

**Decisão tomada:** Revisão do forecast de Q3 para margem de 12,8% (cenário base). Contratação de NDF BRL/USD cobrindo 50% da exposição de embalagens para Q4, a R$5,70. Reajuste de preços de +1,8% a partir de outubro.

**Resultado real:** EBITDA Q3 em R$ 62,9M (margem 13,1%), acima da revisão graças ao hedge (ganho de R$ 920k). NDF Q4 gerou proteção adicional de R$ 1,1M. Reajuste +1,8% absorvido com perda de volume < 2%.

### Premissas Identificadas no Racional Original
1. Câmbio estabiliza entre R$5,50-R$5,75 no Q3
2. NDF contratado a custo de carregamento < 0,5% a.m.
3. Reajuste de +1,8% não gera perda de volume superior a 2%
4. Custo de embalagens não sofre alta adicional além dos 18% já calculados

### Riscos Mencionados no Racional Original
1. Nova depreciação acima de R$6,00 pode ampliar a erosão para R$ 1,9M
2. Contração de crédito pode inviabilizar NDF nas condições modeladas
3. Repasse acima de 1,8% pode ser necessário, gerando risco de volume maior
4. Deterioração de margem simultânea em outros produtos pode comprometer guidance anual

---

## Template do Comparison Report (Pós-Simulação)

Para cada caso, após executar o fluxo completo na API, preencher o seguinte template:

```
=== COMPARISON REPORT — Caso N ===

Seção A — Racional Original
  Premissas identificadas (original) : N
  Riscos mencionados (original)      : N

Seção B — Racional Estruturado pelo Mentor CFO
  Framework aplicado                 : <framework>
  Premissas explicitadas pelo Mentor : N (incluindo implícitas capturadas)
  Riscos identificados pelo Mentor   : N
  Cenários gerados                   : N (se scenario_required=true)
  Recomendação do Mentor             : <texto>

Seção C — Delta de Qualidade
  premissas_adicionais               : N (Mentor - Original)
  riscos_adicionais                  : N (Mentor - Original)
  cenarios_gerados                   : N
  divergencia_registrada             : true/false
  score_clareza_executivo            : 1-5

Seção D — Resultado Real (preencher 90d após decisão)
  outcome_summary                    : <texto>
  forecast_accuracy_score            : 1-10
  risk_realization_rate              : %
  capital_allocation_efficiency_score: %
```

---

## Guia de Execução via API

### Pré-requisitos
```bash
export CFO_API_TOKEN="<seu_token_jwt>"
export BASE_URL="http://localhost:8000"
```

### Fluxo por Caso
```bash
# 1. Criar caso (extraia campos API do _case JSON)
CASE_ID=$(curl -s -X POST "${BASE_URL}/v1/financial-decision-cases" \
  -H "Authorization: Bearer ${CFO_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{ <campos do api_payload> }' | jq -r '.id')

# 2. Classificar
curl -X PUT "${BASE_URL}/v1/financial-decision-cases/${CASE_ID}/classify" \
  -H "Authorization: Bearer ${CFO_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"impact_score": <score>}'

# 3. Estruturar (mínimo 3 premissas + 3 riscos)
curl -X PUT "${BASE_URL}/v1/financial-decision-cases/${CASE_ID}/structure" \
  -H "Authorization: Bearer ${CFO_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"assumptions": [...], "risks": [...]}'

# 4. Analisar (chama LLM)
curl -X PUT "${BASE_URL}/v1/financial-decision-cases/${CASE_ID}/analyze" \
  -H "Authorization: Bearer ${CFO_API_TOKEN}"

# 5. Decidir
curl -X PUT "${BASE_URL}/v1/financial-decision-cases/${CASE_ID}/decide" \
  -H "Authorization: Bearer ${CFO_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"executive_decision": "..."}'

# 6. Revisar
curl -X PUT "${BASE_URL}/v1/financial-decision-cases/${CASE_ID}/review" \
  -H "Authorization: Bearer ${CFO_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"outcome_summary": "...", "forecast_accuracy_score": N, ...}'

# 7. Consultar trilha de auditoria
curl "${BASE_URL}/v1/financial-decision-cases/${CASE_ID}/state-transitions" \
  -H "Authorization: Bearer ${CFO_API_TOKEN}" | jq .
```

### Smoke Test Completo
```bash
./scripts/smoke_test.sh http://localhost:8000 ${CFO_API_TOKEN}
```
