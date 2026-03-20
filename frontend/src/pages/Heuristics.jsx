import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getHeuristics, createHeuristic, deactivateHeuristic, getLearningSummary } from '../lib/api'
import { Layout } from '../components/layout/Layout'
import { Modal } from '../components/ui/Modal'
import { Alert } from '../components/ui/Alert'
import { PageSpinner } from '../components/ui/Spinner'
import { Badge } from '../components/ui/Badge'
import { Plus, PowerOff, Brain, TrendingUp, AlertTriangle, CheckCircle2, ShieldAlert, Landmark, BookOpen, Lightbulb, Sparkles } from 'lucide-react'

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

const HEURISTIC_META = {
  high_accuracy: {
    title: 'Alta Acurácia de Forecast',
    description: 'A projeção financeira foi muito precisa comparada ao resultado real.',
    icon: TrendingUp,
    color: 'text-emerald-600',
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
    metric: (v) => v.forecast_accuracy_score != null ? `${v.forecast_accuracy_score}/10` : null,
    metricLabel: 'Acurácia',
  },
  divergence_risk: {
    title: 'Risco de Divergência',
    description: 'A divergência do executivo em relação ao Mentor resultou em pior outcome.',
    icon: AlertTriangle,
    color: 'text-amber-600',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    metric: () => null,
    metricLabel: null,
  },
  divergence_success: {
    title: 'Divergência Bem-Sucedida',
    description: 'O executivo divergiu da recomendação e obteve resultado positivo.',
    icon: CheckCircle2,
    color: 'text-blue-600',
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    metric: (v) => v.forecast_accuracy_score != null ? `${v.forecast_accuracy_score}/10` : null,
    metricLabel: 'Acurácia',
  },
  high_risk_materialization: {
    title: 'Alta Materialização de Riscos',
    description: 'Mais da metade dos riscos identificados se materializaram.',
    icon: ShieldAlert,
    color: 'text-red-600',
    bg: 'bg-red-50',
    border: 'border-red-200',
    metric: (v) => v.risk_realization_rate != null ? `${v.risk_realization_rate}%` : null,
    metricLabel: 'Taxa de riscos',
  },
  capital_efficient: {
    title: 'Eficiência de Capital',
    description: 'O capital alocado foi utilizado com alta eficiência.',
    icon: Landmark,
    color: 'text-violet-600',
    bg: 'bg-violet-50',
    border: 'border-violet-200',
    metric: (v) => v.capital_allocation_efficiency_score != null ? `${v.capital_allocation_efficiency_score}%` : null,
    metricLabel: 'Eficiência',
  },
}

const DEFAULT_META = {
  title: null, description: null, icon: Brain,
  color: 'text-gray-600', bg: 'bg-gray-50', border: 'border-gray-200',
  metric: () => null, metricLabel: null,
}

function HeuristicCard({ h, onDeactivate }) {
  const val = h.heuristic_value || {}
  const meta = HEURISTIC_META[val.type] || DEFAULT_META
  const Icon = meta.icon
  const confidence = val.confidence != null ? Math.round(val.confidence * 100) : null
  const metricValue = meta.metric(val)
  const framework = FRAMEWORK_LABELS[val.framework] || val.framework

  return (
    <div className={`px-5 py-4 flex items-start gap-4 ${!h.active ? 'opacity-60' : ''}`}>
      <div className={`flex-shrink-0 w-10 h-10 rounded-lg ${meta.bg} flex items-center justify-center mt-0.5`}>
        <Icon className={`w-5 h-5 ${meta.color}`} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5 flex-wrap">
          <span className="text-sm font-semibold text-gray-900">
            {meta.title || h.heuristic_key}
          </span>
          <Badge color={h.active ? 'green' : 'gray'}>{h.active ? 'Ativa' : 'Inativa'}</Badge>
        </div>
        {meta.description && (
          <p className="text-xs text-gray-500 mb-2">{meta.description}</p>
        )}
        <div className="flex items-center gap-3 flex-wrap">
          <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full ${meta.bg} ${meta.color} border ${meta.border}`}>
            {DOMAIN_LABELS[h.financial_domain] || h.financial_domain}
          </span>
          <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border border-gray-200">
            {TYPE_LABELS[h.decision_type] || h.decision_type}
          </span>
          {framework && (
            <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-brand-50 text-brand-700 border border-brand-200">
              {framework}
            </span>
          )}
        </div>
        <div className="flex items-center gap-5 mt-3">
          {metricValue && (
            <div className="text-center">
              <p className="text-lg font-bold text-gray-900">{metricValue}</p>
              <p className="text-[10px] uppercase tracking-wide text-gray-400">{meta.metricLabel}</p>
            </div>
          )}
          {confidence != null && (
            <div className="flex-1 max-w-[180px]">
              <div className="flex items-center justify-between mb-0.5">
                <span className="text-[10px] uppercase tracking-wide text-gray-400">Confianca</span>
                <span className="text-xs font-semibold text-gray-700">{confidence}%</span>
              </div>
              <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${confidence >= 70 ? 'bg-emerald-500' : confidence >= 40 ? 'bg-amber-400' : 'bg-red-400'}`}
                  style={{ width: `${confidence}%` }}
                />
              </div>
            </div>
          )}
        </div>
        {h.source_case_id && (
          <Link
            to={`/cases/${h.source_case_id}`}
            className="inline-flex items-center gap-1 text-[11px] text-brand-700 hover:text-brand-900 hover:underline mt-2"
          >
            Ver caso de origem &rarr;
          </Link>
        )}
      </div>
      {h.active && (
        <button
          onClick={() => onDeactivate(h.id)}
          className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 text-xs text-red-600 hover:bg-red-50 rounded-lg border border-red-200 transition-colors"
        >
          <PowerOff className="h-3.5 w-3.5" />
          Desativar
        </button>
      )}
    </div>
  )
}

function toKey(title) {
  return title
    .toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_|_$/g, '')
    .slice(0, 60)
}

const CONFIDENCE_LABELS = [
  { min: 0,  label: 'Baixa', sublabel: 'Percepção inicial, poucos dados', color: 'text-red-500' },
  { min: 40, label: 'Moderada', sublabel: 'Baseado em alguns casos', color: 'text-amber-500' },
  { min: 70, label: 'Alta', sublabel: 'Padrão consistente observado', color: 'text-emerald-500' },
  { min: 90, label: 'Muito Alta', sublabel: 'Validado repetidamente', color: 'text-emerald-700' },
]

function getConfidenceLabel(val) {
  return [...CONFIDENCE_LABELS].reverse().find((c) => val >= c.min) || CONFIDENCE_LABELS[0]
}

function CreateHeuristicModal({ open, onClose }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({
    decision_type: 'budget_adjustment',
    financial_domain: 'planning',
    title: '',
    insight: '',
    trigger: '',
    always_check: '',
    confidence: 70,
    source_case_id: '',
  })
  const [error, setError] = useState('')

  function set(k, v) { setForm((prev) => ({ ...prev, [k]: v })) }

  const confLabel = getConfidenceLabel(form.confidence)
  const canSubmit = form.title.length >= 3 && form.insight.length >= 10

  const mut = useMutation({
    mutationFn: () => {
      const value = {
        insight: form.insight,
        confidence: form.confidence / 100,
      }
      if (form.trigger.trim()) value.trigger = form.trigger.trim()
      if (form.always_check.trim()) value.always_check = form.always_check.trim()
      return createHeuristic({
        decision_type: form.decision_type,
        financial_domain: form.financial_domain,
        heuristic_key: toKey(form.title),
        heuristic_value: value,
        source_case_id: form.source_case_id || null,
      })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['heuristics'] })
      qc.invalidateQueries({ queryKey: ['learning-summary'] })
      onClose()
    },
    onError: (e) => setError(e.message || e.response?.data?.message || 'Erro ao registrar.'),
  })

  const inputCls = 'w-full px-3 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-600'
  const labelCls = 'block text-sm font-medium text-gray-700 mb-1'

  return (
    <Modal open={open} onClose={onClose} title="" size="md">
      <div className="space-y-5">
        {/* Header */}
        <div className="flex items-start gap-3 -mt-2">
          <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center">
            <Lightbulb className="h-5 w-5 text-amber-600" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-gray-900">Registrar Aprendizado</h2>
            <p className="text-xs text-gray-400 mt-0.5">
              Transforme experiência em sabedoria reutilizável. O Mentor vai incorporar este insight em futuras recomendações.
            </p>
          </div>
        </div>

        {/* Contexto: Domínio + Tipo */}
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Quando aplicar</p>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelCls}>Domínio</label>
              <select value={form.financial_domain} onChange={(e) => set('financial_domain', e.target.value)} className={inputCls}>
                {Object.entries(DOMAIN_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <div>
              <label className={labelCls}>Tipo de Decisão</label>
              <select value={form.decision_type} onChange={(e) => set('decision_type', e.target.value)} className={inputCls}>
                {Object.entries(TYPE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
          </div>
        </div>

        {/* Título */}
        <div>
          <label className={labelCls}>Título do aprendizado *</label>
          <input
            type="text"
            value={form.title}
            onChange={(e) => set('title', e.target.value)}
            placeholder='Ex: "Negociação bilateral sempre supera a sindicalizada"'
            className={inputCls}
          />
        </div>

        {/* Insight principal */}
        <div>
          <label className={labelCls}>O que aprendemos? *</label>
          <textarea
            value={form.insight}
            onChange={(e) => set('insight', e.target.value)}
            rows={3}
            placeholder="Descreva o padrão ou lição em linguagem livre. Ex: Em reestruturações de dívida com bancos múltiplos, negociações bilaterais geraram spreads 15-20% menores que sindicalizadas."
            className={`${inputCls} resize-none`}
          />
          <p className="text-xs text-gray-400 mt-0.5">Quanto mais específico, mais útil será em análises futuras.</p>
        </div>

        {/* Campos opcionais: trigger + always_check */}
        <div className="grid grid-cols-1 gap-3">
          <div>
            <label className={labelCls}>Em que situação isso se aplica? <span className="text-gray-400 font-normal">(opcional)</span></label>
            <input
              type="text"
              value={form.trigger}
              onChange={(e) => set('trigger', e.target.value)}
              placeholder='Ex: "Quando houver mais de 2 credores na mesa"'
              className={inputCls}
            />
          </div>
          <div>
            <label className={labelCls}>O que nunca esquecer de verificar? <span className="text-gray-400 font-normal">(opcional)</span></label>
            <input
              type="text"
              value={form.always_check}
              onChange={(e) => set('always_check', e.target.value)}
              placeholder='Ex: "Comparar custo total (spread + fees) antes de decidir formato"'
              className={inputCls}
            />
          </div>
        </div>

        {/* Confiança */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className={labelCls + ' mb-0'}>Nível de confiança</label>
            <span className={`text-sm font-semibold ${confLabel.color}`}>
              {confLabel.label} — {form.confidence}%
            </span>
          </div>
          <input
            type="range"
            min={10}
            max={100}
            step={5}
            value={form.confidence}
            onChange={(e) => set('confidence', Number(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-brand-700"
          />
          <div className="flex justify-between mt-1">
            <span className="text-[10px] text-gray-400">Percepção inicial</span>
            <span className="text-[10px] text-gray-400">Validado repetidamente</span>
          </div>
          <p className="text-xs text-gray-400 mt-1 italic">{confLabel.sublabel}</p>
        </div>

        {/* Caso de origem */}
        <div>
          <label className={labelCls}>Originado de qual caso? <span className="text-gray-400 font-normal">(opcional)</span></label>
          <input
            type="text"
            value={form.source_case_id}
            onChange={(e) => set('source_case_id', e.target.value)}
            placeholder="Cole o ID do caso que originou esta lição"
            className={inputCls}
          />
        </div>

        {error && <Alert variant="error" message={error} />}

        {/* Actions */}
        <div className="flex gap-3 pt-1">
          <button onClick={onClose} className="flex-1 px-4 py-2.5 border border-gray-300 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-50">
            Cancelar
          </button>
          <button
            onClick={() => mut.mutate()}
            disabled={mut.isPending || !canSubmit}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-brand-900 hover:bg-brand-800 text-white text-sm font-medium rounded-lg disabled:opacity-50 transition-colors"
          >
            <Sparkles className="h-4 w-4" />
            {mut.isPending ? 'Registrando...' : 'Registrar Aprendizado'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

export default function Heuristics() {
  const qc = useQueryClient()
  const [filters, setFilters] = useState({ decision_type: '', domain: '' })
  const [showCreate, setShowCreate] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['heuristics', filters],
    queryFn: () => getHeuristics({
      decision_type: filters.decision_type || undefined,
      domain: filters.domain || undefined,
    }),
  })

  const { data: summaryData, isLoading: summaryLoading } = useQuery({
    queryKey: ['learning-summary'],
    queryFn: getLearningSummary,
  })

  const deactivate = useMutation({
    mutationFn: (id) => deactivateHeuristic(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['heuristics'] })
      qc.invalidateQueries({ queryKey: ['learning-summary'] })
    },
  })

  const selectCls = 'px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-600 bg-white'

  return (
    <Layout>
      <div className="p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Aprendizados</h1>
            <p className="text-sm text-gray-500 mt-0.5">Lições que o Mentor incorpora automaticamente em futuras recomendações</p>
          </div>
          <button onClick={() => setShowCreate(true)} className="flex items-center gap-2 bg-brand-900 hover:bg-brand-800 text-white px-4 py-2.5 rounded-lg text-sm font-medium">
            <Lightbulb className="h-4 w-4" />
            Registrar Aprendizado
          </button>
        </div>

        {/* Learning Summary */}
        {summaryLoading ? (
          <div className="mb-6 rounded-xl border border-brand-200 bg-gradient-to-r from-brand-50 to-blue-50 p-5 animate-pulse">
            <div className="h-5 bg-brand-100 rounded w-48 mb-3" />
            <div className="h-4 bg-brand-100 rounded w-full mb-2" />
            <div className="h-4 bg-brand-100 rounded w-3/4" />
          </div>
        ) : summaryData?.summary ? (
          <div className="mb-6 rounded-xl border border-brand-200 bg-gradient-to-r from-brand-50 to-blue-50 p-5">
            <div className="flex items-center gap-2 mb-3">
              <BookOpen className="h-5 w-5 text-brand-700" />
              <h2 className="text-sm font-semibold text-brand-900">Resumo de Aprendizado</h2>
            </div>
            <p className="text-sm text-gray-700 whitespace-pre-line leading-relaxed">
              {summaryData.summary}
            </p>
            {summaryData.top_frameworks?.length > 0 && (
              <div className="mt-4 pt-3 border-t border-brand-100">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Métodos mais aplicados</p>
                <div className="flex flex-wrap gap-2">
                  {summaryData.top_frameworks.map((fw) => (
                    <span
                      key={fw.framework}
                      className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full bg-white border border-brand-200 text-brand-800"
                    >
                      {fw.framework}
                      <span className="bg-brand-100 text-brand-700 font-semibold px-1.5 py-0.5 rounded-full text-[10px] leading-none">
                        {fw.count}x
                      </span>
                    </span>
                  ))}
                </div>
              </div>
            )}
            <p className="text-xs text-gray-400 mt-3">
              {summaryData.heuristics_count} heurística{summaryData.heuristics_count !== 1 ? 's' : ''} ativa{summaryData.heuristics_count !== 1 ? 's' : ''}
              {' · '}
              {summaryData.llm_generated ? 'Gerado por IA' : 'Resumo automático'}
            </p>
          </div>
        ) : null}

        {/* Filters */}
        <div className="flex gap-3 mb-6 flex-wrap">
          <select value={filters.domain} onChange={(e) => setFilters((p) => ({ ...p, domain: e.target.value }))} className={selectCls}>
            <option value="">Todos os domínios</option>
            {Object.entries(DOMAIN_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <select value={filters.decision_type} onChange={(e) => setFilters((p) => ({ ...p, decision_type: e.target.value }))} className={selectCls}>
            <option value="">Todos os tipos</option>
            {Object.entries(TYPE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </div>

        {isLoading ? (
          <PageSpinner />
        ) : !data?.heuristics?.length ? (
          <div className="text-center py-20">
            <Brain className="h-12 w-12 text-gray-200 mx-auto mb-4" />
            <p className="text-gray-500 font-medium">Nenhuma heurística registrada</p>
            <p className="text-gray-400 text-sm mt-1">Heurísticas são aprendidas automaticamente ao fechar casos</p>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-5 py-3 border-b border-gray-100 bg-gray-50 text-xs uppercase tracking-wide font-semibold text-gray-500">
              {data.total} heurística{data.total !== 1 ? 's' : ''}
            </div>
            <div className="divide-y divide-gray-100">
              {data.heuristics.map((h) => (
                <HeuristicCard key={h.id} h={h} onDeactivate={(id) => deactivate.mutate(id)} />
              ))}
            </div>
          </div>
        )}
      </div>
      <CreateHeuristicModal open={showCreate} onClose={() => setShowCreate(false)} />
    </Layout>
  )
}
