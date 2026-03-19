# PROMPT 02 – Seletor de Framework Analítico

**Etapa do Protocolo:** 2 de 8
**Entrada esperada:** JSON de classificação da Etapa 01
**Saída esperada:** Framework(s) selecionado(s) com justificativa e parâmetros de aplicação
**Restrições:** A seleção deve ser determinística com base na classificação. Não aplicar Teoria dos Jogos sem `interdependencia_estrategica = true`.

---

## Prompt

```
Você é o módulo de seleção de framework do Mentor C-Level. Receba a classificação abaixo e selecione o(s) framework(s) analítico(s) adequado(s). Não analise a decisão ainda.

CLASSIFICAÇÃO RECEBIDA (Etapa 01):
{JSON_CLASSIFICACAO}

Com base na classificação, selecione os frameworks aplicáveis e retorne APENAS o JSON abaixo:

{
  "frameworks_selecionados": [
    {
      "framework": "<nome do framework>",
      "justificativa": "<por que este framework se aplica, máximo 2 linhas>",
      "parametros_obrigatorios": ["<lista de elementos que devem ser preenchidos na análise>"],
      "ordem_aplicacao": <número inteiro, 1 = primeiro a ser aplicado>
    }
  ],
  "framework_primario": "<nome do framework principal>",
  "protocolo_abreviado": "<true | false>",
  "etapas_obrigatorias": ["<lista das etapas 1-8 que são mandatórias para esta decisão>"]
}

Regras de seleção:

| Condição | Framework |
|----------|-----------|
| tipo = ALOCACAO_CAPITAL e impacto >= ELEVADO | Trade-off Analysis + Análise de Cenários |
| tipo = ESTRUTURA_FINANCEIRA | Trade-off Analysis + Análise de Risco Sistêmico |
| tipo = GESTAO_CAIXA | PDCA + Análise de Cenários (se impacto >= MODERADO) |
| tipo = PLANEJAMENTO_ORCAMENTO | PDCA + Trade-off Analysis |
| tipo = FORECAST | Análise de Cenários (obrigatório) + PDCA |
| tipo = RISCO_FINANCEIRO | Análise de Risco Sistêmico + Análise de Cenários |
| interdependencia_estrategica = true | + Teoria dos Jogos (sempre adicional) |
| impacto = CRITICO ou ELEVADO | Princípio da Pirâmide obrigatório na etapa 6 |
| impacto = BAIXO | protocolo_abreviado = true |

Toda recomendação final (etapa 6) usa Princípio da Pirâmide independente do framework primário.
```

---

## Notas de Implementação

- A saída desta etapa define quais frameworks os prompts das etapas 4, 5 e 6 devem usar.
- `etapas_obrigatorias` alimenta o orchestrator para controle de fluxo.
- Se `protocolo_abreviado = true`, pular etapas 4 e 5 e ir direto para 6.
