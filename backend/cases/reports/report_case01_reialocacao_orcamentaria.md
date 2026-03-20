# Comparison Report — Caso 01
## Realocação Orçamentária Q2: COGS vs. Marketing

| Campo | Valor |
|---|---|
| Label | Realocação Orçamentária Mid-Year |
| Domínio | planning |
| Tipo de Decisão | budget_adjustment |
| Exposição Financeira | R$ 380k |
| Horizonte Temporal | short |
| Agentes Externos | Não |
| Framework Selecionado | PDCA (Plan-Do-Check-Act) |
| Cenário Obrigatório | Não |
| Teoria dos Jogos | Não ativa |
| Impacto Score | 2/5 |
| Modo de Análise LLM | Claude (Anthropic) |

---

## Seção A — Racional Original (pré-Mentor)

### A.1 Justificativa Original

Email da Diretoria de Operações datado de maio, reportando overrun de R$ 380k no COGS de proteína animal devido à estiagem no Centro-Oeste que elevou o farelo de soja em 22% vs. orçamento original. O CFO convocou reunião de revisão orçamentária mid-year para realocar verba. Alternativas avaliadas: corte de headcount (descartado — risco operacional), postergação de capex menor (aprovado parcialmente), e corte de ativações de trade marketing no varejo regional.

### A.2 Decisão Tomada (histórico)

Realocação de R$ 380k do budget de trade marketing regional para cobertura integral do overrun de COGS. Campanhas de Q3 no Nordeste postergadas para Q1 do ano seguinte. Revisão de preços de tabela em +2,5% aprovada concomitantemente para recuperação parcial de margem.

### A.3 Resultado Real

EBITDA margin encerrou o semestre em 13,4%, versus 13,1% projetado pós-realocação. A postergação das ativações gerou queda de 1,8pp de market share no canal regional em Q3, recuperado em Q1 seguinte conforme planejado.

### A.4 Premissas Identificadas no Racional Original

As premissas abaixo foram declaradas explicitamente pelo CFO antes da estruturação pelo Mentor:

- Selic permanece em 10,75% ao longo do semestre, sem impacto adicional sobre o custo de capital de giro
- O preço do farelo de soja não sofre nova elevação acima de 5% no restante do exercício
- A postergação das ativações de trade marketing não gera perda permanente de shelf space nos clientes regionais
- A revisão de preços de +2,5% é absorvida pelo canal sem perda relevante de volume

### A.5 Riscos Mencionados no Racional Original

Os riscos abaixo foram fornecidos pelo CFO como insumo da estruturação:

- Nova alta de commodities pode ampliar o overrun de COGS além dos R$ 380k previstos, exigindo cortes adicionais
- Concorrentes aproveitam ausência das ativações para ganho de market share no canal regional do Nordeste
- Resistência dos clientes varejistas ao reajuste de preços pode gerar devoluções e ruptura de contratos
- Reversão do remanejamento pode ser necessária se o guidance de EBITDA for revisado pelo board em Q3

---

## Seção B — Racional Estruturado pelo Mentor CFO

### B.1 Framework Analítico Aplicado

**PDCA (Plan-Do-Check-Act)**

O framework foi selecionado automaticamente pela engine determinística com base em:
- Tipo de decisão: `budget_adjustment`
- Agentes externos presentes: `False`
- Exposição financeira: `R$ 380k` (impact score = 2/5)

### B.2 Recomendação Estruturada

Recomendação estruturada — Framework PDCA aplicado à Realocação Orçamentária Q2.

**PLAN (Diagnóstico):** O overrun de COGS de R$ 380k é de natureza estrutural-temporária: a alta de 22% no farelo de soja é causada por estiagem no Centro-Oeste e tem correlação histórica de reversão parcial em 6–9 meses. A postergação das ativações de trade marketing regional é o único vetor de financiamento disponível com baixo risco de dano permanente à posição competitiva, desde que executada antes do início das campanhas de Q3 dos concorrentes. A revisão de preços de +2,5% é essencial para preservar margem sem depender de hedge de commodities.

**DO (Ações):** (1) Remanejamento imediato de R$ 380k de trade marketing regional para COGS — sem corte de headcount nem postergação de capex estratégico. (2) Aprovação simultânea da revisão de preços de tabela em +2,5%, com vigência a partir de 1° de agosto. (3) Comunicação proativa ao canal varejista sobre a postergação das campanhas regionais, com data-commit para Q1 do exercício seguinte.

**CHECK (Métricas de controle):** (a) EBITDA margin mensal vs. 13,1% revisado — desvio >0,5pp aciona revisão de emergência; (b) Market share no canal regional Nordeste quinzenal — queda >3pp vs. junho aciona ativação emergencial de PDV mínimo; (c) Preço médio de farelo de soja semanal — alta adicional >5% reabre a discussão de hedge.

**ACT (Ajustes contingentes):** Se o market share regional cair >5pp até outubro, redirecionar R$ 80k do budget de mídia nacional para ativações de PDV emergenciais no canal afetado. Se o farelo recuperar >10% do preço, liberar R$ 120k das ativações postergadas ainda em Q3.

### B.3 Métricas Financeiras Impactadas

- EBITDA margin (%)
- OpEx de Marketing (R$)
- COGS / Receita Líquida (%)
- Market Share Canal Regional (%)
- Variância Orçamentária COGS (R$)

#### Premissas Implícitas Capturadas pelo Mentor

1. A elasticidade-preço da demanda no canal regional é suficientemente baixa para absorver reajuste de 2,5% sem ruptura de contratos com redes varejistas do Nordeste.
2. Os concorrentes diretos não realizarão ativações compensatórias no canal regional durante Q3, dado que a ausência das campanhas próprias não é pública.
3. O canal varejista regional não possui alternativas de fornecimento equivalente que tornem a perda de shelf space permanente em razão da postergação.

### B.4 Decisão Executiva Registrada

> Aprovamos a realocação integral de R$ 380k de trade marketing para COGS, com revisão de preços de tabela em 2,5% e postergação das campanhas regionais para Q1 do exercício seguinte. Monitoramento mensal via DRE gerencial.

**Divergência da recomendação do Mentor:** Não — decisão alinhada com a recomendação

---

## Seção C — Delta de Qualidade

| Dimensão | Valor | Observação |
|---|---|---|
| Premissas adicionais identificadas pelo Mentor | **3** | Premissas implícitas não declaradas pelo CFO |
| Riscos adicionais estruturados | **0** | Riscos já fornecidos pelo CFO como insumo |
| Cenários gerados (pessimista/base/otimista) | **0** | Não obrigatório para este caso (impact_score < 4) |
| Divergência registrada | **Não** | CFO acatou a recomendação do Mentor |
| Score de clareza executivo (1–5) | ⬜ _Preencher após leitura (escala 1–5)_ | Avaliação subjetiva do Arquiteto após leitura |

### C.1 Avaliação Qualitativa

- **Cobertura de premissas:** 4 premissas declaradas + 3 implícitas capturadas = 7 total
- **Rigor de riscos:** 4 riscos identificados e estruturados pelo CFO
- **Profundidade analítica:** Moderada — framework sem análise de cenários obrigatória
- **Alinhamento decisório:** ALINHADO — CFO acatou a recomendação integral do Mentor

---

_Relatório gerado automaticamente por `scripts/generate_reports.py` — generate_reports.py_
_Caso ID: 41d86740-3ee4-4603-83ce-1f3aa0b7e4e1_