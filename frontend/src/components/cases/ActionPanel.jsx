import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  classifyCase, structureCase, analyzeCase, reanalyzeCase,
  suggestMethods, suggestReclassification, reclassifyCase,
  recordHypothesis, decideCase, reviewCase, getHeuristicAlerts,
} from '../../lib/api'
import { jaccardSimilarity, RUBBER_STAMP_THRESHOLD } from '../../lib/textSimilarity'
import { Spinner } from '../ui/Spinner'
import { Alert } from '../ui/Alert'
import {
  Plus, Trash2, Brain, CheckCircle, RefreshCw, Info, X, Lock,
  AlertTriangle, BarChart3, RotateCw, Users, Scale, Grid3x3,
  Coins, Table2, Calculator, GitBranch, Crosshair, MessageCircle,
} from 'lucide-react'

const FRAMEWORK_LABELS = {
  pdca: 'PDCA',
  scenario_analysis: 'Análise de Cenários',
  game_theory: 'Teoria dos Jogos',
  trade_off: 'Trade-Off',
  risk_matrix: 'Matriz de Riscos',
  capital_allocation: 'Alocação de Capital',
  decision_matrix: 'Matriz de Decisão',
  cost_benefit_analysis: 'Custo-Benefício',
  decision_tree: 'Árvore de Decisão',
  swot_analysis: 'SWOT / FOFA',
  delphi_method: 'Método Delphi',
}

const FRAMEWORK_ICONS = {
  pdca: RotateCw,
  scenario_analysis: BarChart3,
  game_theory: Users,
  trade_off: Scale,
  risk_matrix: Grid3x3,
  capital_allocation: Coins,
  decision_matrix: Table2,
  cost_benefit_analysis: Calculator,
  decision_tree: GitBranch,
  swot_analysis: Crosshair,
  delphi_method: MessageCircle,
}

const COMPLEXITY_COLORS = {
  baixa: 'bg-green-100 text-green-700',
  média: 'bg-yellow-100 text-yellow-700',
  alta: 'bg-red-100 text-red-700',
}

const DOMAIN_LABELS = {
  treasury: 'Tesouraria',
  corporate_finance: 'Finanças Corporativas',
  capital_markets: 'Mercado de Capitais',
  risk_management: 'Gestão de Riscos',
  accounting_control: 'Contabilidade & Controle',
  investor_relations: 'Relações com Investidores',
  tax_planning: 'Planejamento Tributário',
  mergers_acquisitions: 'Fusões & Aquisições',
}

const TYPE_LABELS = {
  budget_adjustment: 'Ajuste de Budget',
  forecast_revision: 'Revisão de Forecast',
  capital_allocation: 'Alocação de Capital',
  debt_structuring: 'Estruturação de Dívida',
  liquidity_management: 'Gestão de Liquidez',
  risk_hedging: 'Hedge / Proteção',
  cost_reduction: 'Redução de Custos',
  investment_evaluation: 'Avaliação de Investimento',
}

function Field({ label, required, tooltip, children }) {
  const [showTip, setShowTip] = useState(false)
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <label className="block text-sm font-medium text-gray-700">
          {label}{required && <span className="text-red-500 ml-0.5">*</span>}
        </label>
        {tooltip && (
          <div className="relative"
            onMouseEnter={() => setShowTip(true)}
            onMouseLeave={() => setShowTip(false)}
          >
            <Info className="w-4 h-4 text-gray-400 hover:text-brand-600 cursor-help" />
            {showTip && (
              <div className="absolute right-0 top-6 z-50 w-72 p-3 text-xs text-gray-700 bg-white border border-gray-200 rounded-lg shadow-lg whitespace-pre-line">
                {tooltip}
              </div>
            )}
          </div>
        )}
      </div>
      {children}
    </div>
  )
}

function Btn({ children, onClick, disabled, loading, variant = 'primary', type = 'button', className = '' }) {
  const styles = {
    primary: 'bg-brand-900 hover:bg-brand-800 text-white',
    secondary: 'bg-gray-100 hover:bg-gray-200 text-gray-700',
    danger: 'bg-red-600 hover:bg-red-700 text-white',
  }
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${styles[variant]} ${className}`}
    >
      {loading && <Spinner size="sm" />}
      {children}
    </button>
  )
}

// ── DRAFT → CLASSIFIED ──────────────────────────────────────────────────────
function ClassifyPanel({ caseId }) {
  const qc = useQueryClient()
  const [score, setScore] = useState(3)
  const [result, setResult] = useState(null)

  const { data: caseData } = useQuery({ queryKey: ['case', caseId] })

  const [suggestionDismissed, setSuggestionDismissed] = useState(false)

  const { data: suggestion, isLoading: checkingClassification } = useQuery({
    queryKey: ['classification-suggestion', caseId],
    queryFn: () => suggestReclassification(caseId),
    staleTime: Infinity,
    retry: false,
  })

  const reclassifyMut = useMutation({
    mutationFn: (body) => reclassifyCase(caseId, body),
    onSuccess: () => {
      setSuggestionDismissed(true)
      qc.invalidateQueries({ queryKey: ['case', caseId] })
    },
  })

  const showSuggestion = suggestion?.reclassification_needed && !suggestionDismissed

  const mut = useMutation({
    mutationFn: () => classifyCase(caseId, { impact_score: score }),
    onSuccess: (data) => {
      setResult(data)
      qc.invalidateQueries({ queryKey: ['case', caseId] })
    },
  })

  return (
    <div className="space-y-5">
      <p className="text-sm text-gray-600">
        Defina o score de impacto financeiro. O sistema selecionará automaticamente o framework analítico.
      </p>
      {checkingClassification && (
        <p className="text-xs text-gray-400 flex items-center gap-1.5">
          <span className="animate-spin inline-block h-3 w-3 border-2 border-gray-400 border-t-transparent rounded-full" />
          Verificando classificação com o Mentor...
        </p>
      )}

      {showSuggestion && (
        <div className="bg-amber-50 border border-amber-300 rounded-lg p-4 space-y-3">
          <div className="flex items-start gap-2">
            <span className="text-amber-500 text-xl">💡</span>
            <div className="flex-1">
              <p className="text-sm font-semibold text-amber-900">
                Mentor sugere reclassificar este caso
              </p>
              <p className="text-xs text-amber-700 mt-1">{suggestion.reason}</p>
              <div className="mt-2 space-y-1 text-xs text-amber-800">
                {suggestion.suggested_domain &&
                  suggestion.suggested_domain !== caseData?.financial_domain && (
                  <p>
                    <strong>Domínio:</strong> {DOMAIN_LABELS[caseData?.financial_domain]}{' '}
                    → <strong>{DOMAIN_LABELS[suggestion.suggested_domain]}</strong>
                  </p>
                )}
                {suggestion.suggested_decision_type &&
                  suggestion.suggested_decision_type !== caseData?.decision_type && (
                  <p>
                    <strong>Tipo:</strong> {TYPE_LABELS[caseData?.decision_type]}{' '}
                    → <strong>{TYPE_LABELS[suggestion.suggested_decision_type]}</strong>
                  </p>
                )}
              </div>
              <p className="text-xs text-amber-600 mt-2 italic">
                ⚠ Prosseguir com classificação incorreta compromete o aprendizado:
                as heurísticas geradas ao final do ciclo serão associadas ao domínio/tipo
                errado, reduzindo a qualidade das recomendações futuras.
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => reclassifyMut.mutate({
                financial_domain: suggestion.suggested_domain,
                decision_type: suggestion.suggested_decision_type,
              })}
              disabled={reclassifyMut.isPending}
              className="flex-1 py-1.5 px-3 bg-amber-600 text-white text-xs font-semibold rounded-lg hover:bg-amber-700 disabled:opacity-50"
            >
              {reclassifyMut.isPending ? 'Aplicando...' : 'Aplicar sugestão'}
            </button>
            <button
              onClick={() => setSuggestionDismissed(true)}
              className="flex-1 py-1.5 px-3 border border-amber-400 text-amber-800 text-xs font-semibold rounded-lg hover:bg-amber-100"
            >
              Manter minha classificação
            </button>
          </div>
        </div>
      )}

      <Field label="Score de Impacto (1–5)" required>
        <div className="flex items-center gap-4">
          <input
            type="range" min={1} max={5} value={score}
            onChange={(e) => setScore(Number(e.target.value))}
            className="flex-1 accent-brand-900"
          />
          <div className="flex gap-1">
            {[1,2,3,4,5].map((v) => (
              <button
                key={v}
                onClick={() => setScore(v)}
                className={`w-9 h-9 rounded-lg text-sm font-bold border-2 transition-colors ${
                  score === v
                    ? 'bg-brand-900 text-white border-brand-900'
                    : 'bg-white text-gray-400 border-gray-200 hover:border-brand-900'
                }`}
              >
                {v}
              </button>
            ))}
          </div>
        </div>
        <p className="text-xs text-gray-400 mt-1">
          1–2: baixo · 3: médio · 4: alto · 5: crítico
        </p>
      </Field>

      {mut.error && (
        <Alert variant="error" message={mut.error.response?.data?.message || 'Erro ao classificar.'} />
      )}
      {result && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-1">
          <p className="text-sm font-semibold text-blue-900">Classificado com sucesso</p>
          <p className="text-sm text-blue-700">Framework: <strong>{FRAMEWORK_LABELS[result.framework_selected] || result.framework_selected}</strong></p>
          <p className="text-sm text-blue-700">Cenário obrigatório: <strong>{result.scenario_required ? 'Sim' : 'Não'}</strong></p>
        </div>
      )}

      <Btn onClick={() => mut.mutate()} loading={mut.isPending} disabled={!!result}>
        Classificar Caso
      </Btn>
    </div>
  )
}

// ── CLASSIFIED → STRUCTURED ─────────────────────────────────────────────────
function ListEditor({ items, onUpdate, onAdd, onRemove, label, placeholder }) {
  return (
    <Field label={label} required>
      <div className="space-y-2">
        {items.map((v, i) => (
          <div key={i} className="flex gap-2">
            <input
              type="text"
              value={v}
              onChange={(e) => onUpdate(i, e.target.value)}
              placeholder={`${placeholder} ${i + 1}`}
              className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-600"
            />
            {items.length > 3 && (
              <button onClick={() => onRemove(i)} className="p-2 text-red-400 hover:text-red-600">
                <Trash2 className="h-4 w-4" />
              </button>
            )}
          </div>
        ))}
        <button
          onClick={onAdd}
          className="flex items-center gap-1.5 text-xs text-brand-700 hover:text-brand-900 font-medium"
        >
          <Plus className="h-3.5 w-3.5" /> Adicionar mais
        </button>
      </div>
      <p className="text-xs text-gray-400 mt-1">Mínimo 3 itens preenchidos</p>
    </Field>
  )
}

function StructurePanel({ caseId }) {
  const qc = useQueryClient()
  const [assumptions, setAssumptions] = useState(['', '', ''])
  const [risks, setRisks] = useState(['', '', ''])
  const [result, setResult] = useState(null)

  const mut = useMutation({
    mutationFn: () => structureCase(caseId, {
      assumptions: assumptions.filter(Boolean),
      risks: risks.filter(Boolean),
    }),
    onSuccess: (data) => {
      setResult(data)
      qc.invalidateQueries({ queryKey: ['case', caseId] })
    },
  })

  return (
    <div className="space-y-6">
      <p className="text-sm text-gray-600">
        Registre as premissas e riscos que embasam esta decisão. O Mentor CFO vai identificar premissas implícitas adicionais.
      </p>
      <ListEditor
        items={assumptions}
        onUpdate={(i, val) => setAssumptions((prev) => prev.map((v, j) => j === i ? val : v))}
        onAdd={() => setAssumptions((prev) => [...prev, ''])}
        onRemove={(i) => setAssumptions((prev) => prev.filter((_, j) => j !== i))}
        label="Premissas"
        placeholder="Premissa"
      />
      <ListEditor
        items={risks}
        onUpdate={(i, val) => setRisks((prev) => prev.map((v, j) => j === i ? val : v))}
        onAdd={() => setRisks((prev) => [...prev, ''])}
        onRemove={(i) => setRisks((prev) => prev.filter((_, j) => j !== i))}
        label="Riscos"
        placeholder="Risco"
      />

      {mut.error && (
        <Alert variant="error" message={mut.error.response?.data?.message || 'Erro ao estruturar.'} />
      )}
      {result && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-1">
          <p className="text-sm font-semibold text-blue-900">Estruturado com sucesso</p>
          <p className="text-sm text-blue-700">{result.assumptions_count} premissas · {result.risks_count} riscos registrados</p>
        </div>
      )}

      <Btn onClick={() => mut.mutate()} loading={mut.isPending} disabled={!!result}>
        Estruturar Caso
      </Btn>
    </div>
  )
}

// ── STRUCTURED → ANALYZED → RECOMMENDED ─────────────────────────────────────
function AnalyzePanel({ caseId, caseData }) {
  const qc = useQueryClient()
  const [selectedFrameworks, setSelectedFrameworks] = useState(null)
  const [primaryFramework, setPrimaryFramework] = useState(null)
  const [availableFrameworks, setAvailableFrameworks] = useState([])
  const [rationale, setRationale] = useState({})
  const [suggestionDetails, setSuggestionDetails] = useState([])
  const [availableCatalog, setAvailableCatalog] = useState([])
  const [showAddMenu, setShowAddMenu] = useState(false)
  const [result, setResult] = useState(null)
  const [hypothesisText, setHypothesisText] = useState('')
  const [hypothesisSubmitted, setHypothesisSubmitted] = useState(
    () => !!caseData?.initial_hypothesis
  )

  const hypothesisMut = useMutation({
    mutationFn: () => recordHypothesis(caseId, { initial_hypothesis: hypothesisText }),
    onSuccess: () => {
      setHypothesisSubmitted(true)
      qc.invalidateQueries({ queryKey: ['case', caseId] })
    },
  })

  // Reload guard: if caseData already has initial_hypothesis (e.g. page reload), auto-set
  useEffect(() => {
    if (caseData?.initial_hypothesis && !hypothesisSubmitted) {
      setHypothesisSubmitted(true)
    }
  }, [caseData?.initial_hypothesis])

  const { data: suggestions, isLoading: loadingSuggestions, error: suggestError } = useQuery({
    queryKey: ['suggest-methods', caseId],
    queryFn: () => suggestMethods(caseId),
  })

  useEffect(() => {
    if (suggestions && !selectedFrameworks) {
      setSelectedFrameworks(suggestions.suggested_frameworks)
      setPrimaryFramework(suggestions.primary_framework)
      setAvailableFrameworks(suggestions.available_frameworks)
      setRationale(suggestions.suggestions_rationale)
      setSuggestionDetails(suggestions.suggestion_details || [])
      setAvailableCatalog(suggestions.available_catalog || [])
    }
  }, [suggestions])

  const mut = useMutation({
    mutationFn: () => analyzeCase(caseId, { frameworks_selected: selectedFrameworks }),
    onSuccess: (data) => {
      setResult(data)
      qc.invalidateQueries({ queryKey: ['case', caseId] })
    },
  })

  const removeFramework = (fw) => {
    if (fw === primaryFramework) return
    setSelectedFrameworks((prev) => prev.filter((f) => f !== fw))
  }

  const addFramework = (fw) => {
    if (!selectedFrameworks || selectedFrameworks.includes(fw) || selectedFrameworks.length >= 4) return
    setSelectedFrameworks((prev) => [...prev, fw])
    setShowAddMenu(false)
  }

  if (loadingSuggestions) return <div className="flex justify-center py-8"><Spinner /></div>
  if (suggestError) return <Alert variant="error" message="Erro ao carregar sugestões de métodos." />

  const frameworksNotSelected = availableFrameworks.filter((fw) => !selectedFrameworks?.includes(fw))

  return (
    <div className="space-y-5">
      {!result && selectedFrameworks && (
        <>
          <div>
            <p className="text-sm font-semibold text-gray-800 mb-1">Métodos de Análise</p>
            <p className="text-xs text-gray-500 mb-3">
              O Mentor CFO aplicará os métodos selecionados como lentes complementares e sintetizará uma recomendação integrada. Mín. 1 · Máx. 4.
            </p>
            <div className="space-y-2">
              {selectedFrameworks.map((fw) => {
                const detail = suggestionDetails.find((d) => d.framework === fw)
                  || availableCatalog.find((c) => c.framework === fw)
                const IconComp = FRAMEWORK_ICONS[fw]
                const complexity = detail?.complexity
                const isIdeal = detail?.recommended_for?.includes(caseData?.decision_type)
                return (
                  <div key={fw} className="flex items-start gap-3 bg-white border border-gray-200 rounded-lg p-3">
                    {IconComp && (
                      <div className="flex-shrink-0 mt-0.5 w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center">
                        <IconComp className="h-4 w-4 text-gray-600" />
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-medium text-gray-800">{detail?.name || FRAMEWORK_LABELS[fw] || fw}</span>
                        {fw === primaryFramework && (
                          <span className="inline-flex items-center gap-1 text-xs bg-brand-100 text-brand-700 px-1.5 py-0.5 rounded font-medium">
                            <Lock className="h-2.5 w-2.5" /> Principal
                          </span>
                        )}
                        {complexity && (
                          <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${COMPLEXITY_COLORS[complexity] || 'bg-gray-100 text-gray-600'}`}>
                            {complexity}
                          </span>
                        )}
                        {isIdeal && (
                          <span className="text-xs bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded font-medium">
                            Ideal para este tipo
                          </span>
                        )}
                      </div>
                      {detail?.description && (
                        <p className="text-xs text-gray-500 mt-1 line-clamp-2">{detail.description}</p>
                      )}
                      {detail?.why_suggested && (
                        <p className="text-xs text-gray-400 mt-0.5 italic">{detail.why_suggested}</p>
                      )}
                    </div>
                    {fw !== primaryFramework && (
                      <button
                        onClick={() => removeFramework(fw)}
                        className="text-gray-300 hover:text-red-400 mt-0.5 flex-shrink-0"
                        title="Remover método"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </div>
                )
              })}
            </div>

            {selectedFrameworks.length < 4 && frameworksNotSelected.length > 0 && (
              <div className="mt-2">
                <button
                  onClick={() => setShowAddMenu(!showAddMenu)}
                  className="flex items-center gap-1.5 text-xs text-brand-700 hover:text-brand-900 font-medium"
                >
                  <Plus className="h-3.5 w-3.5" /> Adicionar método
                </button>
                {showAddMenu && (
                  <div className="mt-2 bg-white border border-gray-200 rounded-lg shadow-lg p-3 space-y-2 max-h-[400px] overflow-y-auto">
                    <p className="text-xs text-gray-500 font-medium mb-1">Selecione um framework adicional ({4 - selectedFrameworks.length} restante{4 - selectedFrameworks.length !== 1 ? 's' : ''})</p>
                    {frameworksNotSelected.map((fw) => {
                      const catEntry = availableCatalog.find((c) => c.framework === fw)
                      const IconComp = FRAMEWORK_ICONS[fw]
                      const pairsWithSelected = catEntry?.pairs_well_with?.some((p) => selectedFrameworks.includes(p))
                      const pairedWith = catEntry?.pairs_well_with?.filter((p) => selectedFrameworks.includes(p)) || []
                      const isRecommended = catEntry?.recommended_for?.includes(caseData?.decision_type)
                      return (
                        <button
                          key={fw}
                          onClick={() => addFramework(fw)}
                          className={`w-full text-left rounded-lg p-3 border transition-colors hover:bg-gray-50 ${pairsWithSelected ? 'border-green-300 bg-green-50/50' : 'border-gray-200'}`}
                        >
                          <div className="flex items-start gap-3">
                            {IconComp && (
                              <div className="flex-shrink-0 mt-0.5 w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center">
                                <IconComp className="h-4 w-4 text-gray-600" />
                              </div>
                            )}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-sm font-medium text-gray-800">{catEntry?.name || FRAMEWORK_LABELS[fw] || fw}</span>
                                {catEntry?.complexity && (
                                  <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${COMPLEXITY_COLORS[catEntry.complexity] || 'bg-gray-100 text-gray-600'}`}>
                                    {catEntry.complexity}
                                  </span>
                                )}
                                {isRecommended && (
                                  <span className="text-xs bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded font-medium">
                                    Recomendado
                                  </span>
                                )}
                              </div>
                              {catEntry?.description && (
                                <p className="text-xs text-gray-500 mt-1 line-clamp-2">{catEntry.description}</p>
                              )}
                              {pairedWith.length > 0 && (
                                <p className="text-xs text-green-600 mt-1 font-medium">
                                  Combina com {pairedWith.map((p) => FRAMEWORK_LABELS[p] || p).join(', ')}
                                </p>
                              )}
                            </div>
                          </div>
                        </button>
                      )
                    })}
                  </div>
                )}
              </div>
            )}
          </div>

          {mut.error && (
            <Alert variant="error" message={mut.error.response?.data?.message || 'Erro na análise.'} />
          )}

          <Btn onClick={() => mut.mutate()} loading={mut.isPending}>
            <Brain className="h-4 w-4" />
            {mut.isPending ? 'Analisando com IA...' : 'Confirmar e Analisar'}
          </Btn>
        </>
      )}

      {result && (
        <div className="space-y-4">
          {result.frameworks_selected?.length > 0 && (
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="text-xs text-gray-500 font-medium">Métodos aplicados:</span>
              {result.frameworks_selected.map((fw) => (
                <span key={fw} className="bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-full text-xs font-medium">
                  {FRAMEWORK_LABELS[fw] || fw}
                </span>
              ))}
            </div>
          )}
          {result.llm_unavailable && (
            <Alert variant="warning" message="LLM indisponível. Análise gerada pelo motor determinístico de fallback." />
          )}
          {result.implicit_assumptions_found?.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm font-semibold text-blue-900 mb-2">
                Premissas Implícitas Identificadas ({result.implicit_assumptions_found.length})
              </p>
              <ul className="space-y-1">
                {result.implicit_assumptions_found.map((a, i) => (
                  <li key={i} className="text-sm text-blue-700 flex gap-2">
                    <span className="text-blue-400 mt-0.5">•</span>{a}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {result.financial_metrics_impacted?.length > 0 && (
            <div>
              <p className="text-sm font-medium text-gray-700 mb-1.5">Métricas Financeiras Impactadas</p>
              <div className="flex flex-wrap gap-2">
                {result.financial_metrics_impacted.map((m) => (
                  <span key={m} className="bg-gray-100 text-gray-700 px-2.5 py-0.5 rounded-full text-xs font-medium">{m}</span>
                ))}
              </div>
            </div>
          )}
          {result.game_theory_model && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <p className="text-sm font-bold text-purple-900 mb-2">Modelo de Teoria dos Jogos</p>
              <p className="text-sm text-purple-700"><strong>Jogadores:</strong> {result.game_theory_model.players?.join(', ')}</p>
              {result.game_theory_model.equilibrium && (
                <p className="text-sm text-purple-700 mt-1"><strong>Equilíbrio:</strong> {result.game_theory_model.equilibrium}</p>
              )}
              <p className="text-sm text-purple-700 mt-1"><strong>Risco Estratégico:</strong> {result.game_theory_model.strategic_risk}</p>
            </div>
          )}
          {result.scenario_summary && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-sm font-bold text-green-900 mb-2">Análise de Cenários</p>
              <p className="text-sm text-green-800 whitespace-pre-wrap">{result.scenario_summary}</p>
            </div>
          )}

          {/* Hypothesis gate: show form before revealing recommendation */}
          {!hypothesisSubmitted && (
            <div className="bg-blue-50 border border-blue-300 rounded-lg p-5 space-y-3">
              <p className="text-sm font-bold text-blue-900">
                Antes de ver a recomendação da IA, registre sua leitura inicial deste caso
              </p>
              <p className="text-xs text-blue-700">
                Com base nos dados acima (premissas implícitas, métricas, cenários), qual seria sua decisão preliminar? Isso ajuda a prevenir viés de ancoragem.
              </p>
              <textarea
                value={hypothesisText}
                onChange={(e) => setHypothesisText(e.target.value)}
                rows={4}
                placeholder="Minha leitura inicial é que... (mínimo 30 caracteres)"
                className="w-full px-3 py-2.5 text-sm border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none bg-white"
              />
              {hypothesisMut.error && (
                <Alert variant="error" message={hypothesisMut.error.response?.data?.message || 'Erro ao registrar hipótese.'} />
              )}
              <Btn
                onClick={() => hypothesisMut.mutate()}
                loading={hypothesisMut.isPending}
                disabled={hypothesisText.length < 30}
              >
                Registrar Hipótese e Ver Recomendação
              </Btn>
            </div>
          )}

          {/* Recommendation revealed after hypothesis */}
          <div
            className="transition-opacity duration-500"
            style={{ opacity: hypothesisSubmitted ? 1 : 0, maxHeight: hypothesisSubmitted ? 'none' : 0, overflow: 'hidden' }}
          >
            {hypothesisSubmitted && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-5">
                <p className="text-sm font-bold text-amber-900 mb-2">Recomendação do Mentor CFO</p>
                <p className="text-sm text-amber-800 whitespace-pre-wrap">{result.recommendation}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Heuristic Alerts ─────────────────────────────────────────────────────────
const SEVERITY_STYLES = {
  high: 'bg-red-50 border-red-200 text-red-800',
  medium: 'bg-amber-50 border-amber-200 text-amber-800',
  low: 'bg-green-50 border-green-200 text-green-700',
}
const SEVERITY_DOT = { high: 'bg-red-500', medium: 'bg-amber-500', low: 'bg-green-500' }

function AlertsPanel({ alerts }) {
  if (!alerts || alerts.length === 0) return null
  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide flex items-center gap-1.5">
        <AlertTriangle className="h-3.5 w-3.5" /> Inteligência Histórica
      </p>
      {alerts.map((a, i) => (
        <div key={i} className={`border rounded-lg p-3 ${SEVERITY_STYLES[a.severity] || SEVERITY_STYLES.low}`}>
          <div className="flex items-start gap-2">
            <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${SEVERITY_DOT[a.severity] || SEVERITY_DOT.low}`} />
            <div className="flex-1 min-w-0">
              <p className="text-sm">{a.message}</p>
              {a.confidence != null && (
                <p className="text-xs opacity-70 mt-0.5">Confiança: {(a.confidence * 100).toFixed(0)}%</p>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

function MiniStat({ label, value }) {
  return (
    <div className="text-center">
      <p className="text-lg font-bold text-indigo-900">{value ?? '—'}</p>
      <p className="text-xs text-indigo-600">{label}</p>
    </div>
  )
}

function BenchmarkPanel({ benchmark }) {
  if (!benchmark || benchmark.total_similar_cases === 0) return null
  return (
    <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 space-y-3">
      <p className="text-xs font-semibold text-indigo-700 uppercase tracking-wide flex items-center gap-1.5">
        <BarChart3 className="h-3.5 w-3.5" /> Benchmark Histórico
      </p>
      {benchmark.messages?.length > 0 && (
        <ul className="space-y-1">
          {benchmark.messages.map((m, i) => (
            <li key={i} className="text-sm text-indigo-800 flex gap-2">
              <span className="text-indigo-400 mt-0.5">•</span>{m}
            </li>
          ))}
        </ul>
      )}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
        <MiniStat label="Casos similares" value={benchmark.total_similar_cases} />
        <MiniStat label="Seguiram recom." value={benchmark.followed_recommendation_pct != null ? `${benchmark.followed_recommendation_pct}%` : null} />
        <MiniStat label="Acurácia média" value={benchmark.avg_forecast_accuracy != null ? `${benchmark.avg_forecast_accuracy}/10` : null} />
        <MiniStat label="Efic. capital" value={benchmark.avg_capital_efficiency != null ? `${benchmark.avg_capital_efficiency}%` : null} />
      </div>
    </div>
  )
}

// ── RECOMMENDED → DECIDED ────────────────────────────────────────────────────
function DecidePanel({ caseId, recommendation }) {
  const qc = useQueryClient()
  const [decision, setDecision] = useState('')
  const [diverge, setDiverge] = useState(false)
  const [justification, setJustification] = useState('')
  const [criteria, setCriteria] = useState([''])
  const [result, setResult] = useState(null)
  const [reanalysisResult, setReanalysisResult] = useState(null)
  const [alertsAcknowledged, setAlertsAcknowledged] = useState(false)
  const [showRubberStampWarning, setShowRubberStampWarning] = useState(false)

  const { data: alertsData, isLoading: alertsLoading, isError: alertsError } = useQuery({
    queryKey: ['heuristic-alerts', caseId],
    queryFn: () => getHeuristicAlerts(caseId),
    staleTime: 60_000,
    retry: false,
  })

  const hasAlerts = alertsData?.alerts?.length > 0
  const alertsResolved = !hasAlerts || alertsAcknowledged || alertsError

  const displayedRecommendation = reanalysisResult?.recommendation ?? recommendation

  const mut = useMutation({
    mutationFn: () => decideCase(caseId, {
      executive_decision: decision,
      divergence_justification: diverge ? justification : null,
      monitoring_criteria: criteria.filter(Boolean).length ? criteria.filter(Boolean) : null,
    }),
    onSuccess: (data) => {
      setResult(data)
      qc.invalidateQueries({ queryKey: ['case', caseId] })
    },
  })

  const reanalyzeMut = useMutation({
    mutationFn: () => reanalyzeCase(caseId),
    onSuccess: (data) => {
      setReanalysisResult(data)
      qc.invalidateQueries({ queryKey: ['case', caseId] })
    },
  })

  const handleDecide = () => {
    if (displayedRecommendation && jaccardSimilarity(decision, displayedRecommendation) > RUBBER_STAMP_THRESHOLD) {
      setShowRubberStampWarning(true)
      return
    }
    mut.mutate()
  }

  return (
    <div className="space-y-5">
      {hasAlerts && <AlertsPanel alerts={alertsData.alerts} />}
      {alertsData?.benchmark && <BenchmarkPanel benchmark={alertsData.benchmark} />}

      {hasAlerts && !alertsAcknowledged && !alertsError && (
        <label className="flex items-start gap-2.5 cursor-pointer bg-amber-50 border border-amber-200 rounded-lg p-3">
          <input
            type="checkbox"
            checked={alertsAcknowledged}
            onChange={(e) => setAlertsAcknowledged(e.target.checked)}
            className="w-4 h-4 mt-0.5 rounded accent-amber-700"
          />
          <span className="text-sm text-amber-800">Li e considerei os alertas históricos acima</span>
        </label>
      )}

      {(recommendation || reanalysisResult) && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-amber-700 uppercase tracking-wide">Recomendação do Mentor CFO</p>
            <button
              onClick={() => reanalyzeMut.mutate()}
              disabled={reanalyzeMut.isPending || !!result}
              className="flex items-center gap-1.5 text-xs text-amber-700 hover:text-amber-900 font-medium disabled:opacity-40"
              title="Re-executar análise com LLM"
            >
              {reanalyzeMut.isPending
                ? <span className="animate-spin inline-block h-3.5 w-3.5 border-2 border-amber-700 border-t-transparent rounded-full" />
                : <RefreshCw className="h-3.5 w-3.5" />}
              {reanalyzeMut.isPending ? 'Analisando...' : 'Reanalisar'}
            </button>
          </div>
          <p className="text-sm text-amber-900">{displayedRecommendation}</p>
          {reanalysisResult && !reanalysisResult.llm_unavailable && (
            <p className="text-xs text-green-700 font-medium">✓ Análise atualizada pela LLM</p>
          )}
          {reanalysisResult?.llm_unavailable && (
            <p className="text-xs text-red-600 font-medium">⚠ LLM ainda indisponível — análise determinística</p>
          )}
        </div>
      )}
      {reanalyzeMut.error && (
        <Alert variant="error" message={reanalyzeMut.error.response?.data?.message || 'Erro ao reanalisar.'} />
      )}

      <Field label="Sua Decisão Executiva" required>
        <textarea
          value={decision}
          onChange={(e) => setDecision(e.target.value)}
          rows={4}
          placeholder="Descreva a decisão tomada (mínimo 10 caracteres)..."
          className="w-full px-3 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-600 resize-none"
        />
      </Field>

      <label className="flex items-center gap-2.5 cursor-pointer">
        <input
          type="checkbox"
          checked={diverge}
          onChange={(e) => setDiverge(e.target.checked)}
          className="w-4 h-4 rounded accent-brand-900"
        />
        <span className="text-sm text-gray-700">Minha decisão diverge da recomendação do Mentor CFO</span>
      </label>

      {diverge && (
        <Field label="Justificativa da Divergência" required>
          <textarea
            value={justification}
            onChange={(e) => setJustification(e.target.value)}
            rows={3}
            placeholder="Por que você está divergindo da recomendação?"
            className="w-full px-3 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-600 resize-none"
          />
        </Field>
      )}

      <Field label="Critérios de Monitoramento (opcional)">
        <div className="space-y-2">
          {criteria.map((c, i) => (
            <div key={i} className="flex gap-2">
              <input
                type="text"
                value={c}
                onChange={(e) => setCriteria((prev) => prev.map((v, j) => j === i ? e.target.value : v))}
                placeholder={`Critério ${i + 1}`}
                className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-600"
              />
              {criteria.length > 1 && (
                <button onClick={() => setCriteria((prev) => prev.filter((_, j) => j !== i))} className="p-2 text-red-400 hover:text-red-600">
                  <Trash2 className="h-4 w-4" />
                </button>
              )}
            </div>
          ))}
          <button onClick={() => setCriteria((prev) => [...prev, ''])} className="flex items-center gap-1.5 text-xs text-brand-700 hover:text-brand-900 font-medium">
            <Plus className="h-3.5 w-3.5" /> Adicionar critério
          </button>
        </div>
      </Field>

      {mut.error && (
        <Alert variant="error" message={mut.error.response?.data?.message || 'Erro ao registrar decisão.'} />
      )}
      {result && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
          <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-green-900">Decisão registrada</p>
            <p className="text-sm text-green-700">{result.divergence_flag ? 'Divergência registrada e justificada.' : 'Alinhada com a recomendação do Mentor.'}</p>
          </div>
        </div>
      )}

      {!result && (
        <>
          {(!alertsResolved || alertsLoading) && !alertsLoading && (
            <p className="text-xs text-amber-600">Confirme que leu os alertas históricos para prosseguir.</p>
          )}
          <Btn
            onClick={handleDecide}
            loading={mut.isPending}
            disabled={!decision || decision.length < 10 || (diverge && !justification) || !alertsResolved || alertsLoading}
          >
            Registrar Decisão
          </Btn>
        </>
      )}

      {showRubberStampWarning && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full mx-4 p-6 space-y-4">
            <h3 className="text-lg font-bold text-gray-900">Verificação de Reflexão</h3>
            <p className="text-sm text-gray-600">
              Sua decisão é muito similar à recomendação da IA. Você considerou cenários alternativos?
            </p>
            <div className="flex gap-3 pt-2">
              <button
                onClick={() => { setShowRubberStampWarning(false); mut.mutate() }}
                className="flex-1 py-2.5 px-4 bg-brand-900 text-white text-sm font-medium rounded-lg hover:bg-brand-800"
              >
                Sim, considerei
              </button>
              <button
                onClick={() => setShowRubberStampWarning(false)}
                className="flex-1 py-2.5 px-4 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50"
              >
                Quero revisar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ── DECIDED ──────────────────────────────────────────────────────────────────
function DecidedPanel({ caseId, executiveDecision, divergenceFlag, setClosedHeuristicsCount }) {
  const [showReview, setShowReview] = useState(false)

  return (
    <div className="space-y-4">
      <div className="bg-green-50 border border-green-200 rounded-lg p-5">
        <p className="text-xs font-semibold text-green-700 uppercase tracking-wide mb-2">Decisão Executiva Registrada</p>
        <p className="text-sm text-green-900">{executiveDecision || '—'}</p>
      </div>
      {divergenceFlag && (
        <Alert variant="warning" message="Esta decisão divergiu da recomendação do Mentor CFO." />
      )}
      {!showReview ? (
        <>
          <Alert variant="info" message="Este caso está pronto para revisão de resultados pós-decisão." />
          <Btn onClick={() => setShowReview(true)}>
            Iniciar Revisão de Resultados
          </Btn>
        </>
      ) : (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <ReviewPanel caseId={caseId} setClosedHeuristicsCount={setClosedHeuristicsCount} />
        </div>
      )}
    </div>
  )
}

// ── DECIDED → UNDER_REVIEW / CLOSED ──────────────────────────────────────────
function ReviewPanel({ caseId, setClosedHeuristicsCount }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({
    outcome_summary: '',
    forecast_accuracy_score: '',
    risk_realization_rate: '',
    capital_allocation_efficiency_score: '',
    divergence_outcome_flag: false,
  })
  const [result, setResult] = useState(null)

  function set(k, v) { setForm((prev) => ({ ...prev, [k]: v })) }

  const mut = useMutation({
    mutationFn: () => reviewCase(caseId, {
      outcome_summary: form.outcome_summary,
      forecast_accuracy_score: form.forecast_accuracy_score ? Number(form.forecast_accuracy_score) : null,
      risk_realization_rate: form.risk_realization_rate ? Number(form.risk_realization_rate) : null,
      capital_allocation_efficiency_score: form.capital_allocation_efficiency_score ? Number(form.capital_allocation_efficiency_score) : null,
      divergence_outcome_flag: form.divergence_outcome_flag || null,
    }),
    onSuccess: (data) => {
      setResult(data)
      if (setClosedHeuristicsCount) setClosedHeuristicsCount(data.heuristics_generated)
      qc.invalidateQueries({ queryKey: ['case', caseId] })
    },
  })

  return (
    <div className="space-y-5">
      <p className="text-sm text-gray-600">
        Registre os resultados reais vs. o previsto. O sistema vai calcular se a divergência foi acertada e extrair heurísticas.
      </p>

      <Field label="Resumo do Resultado" required>
        <textarea
          value={form.outcome_summary}
          onChange={(e) => set('outcome_summary', e.target.value)}
          rows={4}
          placeholder="Descreva o resultado real da decisão (mínimo 20 caracteres)..."
          className="w-full px-3 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-600 resize-none"
        />
      </Field>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Field label="Acurácia do Forecast (1–10)"
          tooltip={"Quão precisa foi a projeção financeira comparada ao resultado real.\n\n1 = projeção totalmente errada\n10 = projeção perfeita\n\n>= 8 gera heurística de alta acurácia\n< 5 com divergência sinaliza outcome negativo"}
        >
          <input type="number" min={1} max={10} value={form.forecast_accuracy_score}
            onChange={(e) => set('forecast_accuracy_score', e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-600"
            placeholder="1–10"
          />
        </Field>
        <Field label="Taxa de Realização de Riscos (%)"
          tooltip={"Percentual dos riscos identificados na estruturação que de fato se materializaram.\n\n0% = nenhum risco se concretizou\n100% = todos os riscos aconteceram\n\n> 50% marca todos os riscos como materializados e gera heurística automática"}
        >
          <input type="number" min={0} max={100} value={form.risk_realization_rate}
            onChange={(e) => set('risk_realization_rate', e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-600"
            placeholder="0–100"
          />
        </Field>
        <Field label="Eficiência de Capital (%)"
          tooltip={"Quão bem o capital alocado foi utilizado em relação ao resultado obtido.\n\n0% = capital desperdiçado\n100% = retorno máximo para o investido\n\n>= 80% gera heurística de eficiência de capital"}
        >
          <input type="number" min={0} max={100} value={form.capital_allocation_efficiency_score}
            onChange={(e) => set('capital_allocation_efficiency_score', e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-600"
            placeholder="0–100"
          />
        </Field>
      </div>

      <label className="flex items-center gap-2.5 cursor-pointer">
        <input type="checkbox" checked={form.divergence_outcome_flag}
          onChange={(e) => set('divergence_outcome_flag', e.target.checked)}
          className="w-4 h-4 rounded accent-brand-900"
        />
        <span className="text-sm text-gray-700">A divergência da recomendação gerou resultado melhor?</span>
      </label>

      {mut.error && (
        <Alert variant="error" message={mut.error.response?.data?.message || 'Erro ao registrar revisão.'} />
      )}
      {result && (
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 flex items-center gap-3">
          <CheckCircle className="h-5 w-5 text-purple-600 flex-shrink-0" />
          <p className="text-sm font-semibold text-purple-900">Caso encerrado com sucesso</p>
        </div>
      )}

      {!result && (
        <Btn
          onClick={() => mut.mutate()}
          loading={mut.isPending}
          disabled={!form.outcome_summary || form.outcome_summary.length < 20}
        >
          Registrar Revisão e Encerrar
        </Btn>
      )}
    </div>
  )
}

// ── MAIN EXPORT ──────────────────────────────────────────────────────────────
export function ActionPanel({ caseData }) {
  const { id, state, recommendation, initial_hypothesis, executive_decision, divergence_flag } = caseData
  const [closedHeuristicsCount, setClosedHeuristicsCount] = useState(null)

  switch (state) {
    case 'DRAFT':
      return (
        <Section title="Classificar Caso" subtitle="Etapa 1 de 6">
          <ClassifyPanel caseId={id} />
        </Section>
      )
    case 'CLASSIFIED':
      return (
        <Section title="Estruturar Caso" subtitle="Etapa 2 de 6">
          <StructurePanel caseId={id} />
        </Section>
      )
    case 'STRUCTURED':
      return (
        <Section title="Analisar com Mentor CFO" subtitle="Etapa 3 de 6">
          <AnalyzePanel caseId={id} caseData={caseData} />
        </Section>
      )
    case 'ANALYZED':
    case 'RECOMMENDED':
      return (
        <Section title="Registrar Decisão Executiva" subtitle="Etapa 4 de 6">
          <DecidePanel caseId={id} recommendation={recommendation} />
        </Section>
      )
    case 'DECIDED':
      return (
        <Section title="Decisão Registrada" subtitle="Etapa 5 de 6 — Revisão de resultados disponível">
          <DecidedPanel caseId={id} executiveDecision={executive_decision} divergenceFlag={divergence_flag} setClosedHeuristicsCount={setClosedHeuristicsCount} />
        </Section>
      )
    case 'UNDER_REVIEW':
    case 'CLOSED':
      return state === 'UNDER_REVIEW' ? (
        <Section title="Revisão de Resultados" subtitle="Etapa 6 de 6">
          <ReviewPanel caseId={id} setClosedHeuristicsCount={setClosedHeuristicsCount} />
        </Section>
      ) : (
        <Section title="Caso Encerrado" subtitle="Histórico completo da decisão">
          <div className="space-y-4">
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 flex items-center gap-3">
              <CheckCircle className="h-5 w-5 text-purple-600 flex-shrink-0" />
              <p className="text-sm text-purple-700">
                {closedHeuristicsCount === null
                  ? "Consulte a aba Heurísticas para ver os padrões aprendidos."
                  : closedHeuristicsCount === 0
                  ? "Nenhum novo padrão foi identificado neste ciclo."
                  : `${closedHeuristicsCount} heurística${closedHeuristicsCount > 1 ? 's' : ''} aprendida${closedHeuristicsCount > 1 ? 's' : ''} neste ciclo.`}
              </p>
            </div>

            {initial_hypothesis && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-5">
                <p className="text-xs font-semibold text-blue-700 uppercase tracking-wide mb-2">Hipótese Inicial do CFO</p>
                <p className="text-sm text-blue-900 whitespace-pre-wrap">{initial_hypothesis}</p>
              </div>
            )}

            {recommendation && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-5">
                <p className="text-sm font-bold text-amber-900 mb-2">Recomendação do Mentor CFO</p>
                <p className="text-sm text-amber-800 whitespace-pre-wrap">{recommendation}</p>
              </div>
            )}

            {executive_decision && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-5">
                <p className="text-xs font-semibold text-green-700 uppercase tracking-wide mb-2">Decisão Executiva Registrada</p>
                <p className="text-sm text-green-900">{executive_decision}</p>
              </div>
            )}

            {divergence_flag && (
              <Alert variant="warning" message="Esta decisão divergiu da recomendação do Mentor CFO." />
            )}
          </div>
        </Section>
      )
    default:
      return null
  }
}

function Section({ title, subtitle, children }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <div className="mb-5">
        <h3 className="font-semibold text-gray-900">{title}</h3>
        {subtitle && <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>}
      </div>
      {children}
    </div>
  )
}
