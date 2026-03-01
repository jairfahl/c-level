import { GameTheoryAnalysis } from '../types';

interface GameTheoryPanelProps {
  analysis: GameTheoryAnalysis;
}

export default function GameTheoryPanel({ analysis }: GameTheoryPanelProps) {
  return (
    <div className="bg-slate-900 rounded-xl p-5 text-white space-y-5">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <div>
          <h4 className="font-semibold text-white">Game Theory Analysis</h4>
          <p className="text-xs text-slate-400">Strategic interaction modeling</p>
        </div>
      </div>

      {/* Players */}
      {analysis.players && analysis.players.length > 0 && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Players</p>
          <div className="flex flex-wrap gap-2">
            {analysis.players.map((player, i) => (
              <span key={i} className="px-3 py-1 bg-blue-600/30 border border-blue-500/40 text-blue-300 rounded-full text-sm">
                {player}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Strategy Space */}
      {analysis.strategySpace && Object.keys(analysis.strategySpace).length > 0 && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Strategy Space</p>
          <div className="space-y-2">
            {Object.entries(analysis.strategySpace).map(([player, strategies]) => (
              <div key={player} className="flex items-start gap-2">
                <span className="text-sm font-medium text-blue-300 min-w-[120px]">{player}:</span>
                <div className="flex flex-wrap gap-1">
                  {(Array.isArray(strategies) ? strategies : [strategies]).map((s, i) => (
                    <span key={i} className="px-2 py-0.5 bg-slate-700 text-slate-300 rounded text-xs">
                      {String(s)}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Payoff Matrix */}
      {analysis.payoffMatrix && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Payoff Matrix</p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <tbody>
                {typeof analysis.payoffMatrix === 'object' &&
                  Object.entries(analysis.payoffMatrix as Record<string, unknown>).map(([key, value]) => (
                    <tr key={key} className="border-b border-slate-700">
                      <td className="py-1.5 pr-4 text-slate-400 font-medium whitespace-nowrap">{key}</td>
                      <td className="py-1.5 text-slate-200">
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Equilibrium */}
      {analysis.equilibriumEstimation && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Equilibrium Estimation</p>
          <div className="bg-slate-800 rounded-lg p-3 border border-slate-600">
            <p className="text-sm text-slate-200">{analysis.equilibriumEstimation}</p>
          </div>
        </div>
      )}

      {/* Strategic Risk */}
      {analysis.strategicRiskExposure && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Strategic Risk Exposure</p>
          <div className="flex items-start gap-2 bg-red-900/30 border border-red-700/40 rounded-lg p-3">
            <svg className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <p className="text-sm text-red-300">{analysis.strategicRiskExposure}</p>
          </div>
        </div>
      )}
    </div>
  );
}
