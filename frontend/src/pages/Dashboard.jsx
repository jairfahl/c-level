import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getCases, createCase, getDecisionIntelligence, getApiBalance } from '../lib/api'
import { Layout } from '../components/layout/Layout'
import { StateBadge } from '../components/ui/Badge'
import { PageSpinner } from '../components/ui/Spinner'
import { Modal } from '../components/ui/Modal'
import { Alert } from '../components/ui/Alert'
import { Plus, ChevronLeft, ChevronRight, Filter, TrendingUp, Brain, Target, ShieldAlert, Coins, Info, AlertTriangle } from 'lucide-react'

const DOMAINS = ['', 'planning', 'reporting', 'treasury', 'funding', 'risk']
const STATES = ['', 'DRAFT', 'CLASSIFIED', 'STRUCTURED', 'ANALYZED', 'RECOMMENDED', 'DECIDED', 'UNDER_REVIEW', 'CLOSED']
const DECISION_TYPES = [
  '', 'budget_adjustment', 'forecast_revision', 'capital_allocation',
  'debt_structuring', 'liquidity_management', 'risk_hedging', 'cost_reduction', 'investment_evaluation',
]
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

function ScoreDots({ score }) {
  if (!score) return <span className="text-gray-300 text-sm">—</span>
  return (
    <div className="flex gap-0.5">
      {[1,2,3,4,5].map((i) => (
        <div key={i} className={`w-2.5 h-2.5 rounded-full ${i <= score ? 'bg-brand-900' : 'bg-gray-200'}`} />
      ))}
    </div>
  )
}

// ── Create Case Modal ────────────────────────────────────────────────────────
function CreateCaseModal({ open, onClose }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({
    title: '', description: '', financial_domain: 'planning',
    financial_exposure: '', time_horizon: 'medium',
    external_agents_present: false, decision_type: 'budget_adjustment',
  })
  const [error, setError] = useState('')

  function set(k, v) { setForm((prev) => ({ ...prev, [k]: v })) }

  const mut = useMutation({
    mutationFn: () => createCase({ ...form, financial_exposure: Number(form.financial_exposure) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['cases'] })
      onClose()
      setForm({ title: '', description: '', financial_domain: 'planning', financial_exposure: '', time_horizon: 'medium', external_agents_present: false, decision_type: 'budget_adjustment' })
    },
    onError: (e) => setError(e.response?.data?.message || 'Erro ao criar caso.'),
  })

  const inputCls = 'w-full px-3 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-600'
  const labelCls = 'block text-sm font-medium text-gray-700 mb-1'

  return (
    <Modal open={open} onClose={onClose} title="Novo Caso de Decisão" size="lg">
      <div className="space-y-4">
        <div>
          <label className={labelCls}>Título *</label>
          <input type="text" value={form.title} onChange={(e) => set('title', e.target.value)}
            placeholder="Ex: Refinanciamento de dívida com Banco X" className={inputCls} />
          <p className="text-xs text-gray-400 mt-0.5">Entre 5 e 255 caracteres</p>
        </div>
        <div>
          <label className={labelCls}>Descrição *</label>
          <textarea value={form.description} onChange={(e) => set('description', e.target.value)}
            rows={3} placeholder="Descreva o contexto e motivação da decisão..." className={`${inputCls} resize-none`} />
          <p className="text-xs text-gray-400 mt-0.5">Mínimo 20 caracteres</p>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>Domínio Financeiro *</label>
            <select value={form.financial_domain} onChange={(e) => set('financial_domain', e.target.value)} className={inputCls}>
              {DOMAINS.slice(1).map((d) => <option key={d} value={d}>{DOMAIN_LABELS[d]}</option>)}
            </select>
          </div>
          <div>
            <label className={labelCls}>Tipo de Decisão *</label>
            <select value={form.decision_type} onChange={(e) => set('decision_type', e.target.value)} className={inputCls}>
              {DECISION_TYPES.slice(1).map((t) => <option key={t} value={t}>{TYPE_LABELS[t]}</option>)}
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>Exposição Financeira (R$) *</label>
            <input type="number" min="0.01" step="1000" value={form.financial_exposure}
              onChange={(e) => set('financial_exposure', e.target.value)}
              placeholder="Ex: 5000000" className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Horizonte Temporal</label>
            <select value={form.time_horizon} onChange={(e) => set('time_horizon', e.target.value)} className={inputCls}>
              <option value="short">Curto prazo</option>
              <option value="medium">Médio prazo</option>
              <option value="long">Longo prazo</option>
            </select>
          </div>
        </div>
        <label className="flex items-center gap-2.5 cursor-pointer">
          <input type="checkbox" checked={form.external_agents_present}
            onChange={(e) => set('external_agents_present', e.target.checked)}
            className="w-4 h-4 rounded accent-brand-900" />
          <span className="text-sm text-gray-700">Há agentes externos envolvidos (credores, investidores, governo)?</span>
        </label>

        {error && <Alert variant="error" message={error} />}

        <div className="flex gap-3 pt-2">
          <button onClick={onClose} className="flex-1 px-4 py-2.5 border border-gray-300 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-50">
            Cancelar
          </button>
          <button
            onClick={() => mut.mutate()}
            disabled={mut.isPending || !form.title || !form.description || !form.financial_exposure}
            className="flex-1 px-4 py-2.5 bg-brand-900 hover:bg-brand-800 text-white text-sm font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {mut.isPending ? 'Criando...' : 'Criar Caso'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

// ── Intelligence Panel ──────────────────────────────────────────────────────
function KpiCard({ icon: Icon, label, value, subtitle, color = 'brand', tooltip }) {
  const [showTip, setShowTip] = useState(false)
  const colors = {
    brand: 'bg-brand-50 text-brand-700 border-brand-200',
    green: 'bg-green-50 text-green-700 border-green-200',
    amber: 'bg-amber-50 text-amber-700 border-amber-200',
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
  }
  return (
    <div className={`border rounded-xl p-4 ${colors[color]}`}>
      <div className="flex items-center gap-2 mb-2">
        <Icon className="h-4 w-4 opacity-70" />
        <span className="text-xs font-semibold uppercase tracking-wide">{label}</span>
        {tooltip && (
          <div className="relative ml-auto"
            onMouseEnter={() => setShowTip(true)}
            onMouseLeave={() => setShowTip(false)}
          >
            <Info className="w-3.5 h-3.5 opacity-50 hover:opacity-100 cursor-help" />
            {showTip && (
              <div className="absolute right-0 top-5 z-50 w-64 p-3 text-xs text-gray-700 bg-white border border-gray-200 rounded-lg shadow-lg whitespace-pre-line font-normal normal-case tracking-normal">
                {tooltip}
              </div>
            )}
          </div>
        )}
      </div>
      <p className="text-2xl font-bold">{value ?? '—'}</p>
      {subtitle && <p className="text-xs mt-0.5 opacity-70">{subtitle}</p>}
    </div>
  )
}

function DomainBar({ item }) {
  const maxVal = 10
  const accWidth = item.avg_forecast_accuracy ? (item.avg_forecast_accuracy / maxVal) * 100 : 0
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm font-medium text-gray-700 w-28 truncate">{item.domain_label}</span>
      <div className="flex-1 h-5 bg-gray-100 rounded-full overflow-hidden relative">
        <div
          className="h-full bg-brand-600 rounded-full transition-all"
          style={{ width: `${Math.min(accWidth, 100)}%` }}
        />
        {item.avg_forecast_accuracy != null && (
          <span className="absolute inset-0 flex items-center justify-center text-xs font-semibold text-gray-700">
            {item.avg_forecast_accuracy}/10
          </span>
        )}
      </div>
      <span className="text-xs text-gray-400 w-16 text-right">{item.cases_count} caso(s)</span>
    </div>
  )
}

function IntelligencePanel() {
  const { data: intel } = useQuery({
    queryKey: ['decision-intelligence'],
    queryFn: getDecisionIntelligence,
    staleTime: 60_000,
    retry: false,
  })

  if (!intel || intel.total_cases_closed === 0) return null

  return (
    <div className="mb-8 bg-white border border-gray-200 rounded-xl p-6 space-y-5">
      <div className="flex items-center gap-2 mb-1">
        <Brain className="h-5 w-5 text-brand-700" />
        <h2 className="text-lg font-bold text-gray-900">Inteligência Decisória</h2>
        <span className="text-xs text-gray-400 ml-auto">{intel.total_heuristics_active} heurística(s) ativa(s)</span>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          icon={Target}
          label="Acurácia Média"
          value={intel.avg_forecast_accuracy != null ? `${intel.avg_forecast_accuracy}/10` : null}
          subtitle="Forecast vs Resultado"
          color="brand"
          tooltip={"Mede o quão próximas as projeções financeiras ficaram dos resultados reais em casos encerrados.\n\n1 = projeção totalmente errada\n10 = projeção perfeita\n\nValores acima de 7 indicam boa calibração do processo decisório."}
        />
        <KpiCard
          icon={TrendingUp}
          label="Divergência Bem-sucedida"
          value={intel.divergence_success_rate != null ? `${intel.divergence_success_rate}%` : null}
          subtitle={intel.divergence_total > 0 ? `${intel.divergence_success_count} de ${intel.divergence_total}` : 'Sem divergências'}
          color="green"
          tooltip={"Percentual de vezes em que o CFO divergiu da recomendação da IA e obteve resultado superior.\n\nTaxa alta indica bom julgamento executivo.\nTaxa baixa sugere que seguir a recomendação tende a ser mais seguro."}
        />
        <KpiCard
          icon={ShieldAlert}
          label="Materialização de Riscos"
          value={intel.avg_risk_realization != null ? `${intel.avg_risk_realization}%` : null}
          subtitle="Riscos que se concretizaram"
          color="amber"
          tooltip={"Média percentual dos riscos mapeados na etapa de estruturação que efetivamente se concretizaram.\n\n< 30% = boa gestão preventiva de riscos\n> 50% = riscos sub-mitigados, revisar processo de identificação"}
        />
        <KpiCard
          icon={Coins}
          label="Eficiência de Capital"
          value={intel.avg_capital_efficiency != null ? `${intel.avg_capital_efficiency}%` : null}
          subtitle="Retorno sobre capital alocado"
          color="blue"
          tooltip={"Relação entre o retorno obtido e o capital investido nas decisões financeiras.\n\n> 80% = excelente alocação de recursos\n50–80% = retorno adequado\n< 50% = capital subutilizado, revisar critérios de alocação"}
        />
      </div>

      {intel.domain_performance?.length > 0 && (
        <div>
          <p className="text-sm font-semibold text-gray-700 mb-3">Acurácia por Domínio</p>
          <div className="space-y-2">
            {intel.domain_performance.map((dp) => (
              <DomainBar key={dp.domain} item={dp} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ── API Credit Banner ────────────────────────────────────────────────────────
function ApiCreditBanner() {
  const { data: balance } = useQuery({
    queryKey: ['api-balance'],
    queryFn: getApiBalance,
    staleTime: 60_000,
    refetchInterval: 120_000,
    retry: false,
  })

  if (!balance || !balance.warning) return null

  const isZero = balance.remaining <= 0

  return (
    <div className={`mb-6 rounded-xl border px-5 py-4 flex items-start gap-3 ${
      isZero
        ? 'bg-red-50 border-red-200'
        : 'bg-amber-50 border-amber-200'
    }`}>
      <AlertTriangle className={`h-5 w-5 flex-shrink-0 mt-0.5 ${isZero ? 'text-red-600' : 'text-amber-600'}`} />
      <div className="flex-1">
        <p className={`text-sm font-semibold ${isZero ? 'text-red-800' : 'text-amber-800'}`}>
          {isZero
            ? 'Creditos da API esgotados'
            : 'Creditos da API baixos'
          }
        </p>
        <p className={`text-sm mt-0.5 ${isZero ? 'text-red-700' : 'text-amber-700'}`}>
          Saldo restante: <strong>US$ {balance.remaining.toFixed(2)}</strong> de US$ {balance.budget.toFixed(2)}.
          {' '}
          {isZero
            ? 'As analises por IA estao indisponiveis. Recarregue os creditos da API Anthropic para restaurar o funcionamento completo.'
            : 'Recarregue os creditos da API Anthropic para garantir continuidade das analises por IA.'
          }
        </p>
        <p className="text-xs mt-1.5 text-gray-500">
          Tokens consumidos: {balance.input_tokens.toLocaleString('pt-BR')} entrada / {balance.output_tokens.toLocaleString('pt-BR')} saida
        </p>
      </div>
    </div>
  )
}

// ── Dashboard ────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const navigate = useNavigate()
  const [filters, setFilters] = useState({ domain: '', state: '', decision_type: '', page: 1, limit: 20 })
  const [showCreate, setShowCreate] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['cases', filters],
    queryFn: () => getCases({
      domain: filters.domain || undefined,
      state: filters.state || undefined,
      decision_type: filters.decision_type || undefined,
      page: filters.page,
      limit: filters.limit,
    }),
  })

  function setFilter(k, v) { setFilters((prev) => ({ ...prev, [k]: v, page: 1 })) }

  const selectCls = 'px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-600 bg-white'

  return (
    <Layout>
      <div className="p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Casos de Decisão</h1>
            <p className="text-sm text-gray-500 mt-0.5">Governe cada decisão financeira com rigor e inteligência</p>
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 bg-brand-900 hover:bg-brand-800 text-white px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
          >
            <Plus className="h-4 w-4" />
            Novo Caso
          </button>
        </div>

        {/* API Credit Warning */}
        <ApiCreditBanner />

        {/* Filters */}
        <div className="flex items-center gap-3 mb-6 flex-wrap">
          <Filter className="h-4 w-4 text-gray-400" />
          <select value={filters.domain} onChange={(e) => setFilter('domain', e.target.value)} className={selectCls}>
            <option value="">Todos os domínios</option>
            {DOMAINS.slice(1).map((d) => <option key={d} value={d}>{DOMAIN_LABELS[d]}</option>)}
          </select>
          <select value={filters.state} onChange={(e) => setFilter('state', e.target.value)} className={selectCls}>
            <option value="">Todos os estados</option>
            {STATES.slice(1).map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <select value={filters.decision_type} onChange={(e) => setFilter('decision_type', e.target.value)} className={selectCls}>
            <option value="">Todos os tipos</option>
            {DECISION_TYPES.slice(1).map((t) => <option key={t} value={t}>{TYPE_LABELS[t]}</option>)}
          </select>
          {(filters.domain || filters.state || filters.decision_type) && (
            <button onClick={() => setFilters({ domain: '', state: '', decision_type: '', page: 1, limit: 20 })}
              className="text-xs text-red-500 hover:text-red-700 font-medium">
              Limpar filtros
            </button>
          )}
        </div>

        {/* Intelligence Panel */}
        <IntelligencePanel />

        {/* Table */}
        {isLoading ? (
          <PageSpinner />
        ) : data?.items?.length === 0 ? (
          <div className="text-center py-20">
            <TrendingUp className="h-12 w-12 text-gray-200 mx-auto mb-4" />
            <p className="text-gray-500 font-medium">Nenhum caso encontrado</p>
            <p className="text-gray-400 text-sm mt-1">Crie seu primeiro caso de decisão financeira</p>
            <button onClick={() => setShowCreate(true)} className="mt-4 bg-brand-900 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-brand-800">
              Criar Caso
            </button>
          </div>
        ) : (
          <>
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50">
                    <th className="text-left px-5 py-3.5 font-semibold text-gray-600 text-xs uppercase tracking-wide">Título</th>
                    <th className="text-left px-4 py-3.5 font-semibold text-gray-600 text-xs uppercase tracking-wide">Domínio</th>
                    <th className="text-left px-4 py-3.5 font-semibold text-gray-600 text-xs uppercase tracking-wide">Tipo</th>
                    <th className="text-left px-4 py-3.5 font-semibold text-gray-600 text-xs uppercase tracking-wide">Impacto</th>
                    <th className="text-left px-4 py-3.5 font-semibold text-gray-600 text-xs uppercase tracking-wide">Exposição</th>
                    <th className="text-left px-4 py-3.5 font-semibold text-gray-600 text-xs uppercase tracking-wide">Estado</th>
                    <th className="text-left px-4 py-3.5 font-semibold text-gray-600 text-xs uppercase tracking-wide">Data</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {data?.items?.map((c) => (
                    <tr
                      key={c.id}
                      onClick={() => navigate(`/cases/${c.id}`)}
                      className="hover:bg-blue-50 cursor-pointer transition-colors"
                    >
                      <td className="px-5 py-4">
                        <p className="font-medium text-gray-900 truncate max-w-xs">{c.title}</p>
                      </td>
                      <td className="px-4 py-4 text-gray-500 capitalize">{DOMAIN_LABELS[c.financial_domain] || c.financial_domain}</td>
                      <td className="px-4 py-4 text-gray-500">{TYPE_LABELS[c.decision_type] || c.decision_type}</td>
                      <td className="px-4 py-4"><ScoreDots score={c.impact_score} /></td>
                      <td className="px-4 py-4 text-gray-700 font-medium tabular-nums">{fmtBRL(c.financial_exposure)}</td>
                      <td className="px-4 py-4"><StateBadge state={c.state} /></td>
                      <td className="px-4 py-4 text-gray-400">{fmtDate(c.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {data?.total > filters.limit && (
              <div className="flex items-center justify-between mt-4">
                <p className="text-sm text-gray-500">
                  {data.total} casos · página {filters.page} de {Math.ceil(data.total / filters.limit)}
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setFilters((p) => ({ ...p, page: p.page - 1 }))}
                    disabled={filters.page === 1}
                    className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => setFilters((p) => ({ ...p, page: p.page + 1 }))}
                    disabled={filters.page >= Math.ceil(data.total / filters.limit)}
                    className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      <CreateCaseModal open={showCreate} onClose={() => setShowCreate(false)} />
    </Layout>
  )
}
