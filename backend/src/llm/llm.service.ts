import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import OpenAI from 'openai';

@Injectable()
export class LlmService {
  private openai: OpenAI | null = null;

  constructor(private readonly configService: ConfigService) {
    const apiKey = this.configService.get<string>('OPENAI_API_KEY');
    if (apiKey && !apiKey.startsWith('sk-your')) {
      this.openai = new OpenAI({ apiKey });
    }
  }

  async generateRecommendation(caseData: any): Promise<{ recommendation: string; recommendedOption: string }> {
    if (!this.openai) {
      return this.mockRecommendation(caseData);
    }

    try {
      const prompt = this.buildRecommendationPrompt(caseData);
      const response = await this.openai.chat.completions.create({
        model: 'gpt-4o',
        messages: [
          {
            role: 'system',
            content:
              'You are a world-class CFO advisor. Structure your recommendations using the Pyramid Principle: Situation, Complication, Resolution. Be precise, financially rigorous, and executive-ready.',
          },
          { role: 'user', content: prompt },
        ],
        response_format: { type: 'json_object' },
        temperature: 0.3,
      });

      const content = response.choices[0]?.message?.content || '{}';
      const parsed = JSON.parse(content);
      return {
        recommendation: parsed.recommendation || this.mockRecommendation(caseData).recommendation,
        recommendedOption: parsed.recommendedOption || 'PROCEED',
      };
    } catch (err) {
      console.error('LLM recommendation error, falling back to mock:', err.message);
      return this.mockRecommendation(caseData);
    }
  }

  async generateGameTheoryAnalysis(caseData: any): Promise<any> {
    if (!this.openai) {
      return this.mockGameTheoryAnalysis(caseData);
    }

    try {
      const prompt = this.buildGameTheoryPrompt(caseData);
      const response = await this.openai.chat.completions.create({
        model: 'gpt-4o',
        messages: [
          {
            role: 'system',
            content:
              'You are an expert in game theory and strategic decision analysis. Return structured JSON with players, strategySpace, payoffMatrix, equilibrium, and strategicRiskExposure.',
          },
          { role: 'user', content: prompt },
        ],
        response_format: { type: 'json_object' },
        temperature: 0.2,
      });

      const content = response.choices[0]?.message?.content || '{}';
      return JSON.parse(content);
    } catch (err) {
      console.error('LLM game theory error, falling back to mock:', err.message);
      return this.mockGameTheoryAnalysis(caseData);
    }
  }

  private buildRecommendationPrompt(caseData: any): string {
    return `
Analyze the following financial decision case and provide a structured CFO-level recommendation.

Case Title: ${caseData.title}
Description: ${caseData.description}
Domain: ${caseData.financialDomain}
Decision Type: ${caseData.decisionType}
Impact Score: ${caseData.impactScore}/5
External Agents Present: ${caseData.externalAgentsPresent}

Assumptions:
${(caseData.assumptions || []).map((a: any, i: number) => `${i + 1}. ${a.description} (confidence: ${(a.confidence * 100).toFixed(0)}%, source: ${a.source})`).join('\n')}

Risks:
${(caseData.risks || []).map((r: any, i: number) => `${i + 1}. ${r.description} (probability: ${(r.probability * 100).toFixed(0)}%, impact: ${r.impactScore}/5, mitigation: ${r.mitigationPlan || 'none'})`).join('\n')}

Metrics Impacted:
${(caseData.metricsImpacted || []).map((m: any) => `- ${m.metricName}: ${m.currentValue} → ${m.projectedValue} ${m.unit} over ${m.timeHorizonMonths} months`).join('\n')}

Return JSON with:
{
  "recommendation": "<full Pyramid Principle recommendation: Situation, Complication, Resolution>",
  "recommendedOption": "<short identifier like PROCEED / DEFER / REJECT / PROCEED_PHASED>"
}
`;
  }

  private buildGameTheoryPrompt(caseData: any): string {
    return `
Perform a game theory analysis for the following financial decision case.

Case Title: ${caseData.title}
Domain: ${caseData.financialDomain}
Decision Type: ${caseData.decisionType}
External Agents Present: ${caseData.externalAgentsPresent}
Description: ${caseData.description}

Identify all strategic players (internal and external), their strategy spaces, a simplified payoff matrix, the Nash equilibrium, and strategic risk exposure.

Return JSON with:
{
  "players": ["player1", "player2", ...],
  "strategySpace": { "player1": ["strategy1", "strategy2"], ... },
  "payoffMatrix": {
    "description": "...",
    "dominantStrategyCombination": { "player1": "strategyX", ... },
    "payoffs": { "player1": <score 0-10>, ... }
  },
  "equilibrium": "<description of Nash equilibrium>",
  "strategicRiskExposure": "<description of strategic risk>"
}
`;
  }

  private mockRecommendation(caseData: any): { recommendation: string; recommendedOption: string } {
    return {
      recommendation: `**RECOMMENDATION: PROCEED WITH STRUCTURED REVIEW**

**Situation:** The organisation is evaluating a ${caseData.decisionType} decision in the ${caseData.financialDomain} domain with an impact score of ${caseData.impactScore}/5. ${caseData.description}

**Complication:** The decision carries material financial implications across ${(caseData.metricsImpacted || []).length} key metrics. ${(caseData.risks || []).length} risks have been identified, with mitigation plans required for the highest-probability items. Key assumptions require validation before commitment.

**Resolution:** Based on the structured analysis:
1. Validate all ${(caseData.assumptions || []).length} assumptions before proceeding to final decision
2. Implement risk mitigation plans for all risks with probability > 0.4
3. Establish quarterly review gates to monitor metric performance
4. Ensure board-level alignment given impact score of ${caseData.impactScore}/5
5. Document executive decision rationale for governance and audit purposes

This recommendation is generated with structured analysis and should be reviewed by the CFO and relevant stakeholders before final commitment.`,
      recommendedOption: 'PROCEED',
    };
  }

  private mockGameTheoryAnalysis(caseData: any): any {
    return {
      players: [
        'CFO / Finance',
        'Operational Leadership',
        'External Counterparty',
        'Board / Shareholders',
      ],
      strategySpace: {
        'CFO / Finance': ['Approve', 'Defer', 'Reject with Counter-proposal'],
        'Operational Leadership': ['Full Support', 'Conditional Support', 'Opposition'],
        'External Counterparty': ['Aggressive Negotiation', 'Cooperative', 'Withdraw'],
        'Board / Shareholders': ['Endorse', 'Request Further Analysis', 'Veto'],
      },
      payoffMatrix: {
        description: `Payoff analysis for ${caseData.title} under dominant strategy combination`,
        dominantStrategyCombination: {
          'CFO / Finance': 'Approve',
          'Operational Leadership': 'Conditional Support',
          'External Counterparty': 'Cooperative',
          'Board / Shareholders': 'Endorse',
        },
        payoffs: {
          'CFO / Finance': 7,
          'Operational Leadership': 6,
          'External Counterparty': 7,
          'Board / Shareholders': 8,
        },
      },
      equilibrium:
        'Nash Equilibrium at (Approve, Conditional Support, Cooperative, Endorse). No player has unilateral incentive to deviate given current information and payoff structure.',
      strategicRiskExposure:
        `Moderate strategic risk exposure. Primary risk is External Counterparty shifting to Aggressive Negotiation if internal alignment signals weakness. Recommend projecting unified internal position before external engagement. Impact score of ${caseData.impactScore}/5 warrants pre-commitment alignment with Board.`,
    };
  }
}
