import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getCase } from '../lib/api'
import { Layout } from '../components/layout/Layout'
import { StateStepper } from '../components/cases/StateStepper'
import { ActionPanel } from '../components/cases/ActionPanel'
import { AuditTrail } from '../components/cases/AuditTrail'
import { StateBadge } from '../components/ui/Badge'
import { PageSpinner } from '../components/ui/Spinner'
import { ArrowLeft, AlertTriangle, CheckCircle } from 'lucide-react'
import { useState } from 'react'

const DOMAIN_LABELS = { planning: 'Planejamento', reporting: 'Relatórios', treasury: 'Tesouraria', funding: 'Captação', risk: 'Risco' }
const TYPE_LABELS = {
  budget_adjustment: 'Ajuste de Orçamento', forecast_revision: 'Revisão de Forecast',
  capital_allocation: 'Alocação de Capital', debt_structuring: 'Estruturação de Dívida',
  liquidity_management: 'Gestão de Liquidez', risk_hedging: 'Hedge de Risco',
  cost_reduction: 'Redução de Custos', investment_evaluation: 'Avaliação de Investimento',
}
const FRAMEWORK_LABELS = {
  pdca: 'PDCA', scenario_analysis: 'Análise de Cenários', game_theory: 'Teoria dos Jogos',
  trade_off: 'Trade-Off', risk_matrix: 'Matriz de Riscos', capital_allocation: 'Alocação de Capital',
}

function fmtBRL(v) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(v)
}

function InfoItem({ label, value }) {
  return (
    <div>
      <p className="text-xs text-gray-400 uppercase tracking-wide font-medium">{label}</p>
      <p className="text-sm text-gray-900 mt-0.5 font-medium">{value || '—'}</p>
    </div>
  )
}

const TABS = ['Ação', 'Premissas & Riscos', 'Histórico']

export default function CaseDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [tab, setTab] = useState(0)

  const { data: caseData, isLoading } = useQuery({
    queryKey: ['case', id],
    queryFn: () => getCase(id),
    refetchInterval: (data) => {
      // Auto-refresh quando está em análise (LLM pode demorar)
      return data?.state === 'STRUCTURED' ? 3000 : false
    },
  })

  if (isLoading) return <Layout><PageSpinner /></Layout>
  if (!caseData) return <Layout><div className="p-8 text-gray-500">Caso não encontrado.</div></Layout>

  return (
    <Layout>
      <div className="p-8 max-w-5xl mx-auto">
        {/* Back */}
        <button onClick={() => navigate('/')} className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-900 mb-6 transition-colors">
          <ArrowLeft className="h-4 w-4" />
          Voltar ao Dashboard
        </button>

        {/* Header Card */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-2 flex-wrap">
                <StateBadge state={caseData.state} />
                {caseData.divergence_flag && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-700 border border-orange-200">
                    <AlertTriangle className="h-3 w-3" />
                    Divergência registrada
                  </span>
                )}
                {caseData.state === 'CLOSED' && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700">
                    <CheckCircle className="h-3 w-3" />
                    Ciclo completo
                  </span>
                )}
              </div>
              <h1 className="text-xl font-bold text-gray-900 mb-1">{caseData.title}</h1>
              <p className="text-sm text-gray-500 line-clamp-2">{caseData.description}</p>
            </div>
            <div className="text-right flex-shrink-0">
              <p className="text-2xl font-bold text-brand-900">{fmtBRL(caseData.financial_exposure)}</p>
              <p className="text-xs text-gray-400">exposição financeira</p>
            </div>
          </div>

          {/* Meta */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 mt-6 pt-5 border-t border-gray-100">
            <InfoItem label="Domínio" value={DOMAIN_LABELS[caseData.financial_domain] || caseData.financial_domain} />
            <InfoItem label="Tipo de Decisão" value={TYPE_LABELS[caseData.decision_type] || caseData.decision_type} />
            <InfoItem label="Framework" value={FRAMEWORK_LABELS[caseData.framework_selected] || (caseData.framework_selected || 'Ainda não definido')} />
            <InfoItem label="Score de Impacto" value={caseData.impact_score ? `${caseData.impact_score}/5` : 'Ainda não definido'} />
          </div>

          {/* Extras */}
          {(caseData.scenario_required || caseData.external_agents_present) && (
            <div className="flex gap-2 mt-4 flex-wrap">
              {caseData.scenario_required && (
                <span className="bg-amber-100 text-amber-700 border border-amber-200 px-2.5 py-0.5 rounded-full text-xs font-medium">
                  Cenário obrigatório (exposure &gt; R$2M)
                </span>
              )}
              {caseData.external_agents_present && (
                <span className="bg-purple-100 text-purple-700 border border-purple-200 px-2.5 py-0.5 rounded-full text-xs font-medium">
                  Agentes externos envolvidos
                </span>
              )}
            </div>
          )}
        </div>

        {/* Stepper */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6 overflow-x-auto">
          <StateStepper currentState={caseData.state} />
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <div className="flex gap-0">
            {TABS.map((t, i) => (
              <button
                key={t}
                onClick={() => setTab(i)}
                className={`px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
                  tab === i
                    ? 'border-brand-900 text-brand-900'
                    : 'border-transparent text-gray-500 hover:text-gray-900'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        {tab === 0 && <ActionPanel caseData={caseData} />}

        {tab === 1 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <h3 className="font-semibold text-gray-900 mb-4">
                Premissas ({caseData.assumptions?.length || 0})
              </h3>
              {!caseData.assumptions?.length ? (
                <p className="text-sm text-gray-400">Nenhuma premissa registrada ainda.</p>
              ) : (
                <ul className="space-y-2">
                  {caseData.assumptions.map((a) => (
                    <li key={a.id} className="flex gap-2.5 text-sm">
                      <span className="text-blue-400 mt-0.5 flex-shrink-0">•</span>
                      <span className="text-gray-700">{a.text}</span>
                      {a.is_implicit && (
                        <span className="ml-auto flex-shrink-0 text-xs bg-amber-100 text-amber-600 px-1.5 py-0.5 rounded">implícita</span>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <h3 className="font-semibold text-gray-900 mb-4">
                Riscos ({caseData.risks?.length || 0})
              </h3>
              {!caseData.risks?.length ? (
                <p className="text-sm text-gray-400">Nenhum risco registrado ainda.</p>
              ) : (
                <ul className="space-y-2">
                  {caseData.risks.map((r) => (
                    <li key={r.id} className="flex gap-2.5 text-sm">
                      <span className={`mt-0.5 flex-shrink-0 ${r.materialized ? 'text-red-400' : 'text-gray-300'}`}>▲</span>
                      <span className={r.materialized ? 'text-red-700 font-medium' : 'text-gray-700'}>{r.text}</span>
                      {r.materialized && (
                        <span className="ml-auto flex-shrink-0 text-xs bg-red-100 text-red-600 px-1.5 py-0.5 rounded">materializado</span>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {caseData.financial_metrics_impacted?.length > 0 && (
              <div className="md:col-span-2 bg-white border border-gray-200 rounded-xl p-6">
                <h3 className="font-semibold text-gray-900 mb-3">Métricas Financeiras Impactadas</h3>
                <div className="flex flex-wrap gap-2">
                  {caseData.financial_metrics_impacted.map((m) => (
                    <span key={m} className="bg-brand-50 text-brand-700 border border-brand-100 px-3 py-1 rounded-full text-sm font-medium">{m}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {tab === 2 && (
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h3 className="font-semibold text-gray-900 mb-4">Histórico de Transições</h3>
            <AuditTrail caseId={id} />
          </div>
        )}
      </div>
    </Layout>
  )
}
