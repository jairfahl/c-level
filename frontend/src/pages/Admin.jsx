import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getPendingReviews } from '../lib/api'
import { Layout } from '../components/layout/Layout'
import { PageSpinner } from '../components/ui/Spinner'
import { Badge } from '../components/ui/Badge'
import { ShieldAlert, CheckCircle, ArrowRight } from 'lucide-react'

const DOMAIN_LABELS = { planning: 'Planejamento', reporting: 'Relatórios', treasury: 'Tesouraria', funding: 'Captação', risk: 'Risco' }
const TYPE_LABELS = {
  budget_adjustment: 'Ajuste de Orçamento', forecast_revision: 'Revisão de Forecast',
  capital_allocation: 'Alocação de Capital', debt_structuring: 'Estruturação de Dívida',
  liquidity_management: 'Gestão de Liquidez', risk_hedging: 'Hedge de Risco',
  cost_reduction: 'Redução de Custos', investment_evaluation: 'Avaliação de Investimento',
}

function fmtBRL(v) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(v)
}

function fmtDate(dt) {
  return new Date(dt).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

export default function Admin() {
  const navigate = useNavigate()
  const { data, isLoading } = useQuery({
    queryKey: ['pending-reviews'],
    queryFn: getPendingReviews,
  })

  return (
    <Layout>
      <div className="p-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Painel Admin</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Casos decididos há mais de {data?.threshold_days || 1} dia aguardando revisão de resultados
          </p>
        </div>

        {isLoading ? (
          <PageSpinner />
        ) : !data?.pending?.length ? (
          <div className="text-center py-20">
            <CheckCircle className="h-12 w-12 text-green-300 mx-auto mb-4" />
            <p className="text-gray-500 font-medium">Tudo em dia!</p>
            <p className="text-gray-400 text-sm mt-1">Nenhum caso pendente de revisão</p>
          </div>
        ) : (
          <>
            {/* Summary */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
              <div className="bg-white border border-gray-200 rounded-xl p-5">
                <p className="text-3xl font-bold text-red-600">{data.total}</p>
                <p className="text-sm text-gray-500 mt-1">Casos pendentes</p>
              </div>
              <div className="bg-white border border-gray-200 rounded-xl p-5">
                <p className="text-3xl font-bold text-gray-900">
                  {Math.max(...data.pending.map((p) => p.days_pending))}
                </p>
                <p className="text-sm text-gray-500 mt-1">Dias sem revisão (máx.)</p>
              </div>
              <div className="bg-white border border-gray-200 rounded-xl p-5">
                <p className="text-3xl font-bold text-brand-900">
                  {fmtBRL(data.pending.reduce((s, p) => s + p.financial_exposure, 0))}
                </p>
                <p className="text-sm text-gray-500 mt-1">Exposição total em revisão</p>
              </div>
            </div>

            {/* Table */}
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="flex items-center gap-2 px-5 py-3.5 border-b border-gray-100 bg-red-50">
                <ShieldAlert className="h-4 w-4 text-red-500" />
                <p className="text-sm font-medium text-red-700">
                  {data.total} caso{data.total !== 1 ? 's' : ''} aguardando revisão obrigatória
                </p>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50">
                    <th className="text-left px-5 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wide">Título</th>
                    <th className="text-left px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wide">Domínio</th>
                    <th className="text-left px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wide">Exposição</th>
                    <th className="text-left px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wide">Decidido em</th>
                    <th className="text-left px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wide">Dias pendentes</th>
                    <th className="px-4 py-3" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {data.pending.map((p) => (
                    <tr key={p.case_id} className="hover:bg-gray-50">
                      <td className="px-5 py-4">
                        <p className="font-medium text-gray-900 truncate max-w-xs">{p.title}</p>
                        <p className="text-xs text-gray-400">{TYPE_LABELS[p.decision_type] || p.decision_type}</p>
                      </td>
                      <td className="px-4 py-4 text-gray-500">{DOMAIN_LABELS[p.financial_domain] || p.financial_domain}</td>
                      <td className="px-4 py-4 font-medium text-gray-700 tabular-nums">{fmtBRL(p.financial_exposure)}</td>
                      <td className="px-4 py-4 text-gray-500">{fmtDate(p.decided_at)}</td>
                      <td className="px-4 py-4">
                        <Badge color={p.days_pending > 1 ? 'red' : 'yellow'}>
                          {p.days_pending} dias
                        </Badge>
                      </td>
                      <td className="px-4 py-4 text-right">
                        <button
                          onClick={() => navigate(`/cases/${p.case_id}`)}
                          className="inline-flex items-center gap-1.5 text-xs font-medium text-brand-900 hover:text-brand-700"
                        >
                          Revisar
                          <ArrowRight className="h-3.5 w-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </Layout>
  )
}
