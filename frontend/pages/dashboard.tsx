import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Cookies from 'js-cookie';
import api from '../lib/api';
import Layout from '../components/Layout';
import StateBadge from '../components/StateBadge';
import { FinancialDecisionCase, DecisionState } from '../types';

const DOMAIN_LABELS: Record<string, string> = {
  CAPEX: 'CapEx',
  OPEX: 'OpEx',
  REVENUE: 'Revenue',
  TREASURY: 'Treasury',
  RISK_MANAGEMENT: 'Risk Mgmt',
  COMPLIANCE: 'Compliance',
  STRATEGY: 'Strategy',
  M_AND_A: 'M&A',
};

const TYPE_LABELS: Record<string, string> = {
  INVESTMENT: 'Investment',
  DIVESTMENT: 'Divestment',
  FINANCING: 'Financing',
  OPERATIONAL_CHANGE: 'Op. Change',
  RISK_MITIGATION: 'Risk Mitigation',
  STRATEGIC_PARTNERSHIP: 'Strategic Partnership',
  ACQUISITION: 'Acquisition',
  RESTRUCTURING: 'Restructuring',
};

const STATE_ORDER: DecisionState[] = [
  'DRAFT', 'CLASSIFIED', 'STRUCTURED', 'ANALYZED',
  'RECOMMENDED', 'DECIDED', 'UNDER_REVIEW', 'CLOSED',
];

export default function DashboardPage() {
  const router = useRouter();
  const [cases, setCases] = useState<FinancialDecisionCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = Cookies.get('token');
    if (!token) {
      void router.replace('/login');
      return;
    }
    void fetchCases();
  }, [router]);

  const fetchCases = useCallback(async () => {
    try {
      const res = await api.get('/financial-decision-cases');
      setCases(res.data?.data || res.data || []);
    } catch {
      setError('Failed to load cases. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  const stateCounts = STATE_ORDER.reduce((acc, s) => {
    acc[s] = cases.filter((c) => c.state === s).length;
    return acc;
  }, {} as Record<DecisionState, number>);

  const impactColors = ['', 'bg-green-100 text-green-700', 'bg-lime-100 text-lime-700',
    'bg-yellow-100 text-yellow-700', 'bg-orange-100 text-orange-700', 'bg-red-100 text-red-700'];

  return (
    <Layout>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Financial Decision Cases</h1>
          <p className="text-slate-500 text-sm mt-0.5">
            {cases.length} total case{cases.length !== 1 ? 's' : ''} across all states
          </p>
        </div>
        <Link
          href="/cases/new"
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg text-sm transition-colors shadow-sm"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Case
        </Link>
      </div>

      {/* State summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 mb-6">
        {STATE_ORDER.map((state) => (
          <div key={state} className="bg-white rounded-lg border border-slate-200 p-3 text-center shadow-sm">
            <p className="text-2xl font-bold text-slate-800">{stateCounts[state]}</p>
            <StateBadge state={state} size="sm" />
          </div>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
      )}

      {/* Loading */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <svg className="animate-spin h-8 w-8 text-blue-600" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
          </svg>
        </div>
      ) : cases.length === 0 ? (
        <div className="text-center py-20">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
            </svg>
          </div>
          <p className="text-slate-500 font-medium">No decision cases yet</p>
          <p className="text-slate-400 text-sm mt-1">Create your first financial decision case to get started.</p>
          <Link
            href="/cases/new"
            className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg text-sm transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create First Case
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {cases.map((c) => (
            <Link
              key={c.id}
              href={`/cases/${c.id}`}
              className="bg-white rounded-xl border border-slate-200 p-5 hover:border-blue-300 hover:shadow-md transition-all group"
            >
              <div className="flex items-start justify-between gap-2 mb-3">
                <h3 className="font-semibold text-slate-800 group-hover:text-blue-700 leading-snug line-clamp-2">
                  {c.title}
                </h3>
                <StateBadge state={c.state} size="sm" />
              </div>

              <p className="text-sm text-slate-500 line-clamp-2 mb-3">{c.description}</p>

              <div className="flex flex-wrap gap-2 mb-3">
                <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 bg-slate-100 text-slate-600 rounded">
                  <span className="font-medium">Domain:</span> {DOMAIN_LABELS[c.financialDomain] || c.financialDomain}
                </span>
                <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 bg-slate-100 text-slate-600 rounded">
                  <span className="font-medium">Type:</span> {TYPE_LABELS[c.decisionType] || c.decisionType}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500">Impact:</span>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded ${impactColors[c.impactScore] || 'bg-slate-100 text-slate-600'}`}>
                    {c.impactScore}/5
                  </span>
                </div>
                <time className="text-xs text-slate-400">
                  {new Date(c.createdAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                </time>
              </div>

              {(c.externalAgentsPresent || c.gameTheoryTriggered) && (
                <div className="mt-3 pt-3 border-t border-slate-100 flex gap-2">
                  {c.externalAgentsPresent && (
                    <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-600 border border-blue-200 rounded">
                      External Agents
                    </span>
                  )}
                  {c.gameTheoryTriggered && (
                    <span className="text-xs px-2 py-0.5 bg-purple-50 text-purple-600 border border-purple-200 rounded">
                      Game Theory
                    </span>
                  )}
                </div>
              )}
            </Link>
          ))}
        </div>
      )}
    </Layout>
  );
}
