# Comparison Report — Caso 05
## Revisão de Forecast Q3: Impacto Cambial e Inflação de Insumos

| Campo | Valor |
|---|---|
| Label | Revisão de Forecast Q3 sob Pressão Cambial |
| Domínio | reporting |
| Tipo de Decisão | forecast_revision |
| Exposição Financeira | R$ 1.2M |
| Horizonte Temporal | short |
| Agentes Externos | Não |
| Framework Selecionado | Análise de Cenários |
| Cenário Obrigatório | Não |
| Teoria dos Jogos | Não ativa |
| Impacto Score | 3/5 |
| Modo de Análise LLM | Claude (Anthropic) |

---

## Seção A — Racional Original (pré-Mentor)

### A.1 Justificativa Original

Relatório do Planejamento Financeiro de julho: O BRL depreciou 15% vs. USD no Q2 (de R$4,90 para R$5,64), impactando diretamente embalagens importadas (participação de 23% no COGS). Modelo de sensibilidade indicou erosão de R$ 1,2M na margem EBITDA do Q3, reduzindo a margem de 14,2% para 12,8%. O CFO solicitou revisão formal do forecast com três cenários: base (câmbio estabiliza em R$5,64), otimista (apreciação para R$5,30) e pessimista (depreciação para R$6,00). A tese de hedging parcial foi levantada como mitigante.

### A.2 Decisão Tomada (histórico)

Revisão do forecast de EBITDA do Q3 de R$ 68,2M (margem 14,2%) para R$ 61,4M (margem 12,8%), refletindo o cenário base. Implementação de hedge cambial de 50% da exposição de embalagens importadas via NDF BRL/USD para Q4, a R$5,70. Revisão de preços de tabela em +1,8% aprovada para Q4 como mitigante adicional.

### A.3 Resultado Real

EBITDA do Q3 encerrou em R$ 62,9M (margem 13,1%), acima da revisão de 12,8% graças ao hedge parcial que gerou ganho de R$ 920k. NDF de Q4 resultou em proteção adicional de R$ 1,1M. Revisão de preços de +1,8% absorvida pelo canal com impacto de volume abaixo de 2%.

### A.4 Premissas Identificadas no Racional Original

As premissas abaixo foram declaradas explicitamente pelo CFO antes da estruturação pelo Mentor:

- A taxa de câmbio BRL/USD se estabiliza no intervalo de R$5,50-R$5,75 no Q3, sem novo choque desordenado de depreciação
- O hedge via NDF a R$5,70 pode ser contratado a custo de carregamento inferior a 0,5% a.m. com as contrapartes bancárias disponíveis
- A revisão de preços de tabela em +1,8% não gera perda de volume superior a 2% nos canais atacado e varejo durante o trimestre
- O custo de embalagens importadas não sofre alta adicional além do impacto já calculado de 18% no período de referência

### A.5 Riscos Mencionados no Racional Original

Os riscos abaixo foram fornecidos pelo CFO como insumo da estruturação:

- Nova depreciação cambial acima de R$6,00 pode ampliar a erosão de margem para além dos R$ 1,2M projetados, alcançando R$ 1,9M no pior cenário
- Contração de crédito bancário pode inviabilizar a contratação do NDF nas condições de custo assumidas no modelo de sensibilidade
- Repasse de preços acima de 1,8% pode ser necessário se a inflação de insumos acelerar, gerando risco de volume maior do que o modelado
- Deterioração de margem simultânea em outros produtos pode inviabilizar o guidance anual, exigindo revisão do outlook ao mercado

---

## Seção B — Racional Estruturado pelo Mentor CFO

### B.1 Framework Analítico Aplicado

**Análise de Cenários**

O framework foi selecionado automaticamente pela engine determinística com base em:
- Tipo de decisão: `forecast_revision`
- Agentes externos presentes: `False`
- Exposição financeira: `R$ 1.2M` (impact score = 3/5)

### B.2 Recomendação Estruturada

Recomendação estruturada — Framework de Análise de Cenários aplicado à Revisão de Forecast Q3 (Impacto Cambial R$ 1,2M).

A revisão do forecast de EBITDA é matematicamente obrigatória dado o choque cambial comprovado: BRL/USD de R$4,90 para R$5,64 (+15,1%) com 23% do COGS exposto a embalagens importadas gera erosão de margem de 1,4pp — de 14,2% para 12,8% — equivalente a R$ 1,2M em EBITDA Q3.

**Estrutura de Ação Recomendada:**

(1) *Revisão formal do forecast Q3*: Comunicar internamente a revisão de margem EBITDA de 14,2% → 12,8% para Q3. Não comunicar ao mercado até encerramento do trimestre, a menos que a margem acumulada no semestre ameace violar o guidance anual de 13,5%.

(2) *Hedge cambial via NDF BRL/USD para Q4*: Contratar NDF cobrindo 50% da exposição de embalagens importadas de Q4 (estimada em R$ 2,4M de custo de embalagens importadas) a taxa de R$5,70, com vencimento em dezembro. Custo de carregamento estimado em 0,3% a.m. para contrapartes com rating A+ = custo total de ~R$ 7k para proteção de ~R$ 1,2M de exposição.

(3) *Reajuste de preços de tabela de +1,8%*: Implementar em outubro para todos os canais. A elasticidade histórica sugere perda de volume de 1,5–2% — aceitável dado que o ganho de receita líquida (+1,8% × 98% de volume retido) supera a perda de R$ 420k estimada por ponto de margem sacrificado.

(4) *Não implementar hedge total (100%)*: O custo de carregamento do NDF a 100% de cobertura elevaria o custo de proteção para R$ 38k por trimestre, com ganho marginal limitado dado que o cenário base já prevê estabilização do câmbio.

### B.3 Métricas Financeiras Impactadas

- Margem EBITDA (%) — Q3 e acumulado anual
- Receita Líquida (R$) — impacto do reajuste de preços
- COGS / Receita Líquida (%) — sensibilidade cambial
- Resultado Financeiro — ganho/perda do NDF (R$)
- FCO — Fluxo de Caixa Operacional (R$)
- Volume de Vendas — elasticidade do reajuste de preços

#### Premissas Implícitas Capturadas pelo Mentor

1. A exposição cambial de embalagens importadas de Q4 é estruturalmente similar à de Q3 (R$ 2,4M de custo de embalagens importadas por trimestre) — qualquer mudança no mix de produtos ou substituição parcial de fornecedores altera o volume de exposição e, portanto, o dimensionamento do NDF.
2. A contratação do NDF não viola nenhum covenant financeiro que proíba instrumentos derivativos sem aprovação prévia do conselho — alguns contratos de crédito têm cláusulas restritivas a derivativos especulativos.
3. A revisão de preços de +1,8% pode ser implementada unilateralmente sem renegociação contratual formal com os principais clientes varejistas — caso haja contratos de preço fixo em vigor, o reajuste pode ser bloqueado até o vencimento do contrato.

#### Análise de Cenários (scenario_required = true)

**Cenário Pessimista** (BRL/USD atinge R$6,00; inflação de embalagens sobe +26% vs. orçamento): Erosão de EBITDA amplia para R$ 1,9M. Margem Q3 cai para 12,1%. NDF de 50% protege R$ 920k dos R$ 1,9M de impacto. Margem líquida pós-hedge: ~12,5%. Se acumulado do ano cair abaixo de 13,0%, acionar revisão de guidance ao mercado. Ação adicional: hedgear mais 20% da exposição Q4 (total 70%) e implementar reajuste emergencial de +0,8% adicional em novembro.

**Cenário Base** (BRL/USD estabiliza em R$5,64; COGS de embalagens +18%): Erosão de R$ 1,2M. Margem Q3 de 12,8%. NDF 50% gera ganho de R$ 920k em Q4. Reajuste de +1,8% absorvido com perda de volume <2%. Margem acumulada anual: ~13,3% — acima do guidance de 13,0%. Este é o cenário de referência da revisão.

**Cenário Otimista** (BRL/USD aprecia para R$5,30 no Q3; embalagens sobem apenas +10%): Erosão reduz para R$ 650k. Margem Q3 sobe para 13,6%. NDF gera perda contábil de R$ 120k (hedge ficou 'out-of-the-money'). Impacto líquido positivo: margem acima do forecast original. Recomendação: não cancelar o NDF (custo de reversão > ganho incremental), manter reajuste de preços (+1,8% gera receita adicional líquida de ~R$ 800k no Q4).

### B.4 Decisão Executiva Registrada

> Aprovamos a revisão do forecast de Q3 para margem EBITDA de 12,8%, com contratação de NDF cobrindo 50% da exposição cambial de embalagens para Q4 e reajuste de preços de +1,8% a partir de outubro. Revisão de guidance anual será comunicada ao mercado se a margem consolidada ficar abaixo de 13% no acumulado.

**Divergência da recomendação do Mentor:** Não — decisão alinhada com a recomendação

---

## Seção C — Delta de Qualidade

| Dimensão | Valor | Observação |
|---|---|---|
| Premissas adicionais identificadas pelo Mentor | **3** | Premissas implícitas não declaradas pelo CFO |
| Riscos adicionais estruturados | **0** | Riscos já fornecidos pelo CFO como insumo |
| Cenários gerados (pessimista/base/otimista) | **1** | Análise de cenários aplicada |
| Divergência registrada | **Não** | CFO acatou a recomendação do Mentor |
| Score de clareza executivo (1–5) | ⬜ _Preencher após leitura (escala 1–5)_ | Avaliação subjetiva do Arquiteto após leitura |

### C.1 Avaliação Qualitativa

- **Cobertura de premissas:** 4 premissas declaradas + 3 implícitas capturadas = 7 total
- **Rigor de riscos:** 4 riscos identificados e estruturados pelo CFO
- **Profundidade analítica:** Moderada — framework sem análise de cenários obrigatória
- **Alinhamento decisório:** ALINHADO — CFO acatou a recomendação integral do Mentor

---

_Relatório gerado automaticamente por `scripts/generate_reports.py` — generate_reports.py_
_Caso ID: 068b9dcc-9a94-451a-bf6e-f058d22bc815_