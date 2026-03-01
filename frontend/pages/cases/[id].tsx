import { useEffect, useState, FormEvent } from 'react';
import { useRouter } from 'next/router';
import Cookies from 'js-cookie';
import api from '../../lib/api';
import Layout from '../../components/Layout';
import StateBadge from '../../components/StateBadge';
import StateStepper from '../../components/StateStepper';
import PyramidRecommendation from '../../components/PyramidRecommendation';
import GameTheoryPanel from '../../components/GameTheoryPanel';
import AuditTimeline from '../../components/AuditTimeline';
import {
  FinancialDecisionCase,
  DecisionState,
  FinancialAssumption,
  FinancialRisk,
  FinancialMetricImpacted,
} from '../../types';

type Tab = 'overview' | 'assumptions' | 'analysis' | 'recommendation' | 'decision' | 'review' | 'audit';

const TABS: { id: Tab; label: string }[] = [
  { id: 'overview',       label: 'Overview' },
  { id: 'assumptions',    label: 'Assumptions & Risks' },
  { id: 'analysis',       label: 'Analysis' },
  { id: 'recommendation', label: 'Recommendation' },
  { id: 'decision',       label: 'Decision' },
  { id: 'review',         label: 'Review' },
  { id: 'audit',          label: 'Audit Trail' },
];

const DOMAIN_LABELS: Record<string, string> = {
  CAPEX: 'Capital Expenditure',
  OPEX: 'Operating Expenditure',
  REVENUE: 'Revenue',
  TREASURY: 'Treasury',
  RISK_MANAGEMENT: 'Risk Management',
  COMPLIANCE: 'Compliance',
  STRATEGY: 'Strategy',
  M_AND_A: 'Mergers & Acquisitions',
};

const TYPE_LABELS: Record<string, string> = {
  INVESTMENT: 'Investment',
  DIVESTMENT: 'Divestment',
  FINANCING: 'Financing',
  OPERATIONAL_CHANGE: 'Operational Change',
  RISK_MITIGATION: 'Risk Mitigation',
  STRATEGIC_PARTNERSHIP: 'Strategic Partnership',
  ACQUISITION: 'Acquisition',
  RESTRUCTURING: 'Restructuring',
};

function inputCls(extra = '') {
  return `w-full px-3 py-2 border border-slate-300 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${extra}`;
}

function SectionCard({ title, children }: { title?: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
      {title && <h3 className="text-base font-semibold text-slate-800 mb-4">{title}</h3>}
      {children}
    </div>
  );
}

// ─── Assumption Form ─────────────────────────────────────────────────────────
function AddAssumptionForm({ caseId, onAdded }: { caseId: string; onAdded: () => void }) {
  const [form, setForm] = useState({ description: '', source: '', confidence: 0.8 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await api.post(`/financial-decision-cases/${caseId}/assumptions`, form);
      setForm({ description: '', source: '', confidence: 0.8 });
      onAdded();
    } catch (err: unknown) {
      setError(extractMessage(err) || 'Failed to add assumption.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-blue-50 border border-blue-200 rounded-xl p-4 space-y-3">
      <p className="text-sm font-semibold text-blue-800">Add Assumption</p>
      {error && <p className="text-xs text-red-600">{error}</p>}
      <div>
        <label className="block text-xs font-medium text-slate-600 mb-1">Description *</label>
        <textarea
          required
          rows={2}
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          placeholder="Describe the assumption..."
          className={inputCls()}
        />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">Source *</label>
          <input
            required
            type="text"
            value={form.source}
            onChange={(e) => setForm({ ...form, source: e.target.value })}
            placeholder="e.g. Bloomberg, Internal"
            className={inputCls()}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">
            Confidence ({Math.round(form.confidence * 100)}%)
          </label>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={form.confidence}
            onChange={(e) => setForm({ ...form, confidence: Number(e.target.value) })}
            className="w-full accent-blue-600 mt-1"
          />
        </div>
      </div>
      <button type="submit" disabled={loading}
        className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-sm font-medium rounded-lg transition-colors">
        {loading ? 'Adding…' : 'Add Assumption'}
      </button>
    </form>
  );
}

// ─── Risk Form ────────────────────────────────────────────────────────────────
function AddRiskForm({ caseId, onAdded }: { caseId: string; onAdded: () => void }) {
  const [form, setForm] = useState({ description: '', probability: 0.5, impactScore: 3, mitigationPlan: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await api.post(`/financial-decision-cases/${caseId}/risks`, form);
      setForm({ description: '', probability: 0.5, impactScore: 3, mitigationPlan: '' });
      onAdded();
    } catch (err: unknown) {
      setError(extractMessage(err) || 'Failed to add risk.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-orange-50 border border-orange-200 rounded-xl p-4 space-y-3">
      <p className="text-sm font-semibold text-orange-800">Add Risk</p>
      {error && <p className="text-xs text-red-600">{error}</p>}
      <div>
        <label className="block text-xs font-medium text-slate-600 mb-1">Description *</label>
        <textarea
          required
          rows={2}
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          placeholder="Describe the risk..."
          className={inputCls()}
        />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">
            Probability ({Math.round(form.probability * 100)}%)
          </label>
          <input type="range" min={0} max={1} step={0.05}
            value={form.probability}
            onChange={(e) => setForm({ ...form, probability: Number(e.target.value) })}
            className="w-full accent-orange-500 mt-1" />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">Impact Score (1–5)</label>
          <input type="range" min={1} max={5} step={1}
            value={form.impactScore}
            onChange={(e) => setForm({ ...form, impactScore: Number(e.target.value) })}
            className="w-full accent-red-500 mt-1" />
          <p className="text-xs text-slate-500 text-center">{form.impactScore}</p>
        </div>
      </div>
      <div>
        <label className="block text-xs font-medium text-slate-600 mb-1">Mitigation Plan</label>
        <textarea
          rows={2}
          value={form.mitigationPlan}
          onChange={(e) => setForm({ ...form, mitigationPlan: e.target.value })}
          placeholder="Describe mitigation strategy (optional)..."
          className={inputCls()}
        />
      </div>
      <button type="submit" disabled={loading}
        className="px-4 py-1.5 bg-orange-600 hover:bg-orange-700 disabled:bg-orange-400 text-white text-sm font-medium rounded-lg transition-colors">
        {loading ? 'Adding…' : 'Add Risk'}
      </button>
    </form>
  );
}

// ─── Metric Form ──────────────────────────────────────────────────────────────
function AddMetricForm({ caseId, onAdded }: { caseId: string; onAdded: () => void }) {
  const [form, setForm] = useState({ metricName: '', currentValue: '', projectedValue: '', unit: '', timeHorizonMonths: 12 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await api.post(`/financial-decision-cases/${caseId}/metrics`, {
        ...form,
        currentValue: Number(form.currentValue),
        projectedValue: Number(form.projectedValue),
      });
      setForm({ metricName: '', currentValue: '', projectedValue: '', unit: '', timeHorizonMonths: 12 });
      onAdded();
    } catch (err: unknown) {
      setError(extractMessage(err) || 'Failed to add metric.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 space-y-3">
      <p className="text-sm font-semibold text-yellow-800">Add Financial Metric</p>
      {error && <p className="text-xs text-red-600">{error}</p>}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">Metric Name *</label>
          <input required type="text" value={form.metricName}
            onChange={(e) => setForm({ ...form, metricName: e.target.value })}
            placeholder="e.g. EBITDA, Revenue" className={inputCls()} />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">Unit *</label>
          <input required type="text" value={form.unit}
            onChange={(e) => setForm({ ...form, unit: e.target.value })}
            placeholder="e.g. USD M, %" className={inputCls()} />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">Current Value *</label>
          <input required type="number" step="any" value={form.currentValue}
            onChange={(e) => setForm({ ...form, currentValue: e.target.value })}
            placeholder="Current" className={inputCls()} />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">Projected Value *</label>
          <input required type="number" step="any" value={form.projectedValue}
            onChange={(e) => setForm({ ...form, projectedValue: e.target.value })}
            placeholder="Projected" className={inputCls()} />
        </div>
        <div className="col-span-2">
          <label className="block text-xs font-medium text-slate-600 mb-1">Time Horizon (months): {form.timeHorizonMonths}</label>
          <input type="range" min={1} max={120} value={form.timeHorizonMonths}
            onChange={(e) => setForm({ ...form, timeHorizonMonths: Number(e.target.value) })}
            className="w-full accent-yellow-600" />
          <div className="flex justify-between text-xs text-slate-400 mt-1"><span>1m</span><span>5y</span><span>10y</span></div>
        </div>
      </div>
      <button type="submit" disabled={loading}
        className="px-4 py-1.5 bg-yellow-600 hover:bg-yellow-700 disabled:bg-yellow-400 text-white text-sm font-medium rounded-lg transition-colors">
        {loading ? 'Adding…' : 'Add Metric'}
      </button>
    </form>
  );
}

// ─── Utilities ────────────────────────────────────────────────────────────────
function extractMessage(err: unknown): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const r = (err as { response: { data: { message?: string | string[] } } }).response;
    const msg = r?.data?.message;
    return Array.isArray(msg) ? msg.join(', ') : msg || '';
  }
  return '';
}

const IMPACT_COLORS = ['', 'text-green-700 bg-green-100', 'text-lime-700 bg-lime-100',
  'text-yellow-700 bg-yellow-100', 'text-orange-700 bg-orange-100', 'text-red-700 bg-red-100'];

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function CaseDetailPage() {
  const router = useRouter();
  const { id } = router.query;

  const [caseData, setCaseData] = useState<FinancialDecisionCase | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionError, setActionError] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>('overview');

  // Classify form state
  const [classifyForm, setClassifyForm] = useState({ classification: '', rationale: '' });
  const [showClassifyForm, setShowClassifyForm] = useState(false);

  // Decision form state
  const [decisionForm, setDecisionForm] = useState({ executiveDecision: '', divergenceJustification: '' });

  // Review form state
  const [reviewForm, setReviewForm] = useState({ actualOutcome: '', varianceAnalysis: '', lessonsLearned: '' });

  useEffect(() => {
    if (!Cookies.get('token')) {
      router.replace('/login');
      return;
    }
    if (id) fetchCase();
  }, [id]);

  async function fetchCase() {
    setLoading(true);
    try {
      const res = await api.get(`/financial-decision-cases/${id}`);
      setCaseData(res.data?.data || res.data);
    } catch {
      setError('Failed to load case.');
    } finally {
      setLoading(false);
    }
  }

  async function performAction(endpoint: string, method: 'post' | 'patch' = 'post', body?: unknown) {
    setActionError('');
    setActionLoading(true);
    try {
      await api[method](endpoint, body || {});
      await fetchCase();
    } catch (err: unknown) {
      const msg = extractMessage(err);
      const status = err && typeof err === 'object' && 'response' in err
        ? (err as { response: { status: number } }).response?.status
        : 0;
      if (status === 409) {
        setActionError(`Protocol violation: ${msg || 'This transition is not allowed in the current state.'}`);
      } else if (status === 422) {
        setActionError(`Validation error: ${msg || 'Requirements not met for this transition.'}`);
      } else {
        setActionError(msg || 'Action failed. Please try again.');
      }
    } finally {
      setActionLoading(false);
    }
  }

  // ── Action Handlers ──────────────────────────────────────────────────────
  async function handleClassify(e: FormEvent) {
    e.preventDefault();
    await performAction(`/financial-decision-cases/${id}/classify`, 'post', classifyForm);
    setShowClassifyForm(false);
  }

  async function handleStructure() {
    await performAction(`/financial-decision-cases/${id}/structure`);
    setActiveTab('assumptions');
  }

  async function handleAnalyze() {
    await performAction(`/financial-decision-cases/${id}/analyze`);
    setActiveTab('analysis');
  }

  async function handleRecommend() {
    await performAction(`/financial-decision-cases/${id}/recommend`);
    setActiveTab('recommendation');
  }

  async function handleDecision(e: FormEvent) {
    e.preventDefault();
    await performAction(`/financial-decision-cases/${id}/decide`, 'post', decisionForm);
  }

  async function handleSubmitReview(e: FormEvent) {
    e.preventDefault();
    await performAction(`/financial-decision-cases/${id}/review`, 'post', reviewForm);
  }

  async function handleCloseCase() {
    await performAction(`/financial-decision-cases/${id}/close`);
  }

  // ── Requirements Check ───────────────────────────────────────────────────
  function getStructureRequirements(): string[] {
    const missing: string[] = [];
    if (!caseData) return missing;
    const assumptions = caseData.assumptions || [];
    const risks = caseData.risks || [];
    if (assumptions.length < 3) missing.push(`At least 3 assumptions required (have ${assumptions.length})`);
    if (risks.length < 1) missing.push('At least 1 risk is required');
    return missing;
  }

  function getAnalyzeRequirements(): string[] {
    const missing: string[] = [];
    if (!caseData) return missing;
    const metrics = caseData.metricsImpacted || [];
    if (metrics.length < 1) missing.push('At least 1 financial metric is required');
    return missing;
  }

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center py-32">
          <svg className="animate-spin h-10 w-10 text-blue-600" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
          </svg>
        </div>
      </Layout>
    );
  }

  if (error || !caseData) {
    return (
      <Layout>
        <div className="max-w-xl mx-auto text-center py-20">
          <p className="text-red-600 font-medium">{error || 'Case not found.'}</p>
          <button onClick={() => router.back()} className="mt-4 text-blue-600 hover:underline text-sm">← Go back</button>
        </div>
      </Layout>
    );
  }

  const state = caseData.state;
  const latestDecision = caseData.decisions?.[caseData.decisions.length - 1];
  const latestReview = caseData.reviews?.[caseData.reviews.length - 1];
  const structureMissing = getStructureRequirements();
  const analyzeMissing = getAnalyzeRequirements();

  return (
    <Layout>
      {/* Back */}
      <button
        onClick={() => router.push('/dashboard')}
        className="flex items-center gap-2 text-slate-500 hover:text-slate-800 text-sm mb-4 transition-colors"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to Dashboard
      </button>

      {/* Case Header */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden mb-5">
        <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-700 px-6 py-5">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-2 flex-wrap">
                <StateBadge state={state} size="lg" />
                {caseData.gameTheoryTriggered && (
                  <span className="text-xs px-2 py-0.5 bg-purple-900/60 text-purple-300 border border-purple-600/50 rounded">
                    Game Theory Active
                  </span>
                )}
                {caseData.externalAgentsPresent && (
                  <span className="text-xs px-2 py-0.5 bg-blue-900/60 text-blue-300 border border-blue-600/50 rounded">
                    External Agents
                  </span>
                )}
              </div>
              <h1 className="text-xl font-bold text-white leading-snug">{caseData.title}</h1>
              <div className="flex flex-wrap gap-4 mt-2 text-sm text-slate-400">
                <span>{DOMAIN_LABELS[caseData.financialDomain] || caseData.financialDomain}</span>
                <span>·</span>
                <span>{TYPE_LABELS[caseData.decisionType] || caseData.decisionType}</span>
                <span>·</span>
                <span>Created {new Date(caseData.createdAt).toLocaleDateString()}</span>
              </div>
            </div>
            <div className="text-right flex-shrink-0">
              <div className={`text-2xl font-bold px-3 py-1 rounded-lg ${IMPACT_COLORS[caseData.impactScore] || 'text-white bg-slate-600'}`}>
                {caseData.impactScore}/5
              </div>
              <p className="text-xs text-slate-400 mt-1">Impact Score</p>
            </div>
          </div>
        </div>

        {/* State Stepper */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200">
          <StateStepper currentState={state} />
        </div>
      </div>

      {/* Action Error */}
      {actionError && (
        <div className="mb-4 p-4 bg-red-50 border-l-4 border-red-500 rounded-lg flex items-start gap-3">
          <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <p className="font-semibold text-red-800 text-sm">Action Failed</p>
            <p className="text-red-700 text-sm">{actionError}</p>
          </div>
          <button onClick={() => setActionError('')} className="ml-auto text-red-400 hover:text-red-600">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* State Action Panel */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 mb-5">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-1.5 h-6 bg-blue-600 rounded-full"></div>
          <h2 className="font-semibold text-slate-800">Current State Actions</h2>
        </div>

        {state === 'DRAFT' && (
          <div className="space-y-3">
            <p className="text-sm text-slate-600">
              This case is in <strong>Draft</strong>. Classify it to begin the structured decision process.
            </p>
            {!showClassifyForm ? (
              <button
                onClick={() => setShowClassifyForm(true)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition-colors"
              >
                Classify Case →
              </button>
            ) : (
              <form onSubmit={handleClassify} className="bg-slate-50 rounded-xl p-4 space-y-3 border border-slate-200">
                <p className="text-sm font-semibold text-slate-700">Classify this Case</p>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Classification Label *</label>
                  <input
                    required type="text"
                    value={classifyForm.classification}
                    onChange={(e) => setClassifyForm({ ...classifyForm, classification: e.target.value })}
                    placeholder="e.g. HIGH_PRIORITY, STRATEGIC, ROUTINE"
                    className={inputCls()}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Rationale *</label>
                  <textarea
                    required rows={2}
                    value={classifyForm.rationale}
                    onChange={(e) => setClassifyForm({ ...classifyForm, rationale: e.target.value })}
                    placeholder="Why is this classification appropriate?"
                    className={inputCls()}
                  />
                </div>
                <div className="flex gap-2">
                  <button type="submit" disabled={actionLoading}
                    className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-sm font-medium rounded-lg transition-colors">
                    {actionLoading ? 'Classifying…' : 'Submit Classification'}
                  </button>
                  <button type="button" onClick={() => setShowClassifyForm(false)}
                    className="px-4 py-1.5 text-slate-600 hover:text-slate-800 text-sm font-medium transition-colors">
                    Cancel
                  </button>
                </div>
              </form>
            )}
          </div>
        )}

        {state === 'CLASSIFIED' && (
          <div className="space-y-3">
            <p className="text-sm text-slate-600">
              Case is <strong>Classified</strong>. Add at least 3 assumptions and 1 risk, then structure the case.
            </p>
            {structureMissing.length > 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                <p className="text-xs font-semibold text-amber-800 mb-1">Requirements not yet met:</p>
                <ul className="list-disc list-inside text-xs text-amber-700 space-y-0.5">
                  {structureMissing.map((m, i) => <li key={i}>{m}</li>)}
                </ul>
              </div>
            )}
            <div className="flex gap-2">
              <button
                onClick={() => setActiveTab('assumptions')}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg transition-colors"
              >
                Go to Assumptions & Risks
              </button>
              <button
                onClick={handleStructure}
                disabled={structureMissing.length > 0 || actionLoading}
                className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 disabled:bg-slate-300 disabled:text-slate-500 text-white text-sm font-semibold rounded-lg transition-colors"
              >
                {actionLoading ? 'Structuring…' : 'Structure Case →'}
              </button>
            </div>
          </div>
        )}

        {state === 'STRUCTURED' && (
          <div className="space-y-3">
            <p className="text-sm text-slate-600">
              Case is <strong>Structured</strong>. Add financial metrics, then run the analysis.
            </p>
            {analyzeMissing.length > 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                <p className="text-xs font-semibold text-amber-800 mb-1">Requirements not yet met:</p>
                <ul className="list-disc list-inside text-xs text-amber-700 space-y-0.5">
                  {analyzeMissing.map((m, i) => <li key={i}>{m}</li>)}
                </ul>
              </div>
            )}
            <div className="flex gap-2">
              <button
                onClick={() => setActiveTab('analysis')}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg transition-colors"
              >
                Go to Analysis
              </button>
              <button
                onClick={handleAnalyze}
                disabled={analyzeMissing.length > 0 || actionLoading}
                className="px-4 py-2 bg-orange-600 hover:bg-orange-700 disabled:bg-slate-300 disabled:text-slate-500 text-white text-sm font-semibold rounded-lg transition-colors"
              >
                {actionLoading ? 'Analyzing…' : 'Run Analysis →'}
              </button>
            </div>
          </div>
        )}

        {state === 'ANALYZED' && (
          <div className="space-y-3">
            <p className="text-sm text-slate-600">
              Analysis complete. Generate the <strong>AI-powered recommendation</strong> using Pyramid Principle structuring.
            </p>
            <button
              onClick={handleRecommend}
              disabled={actionLoading}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-300 text-white text-sm font-semibold rounded-lg transition-colors"
            >
              {actionLoading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                  </svg>
                  Generating Recommendation…
                </span>
              ) : 'Generate Recommendation →'}
            </button>
          </div>
        )}

        {state === 'RECOMMENDED' && (
          <div className="space-y-3">
            <p className="text-sm text-slate-600">
              Recommendation ready. Review it and record the <strong>executive decision</strong>.
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setActiveTab('recommendation')}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg transition-colors"
              >
                View Recommendation
              </button>
              <button
                onClick={() => setActiveTab('decision')}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-semibold rounded-lg transition-colors"
              >
                Record Decision →
              </button>
            </div>
          </div>
        )}

        {state === 'DECIDED' && (
          <div className="space-y-3">
            <p className="text-sm text-slate-600">
              Decision recorded. Submit this case for <strong>outcome review</strong>.
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setActiveTab('review')}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white text-sm font-semibold rounded-lg transition-colors"
              >
                Submit for Review →
              </button>
            </div>
          </div>
        )}

        {state === 'UNDER_REVIEW' && (
          <div className="space-y-3">
            <p className="text-sm text-slate-600">
              This case is <strong>Under Review</strong>. Complete the outcome review to close the case.
            </p>
            <div className="flex gap-2">
              <button onClick={() => setActiveTab('review')}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg transition-colors">
                Complete Review
              </button>
              <button onClick={handleCloseCase} disabled={actionLoading}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-800 text-white text-sm font-semibold rounded-lg transition-colors">
                {actionLoading ? 'Closing…' : 'Close Case'}
              </button>
            </div>
          </div>
        )}

        {state === 'CLOSED' && (
          <div className="flex items-center gap-3 bg-slate-50 rounded-xl p-4 border border-slate-200">
            <div className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <p className="font-semibold text-slate-800 text-sm">Case Closed</p>
              <p className="text-xs text-slate-500">This decision case has been completed and archived.</p>
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="flex overflow-x-auto border-b border-slate-200">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-5 py-3.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-600 text-blue-700 bg-blue-50/50'
                  : 'border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="p-6">
          {/* ── OVERVIEW ─────────────────────────────────────── */}
          {activeTab === 'overview' && (
            <div className="space-y-4">
              <SectionCard title="Case Details">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div><p className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Description</p>
                    <p className="text-slate-700 leading-relaxed">{caseData.description}</p></div>
                  <div className="space-y-3">
                    <div><p className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Domain</p>
                      <p className="text-slate-700">{DOMAIN_LABELS[caseData.financialDomain]}</p></div>
                    <div><p className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Decision Type</p>
                      <p className="text-slate-700">{TYPE_LABELS[caseData.decisionType]}</p></div>
                    <div><p className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Scenario Analysis</p>
                      <p className="text-slate-700">{caseData.scenarioAnalysisRequired ? 'Required' : 'Not required'}</p></div>
                    <div><p className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">External Agents</p>
                      <p className="text-slate-700">{caseData.externalAgentsPresent ? 'Yes' : 'No'}</p></div>
                    <div><p className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Last Updated</p>
                      <p className="text-slate-700">{new Date(caseData.updatedAt).toLocaleString()}</p></div>
                  </div>
                </div>
              </SectionCard>

              {/* State Transitions Summary */}
              {(caseData.stateTransitions || []).length > 0 && (
                <SectionCard title="State History">
                  <div className="space-y-2">
                    {[...(caseData.stateTransitions || [])].reverse().slice(0, 5).map((t) => (
                      <div key={t.id} className="flex items-center gap-3 text-sm">
                        <StateBadge state={t.fromState} size="sm" />
                        <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                        </svg>
                        <StateBadge state={t.toState} size="sm" />
                        <span className="text-slate-400 text-xs ml-auto">
                          {new Date(t.transitionedAt).toLocaleString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </SectionCard>
              )}
            </div>
          )}

          {/* ── ASSUMPTIONS & RISKS ──────────────────────────── */}
          {activeTab === 'assumptions' && (
            <div className="space-y-5">
              {/* Assumptions */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-slate-800">
                    Assumptions
                    <span className="ml-2 text-xs px-2 py-0.5 bg-slate-100 text-slate-600 rounded-full">
                      {(caseData.assumptions || []).length}
                    </span>
                    {(caseData.assumptions || []).length < 3 && (
                      <span className="ml-2 text-xs text-amber-600 font-medium">
                        (min. 3 required)
                      </span>
                    )}
                  </h3>
                </div>
                {(caseData.assumptions || []).length === 0 ? (
                  <p className="text-sm text-slate-400 italic">No assumptions added yet.</p>
                ) : (
                  <div className="space-y-2">
                    {caseData.assumptions!.map((a: FinancialAssumption) => (
                      <div key={a.id} className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                        <p className="text-sm text-slate-800 font-medium">{a.description}</p>
                        <div className="flex items-center gap-4 mt-1.5 text-xs text-slate-500">
                          <span>Source: <strong className="text-slate-600">{a.source}</strong></span>
                          <span>Confidence: <strong className="text-blue-600">{Math.round(a.confidence * 100)}%</strong></span>
                          {a.validatedAt && <span>Validated: {new Date(a.validatedAt).toLocaleDateString()}</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {(state === 'CLASSIFIED' || state === 'STRUCTURED') && (
                  <div className="mt-3">
                    <AddAssumptionForm caseId={caseData.id} onAdded={fetchCase} />
                  </div>
                )}
              </div>

              {/* Risks */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-slate-800">
                    Risks
                    <span className="ml-2 text-xs px-2 py-0.5 bg-slate-100 text-slate-600 rounded-full">
                      {(caseData.risks || []).length}
                    </span>
                  </h3>
                </div>
                {(caseData.risks || []).length === 0 ? (
                  <p className="text-sm text-slate-400 italic">No risks identified yet.</p>
                ) : (
                  <div className="space-y-2">
                    {caseData.risks!.map((r: FinancialRisk) => (
                      <div key={r.id} className="bg-red-50 border border-red-100 rounded-lg p-3">
                        <p className="text-sm text-slate-800 font-medium">{r.description}</p>
                        <div className="flex flex-wrap items-center gap-4 mt-1.5 text-xs text-slate-500">
                          <span>Probability: <strong className="text-orange-600">{Math.round(r.probability * 100)}%</strong></span>
                          <span>Impact: <strong className="text-red-600">{r.impactScore}/5</strong></span>
                          {r.residualRisk !== undefined && (
                            <span>Residual Risk: <strong>{r.residualRisk}</strong></span>
                          )}
                        </div>
                        {r.mitigationPlan && (
                          <p className="text-xs text-slate-600 mt-1.5 bg-white rounded p-2 border border-red-100">
                            <span className="font-medium">Mitigation:</span> {r.mitigationPlan}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
                {(state === 'CLASSIFIED' || state === 'STRUCTURED') && (
                  <div className="mt-3">
                    <AddRiskForm caseId={caseData.id} onAdded={fetchCase} />
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── ANALYSIS ─────────────────────────────────────── */}
          {activeTab === 'analysis' && (
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-slate-800">
                    Financial Metrics Impacted
                    <span className="ml-2 text-xs px-2 py-0.5 bg-slate-100 text-slate-600 rounded-full">
                      {(caseData.metricsImpacted || []).length}
                    </span>
                  </h3>
                </div>
                {(caseData.metricsImpacted || []).length === 0 ? (
                  <p className="text-sm text-slate-400 italic">No metrics added yet.</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm border-collapse">
                      <thead>
                        <tr className="bg-slate-50 border-y border-slate-200">
                          <th className="text-left px-3 py-2 text-xs font-semibold text-slate-600">Metric</th>
                          <th className="text-right px-3 py-2 text-xs font-semibold text-slate-600">Current</th>
                          <th className="text-right px-3 py-2 text-xs font-semibold text-slate-600">Projected</th>
                          <th className="text-right px-3 py-2 text-xs font-semibold text-slate-600">Change</th>
                          <th className="text-center px-3 py-2 text-xs font-semibold text-slate-600">Horizon</th>
                        </tr>
                      </thead>
                      <tbody>
                        {caseData.metricsImpacted!.map((m: FinancialMetricImpacted) => {
                          const pct = m.currentValue !== 0
                            ? ((m.projectedValue - m.currentValue) / Math.abs(m.currentValue)) * 100
                            : 0;
                          const isPositive = pct >= 0;
                          return (
                            <tr key={m.id} className="border-b border-slate-100 hover:bg-slate-50">
                              <td className="px-3 py-2.5 font-medium text-slate-800">{m.metricName}</td>
                              <td className="px-3 py-2.5 text-right text-slate-600">
                                {m.currentValue.toLocaleString()} {m.unit}
                              </td>
                              <td className="px-3 py-2.5 text-right text-slate-800 font-medium">
                                {m.projectedValue.toLocaleString()} {m.unit}
                              </td>
                              <td className={`px-3 py-2.5 text-right font-semibold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                                {isPositive ? '+' : ''}{pct.toFixed(1)}%
                              </td>
                              <td className="px-3 py-2.5 text-center text-slate-500">
                                {m.timeHorizonMonths}m
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
                {(state === 'STRUCTURED' || state === 'ANALYZED') && (
                  <div className="mt-4">
                    <AddMetricForm caseId={caseData.id} onAdded={fetchCase} />
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── RECOMMENDATION ───────────────────────────────── */}
          {activeTab === 'recommendation' && (
            <div>
              {!latestDecision ? (
                <div className="text-center py-12">
                  <div className="w-14 h-14 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <svg className="w-7 h-7 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                        d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                  <p className="text-slate-600 font-medium">No recommendation generated yet.</p>
                  {state === 'ANALYZED' && (
                    <button onClick={handleRecommend} disabled={actionLoading}
                      className="mt-3 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium rounded-lg transition-colors">
                      {actionLoading ? 'Generating…' : 'Generate Recommendation'}
                    </button>
                  )}
                </div>
              ) : (
                <div className="space-y-5">
                  <PyramidRecommendation decision={latestDecision} />
                  {caseData.gameTheoryTriggered && latestDecision.gameTheoryAnalysis && (
                    <GameTheoryPanel analysis={latestDecision.gameTheoryAnalysis} />
                  )}
                </div>
              )}
            </div>
          )}

          {/* ── DECISION ─────────────────────────────────────── */}
          {activeTab === 'decision' && (
            <div className="space-y-5">
              {state === 'RECOMMENDED' && !latestDecision?.executiveDecision ? (
                <div>
                  <h3 className="font-semibold text-slate-800 mb-4">Record Executive Decision</h3>
                  {latestDecision && (
                    <div className="mb-4 p-4 bg-purple-50 border border-purple-200 rounded-xl">
                      <p className="text-xs font-semibold uppercase tracking-wider text-purple-600 mb-1">AI Recommendation</p>
                      <p className="text-sm font-medium text-slate-800">{latestDecision.recommendedOption}</p>
                    </div>
                  )}
                  <form onSubmit={handleDecision} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        Executive Decision *
                      </label>
                      <textarea
                        required rows={4}
                        value={decisionForm.executiveDecision}
                        onChange={(e) => setDecisionForm({ ...decisionForm, executiveDecision: e.target.value })}
                        placeholder="State the executive's final decision..."
                        className={inputCls()}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        Divergence Justification
                        <span className="ml-1 text-xs text-slate-400">(required only if decision differs from recommendation)</span>
                      </label>
                      <textarea rows={3}
                        value={decisionForm.divergenceJustification}
                        onChange={(e) => setDecisionForm({ ...decisionForm, divergenceJustification: e.target.value })}
                        placeholder="If diverging from the recommendation, explain why..."
                        className={inputCls()}
                      />
                    </div>
                    <button type="submit" disabled={actionLoading}
                      className="px-6 py-2.5 bg-green-600 hover:bg-green-700 disabled:bg-slate-300 text-white text-sm font-semibold rounded-lg transition-colors">
                      {actionLoading ? 'Recording…' : 'Record Decision'}
                    </button>
                  </form>
                </div>
              ) : latestDecision ? (
                <div className="space-y-4">
                  <SectionCard title="Executive Decision">
                    <div className="space-y-3">
                      <div>
                        <p className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">AI Recommendation</p>
                        <p className="text-sm text-slate-700">{latestDecision.recommendedOption}</p>
                      </div>
                      {latestDecision.executiveDecision && (
                        <div>
                          <p className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Executive Decision</p>
                          <p className="text-sm text-slate-800 font-medium">{latestDecision.executiveDecision}</p>
                        </div>
                      )}
                      {latestDecision.decidedAt && (
                        <div>
                          <p className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Decided At</p>
                          <p className="text-sm text-slate-700">{new Date(latestDecision.decidedAt).toLocaleString()}</p>
                        </div>
                      )}
                      {latestDecision.divergenceFlag && (
                        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                          <p className="text-xs font-semibold text-amber-800 uppercase tracking-wide mb-1">
                            ⚠ Divergence from AI Recommendation
                          </p>
                          <p className="text-sm text-amber-700">
                            {latestDecision.divergenceJustification || 'No justification provided.'}
                          </p>
                        </div>
                      )}
                    </div>
                  </SectionCard>
                </div>
              ) : (
                <p className="text-sm text-slate-400 italic text-center py-8">
                  No decision has been recorded yet.
                </p>
              )}
            </div>
          )}

          {/* ── REVIEW ───────────────────────────────────────── */}
          {activeTab === 'review' && (
            <div className="space-y-5">
              {(state === 'DECIDED' || state === 'UNDER_REVIEW') && !latestReview ? (
                <div>
                  <h3 className="font-semibold text-slate-800 mb-4">Outcome Review</h3>
                  <form onSubmit={handleSubmitReview} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Actual Outcome *</label>
                      <textarea required rows={3}
                        value={reviewForm.actualOutcome}
                        onChange={(e) => setReviewForm({ ...reviewForm, actualOutcome: e.target.value })}
                        placeholder="Describe what actually happened as a result of this decision..."
                        className={inputCls()}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Variance Analysis *</label>
                      <textarea required rows={3}
                        value={reviewForm.varianceAnalysis}
                        onChange={(e) => setReviewForm({ ...reviewForm, varianceAnalysis: e.target.value })}
                        placeholder="How did the actual outcome vary from projected metrics?"
                        className={inputCls()}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Lessons Learned *</label>
                      <textarea required rows={3}
                        value={reviewForm.lessonsLearned}
                        onChange={(e) => setReviewForm({ ...reviewForm, lessonsLearned: e.target.value })}
                        placeholder="Key lessons for future decision-making..."
                        className={inputCls()}
                      />
                    </div>
                    <button type="submit" disabled={actionLoading}
                      className="px-6 py-2.5 bg-amber-600 hover:bg-amber-700 disabled:bg-slate-300 text-white text-sm font-semibold rounded-lg transition-colors">
                      {actionLoading ? 'Submitting…' : 'Submit Review'}
                    </button>
                  </form>
                </div>
              ) : latestReview ? (
                <SectionCard title="Outcome Review">
                  <div className="space-y-4">
                    <div>
                      <p className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Actual Outcome</p>
                      <p className="text-sm text-slate-700 leading-relaxed">{latestReview.actualOutcome}</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Variance Analysis</p>
                      <p className="text-sm text-slate-700 leading-relaxed">{latestReview.varianceAnalysis}</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Lessons Learned</p>
                      <p className="text-sm text-slate-700 leading-relaxed">{latestReview.lessonsLearned}</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Reviewed At</p>
                      <p className="text-sm text-slate-600">{new Date(latestReview.reviewedAt).toLocaleString()}</p>
                    </div>
                  </div>
                </SectionCard>
              ) : (
                <p className="text-sm text-slate-400 italic text-center py-8">
                  Review is not yet available. Complete the decision first.
                </p>
              )}
            </div>
          )}

          {/* ── AUDIT TRAIL ──────────────────────────────────── */}
          {activeTab === 'audit' && (
            <div>
              <h3 className="font-semibold text-slate-800 mb-4">Audit Trail</h3>
              <AuditTimeline
                auditLogs={caseData.auditLogs}
                stateTransitions={caseData.stateTransitions}
              />
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
