import { useState, FormEvent, useEffect } from 'react';
import { useRouter } from 'next/router';
import Cookies from 'js-cookie';
import api from '../../lib/api';
import Layout from '../../components/Layout';
import { FinancialDomain, DecisionType } from '../../types';

const DOMAINS: { value: FinancialDomain; label: string }[] = [
  { value: 'CAPEX',           label: 'Capital Expenditure (CapEx)' },
  { value: 'OPEX',            label: 'Operating Expenditure (OpEx)' },
  { value: 'REVENUE',         label: 'Revenue' },
  { value: 'TREASURY',        label: 'Treasury' },
  { value: 'RISK_MANAGEMENT', label: 'Risk Management' },
  { value: 'COMPLIANCE',      label: 'Compliance' },
  { value: 'STRATEGY',        label: 'Strategy' },
  { value: 'M_AND_A',         label: 'Mergers & Acquisitions (M&A)' },
];

const TYPES: { value: DecisionType; label: string }[] = [
  { value: 'INVESTMENT',           label: 'Investment' },
  { value: 'DIVESTMENT',           label: 'Divestment' },
  { value: 'FINANCING',            label: 'Financing' },
  { value: 'OPERATIONAL_CHANGE',   label: 'Operational Change' },
  { value: 'RISK_MITIGATION',      label: 'Risk Mitigation' },
  { value: 'STRATEGIC_PARTNERSHIP',label: 'Strategic Partnership' },
  { value: 'ACQUISITION',          label: 'Acquisition' },
  { value: 'RESTRUCTURING',        label: 'Restructuring' },
];

export default function NewCasePage() {
  const router = useRouter();
  const [form, setForm] = useState({
    title: '',
    description: '',
    financialDomain: 'CAPEX' as FinancialDomain,
    decisionType: 'INVESTMENT' as DecisionType,
    impactScore: 3,
    externalAgentsPresent: false,
    scenarioAnalysisRequired: false,
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!Cookies.get('token')) router.replace('/login');
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await api.post('/financial-decision-cases', form);
      const id = res.data?.id || res.data?.data?.id;
      if (id) {
        router.push(`/cases/${id}`);
      } else {
        router.push('/dashboard');
      }
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const r = (err as { response: { data: { message?: string | string[] } } }).response;
        const msg = r?.data?.message;
        setError(Array.isArray(msg) ? msg.join(', ') : msg || 'Failed to create case.');
      } else {
        setError('Failed to create case. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }

  function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
    return (
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">
          {label} {required && <span className="text-red-500">*</span>}
        </label>
        {children}
      </div>
    );
  }

  const inputCls = "w-full px-3 py-2 border border-slate-300 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent";

  return (
    <Layout>
      <div className="max-w-2xl mx-auto">
        {/* Back link */}
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-slate-500 hover:text-slate-800 text-sm mb-6 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Dashboard
        </button>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="bg-gradient-to-r from-slate-900 to-slate-700 px-6 py-5">
            <h1 className="text-xl font-bold text-white">New Financial Decision Case</h1>
            <p className="text-slate-400 text-sm mt-1">
              Define the parameters of the decision to be analyzed
            </p>
          </div>

          {error && (
            <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="p-6 space-y-5">
            <Field label="Case Title" required>
              <input
                type="text"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                required
                maxLength={200}
                placeholder="e.g. Acquisition of XYZ Corp – Strategic Fit Assessment"
                className={inputCls}
              />
            </Field>

            <Field label="Description" required>
              <textarea
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                required
                rows={4}
                placeholder="Provide a detailed description of the decision context..."
                className={inputCls}
              />
            </Field>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <Field label="Financial Domain" required>
                <select
                  value={form.financialDomain}
                  onChange={(e) => setForm({ ...form, financialDomain: e.target.value as FinancialDomain })}
                  className={inputCls}
                >
                  {DOMAINS.map((d) => (
                    <option key={d.value} value={d.value}>{d.label}</option>
                  ))}
                </select>
              </Field>

              <Field label="Decision Type" required>
                <select
                  value={form.decisionType}
                  onChange={(e) => setForm({ ...form, decisionType: e.target.value as DecisionType })}
                  className={inputCls}
                >
                  {TYPES.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </Field>
            </div>

            <Field label="Impact Score (1 = Low, 5 = Critical)" required>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min={1}
                  max={5}
                  value={form.impactScore}
                  onChange={(e) => setForm({ ...form, impactScore: Number(e.target.value) })}
                  className="w-full accent-blue-600"
                />
                <span className={`text-sm font-bold w-8 text-center px-1 py-0.5 rounded ${
                  form.impactScore >= 4 ? 'text-red-700 bg-red-100' :
                  form.impactScore === 3 ? 'text-yellow-700 bg-yellow-100' :
                  'text-green-700 bg-green-100'
                }`}>
                  {form.impactScore}
                </span>
              </div>
              <div className="flex justify-between text-xs text-slate-400 mt-1">
                <span>Low</span><span>Moderate</span><span>Critical</span>
              </div>
            </Field>

            <div className="space-y-3 bg-slate-50 rounded-xl p-4">
              <p className="text-sm font-medium text-slate-700">Additional Options</p>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.externalAgentsPresent}
                  onChange={(e) => setForm({ ...form, externalAgentsPresent: e.target.checked })}
                  className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
                />
                <div>
                  <p className="text-sm font-medium text-slate-700">External Agents Present</p>
                  <p className="text-xs text-slate-500">Competitors, regulators, or third parties are involved</p>
                </div>
              </label>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.scenarioAnalysisRequired}
                  onChange={(e) => setForm({ ...form, scenarioAnalysisRequired: e.target.checked })}
                  className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
                />
                <div>
                  <p className="text-sm font-medium text-slate-700">Scenario Analysis Required</p>
                  <p className="text-xs text-slate-500">Multiple scenarios (base, bear, bull) should be modeled</p>
                </div>
              </label>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => router.back()}
                className="px-4 py-2 text-slate-600 hover:text-slate-800 font-medium text-sm transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold rounded-lg text-sm transition-colors shadow-sm"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                    </svg>
                    Creating…
                  </span>
                ) : 'Create Case'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Layout>
  );
}
