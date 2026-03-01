import { Decision } from '../types';

interface PyramidRecommendationProps {
  decision: Decision;
}

export default function PyramidRecommendation({ decision }: PyramidRecommendationProps) {
  // Parse the recommendation text into pyramid layers
  const lines = (decision.recommendation || '')
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean);

  // Attempt structured parsing: look for numbered points or bullet points
  const keyPoints: string[] = [];
  const supportingEvidence: string[] = [];
  let mainThesis = decision.recommendedOption || '';

  lines.forEach((line) => {
    const bulletMatch = /^[-•*]\s+(.+)/.exec(line);
    const numberedMatch = /^\d+[.)]\s+(.+)/.exec(line);
    const evidenceMatch = /^(evidence|data|supporting|analysis|result):/i.exec(line);

    if (evidenceMatch) {
      supportingEvidence.push(line.replace(/^[^:]+:\s*/i, ''));
    } else if (bulletMatch || numberedMatch) {
      const text = (bulletMatch || numberedMatch)![1];
      if (keyPoints.length < 3) {
        keyPoints.push(text);
      } else {
        supportingEvidence.push(text);
      }
    }
  });

  // Fallback: split recommendation into sentences if no structured bullets
  if (keyPoints.length === 0 && lines.length > 0) {
    const sentences = decision.recommendation
      .split(/[.!?]+/)
      .map((s) => s.trim())
      .filter((s) => s.length > 15);

    if (!mainThesis && sentences.length > 0) {
      mainThesis = sentences[0];
    }
    sentences.slice(1, 4).forEach((s) => keyPoints.push(s));
    sentences.slice(4).forEach((s) => supportingEvidence.push(s));
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-1 h-8 bg-purple-500 rounded-full"></div>
        <div>
          <h3 className="font-semibold text-slate-800">Pyramid Principle Analysis</h3>
          <p className="text-xs text-slate-500">Structured from executive summary down to supporting evidence</p>
        </div>
      </div>

      {/* Level 1 — Executive Answer (Top of Pyramid) */}
      <div className="relative">
        <div className="mx-auto bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl p-5 text-white shadow-lg">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
              </svg>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-white/70 mb-1">
                RECOMMENDATION — So What?
              </p>
              <p className="text-lg font-bold leading-snug">
                {mainThesis || 'No recommended option specified.'}
              </p>
            </div>
          </div>
        </div>
        {/* Pyramid triangle visual indicator */}
        <div className="flex justify-center mt-1">
          <div className="w-0 h-0 border-l-8 border-r-8 border-t-8 border-l-transparent border-r-transparent border-t-purple-200"></div>
        </div>
      </div>

      {/* Level 2 — Key Reasoning Points */}
      <div className="relative">
        <div className="bg-purple-50 border border-purple-200 rounded-xl p-5">
          <p className="text-xs font-semibold uppercase tracking-widest text-purple-500 mb-3">
            KEY REASONING — Why?
          </p>
          {keyPoints.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {keyPoints.slice(0, 3).map((point, i) => (
                <div key={i} className="flex items-start gap-2 bg-white rounded-lg p-3 border border-purple-100">
                  <div className="w-6 h-6 bg-purple-600 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                    {i + 1}
                  </div>
                  <p className="text-sm text-slate-700 leading-relaxed">{point}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500 italic">
              Full recommendation text available in the details below.
            </p>
          )}
        </div>
        <div className="flex justify-center mt-1">
          <div className="w-0 h-0 border-l-8 border-r-8 border-t-8 border-l-transparent border-r-transparent border-t-purple-100"></div>
        </div>
      </div>

      {/* Level 3 — Supporting Evidence */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-5">
        <p className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-3">
          SUPPORTING EVIDENCE — How do we know?
        </p>
        {supportingEvidence.length > 0 ? (
          <ul className="space-y-2">
            {supportingEvidence.map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                <svg className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
                {item}
              </li>
            ))}
          </ul>
        ) : (
          <div className="prose prose-sm text-slate-600 max-w-none">
            <p className="whitespace-pre-wrap text-sm leading-relaxed">{decision.recommendation}</p>
          </div>
        )}
      </div>

      {/* Divergence warning */}
      {decision.divergenceFlag && (
        <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-300 rounded-xl">
          <svg className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div>
            <p className="font-semibold text-amber-800 text-sm">Executive Divergence Detected</p>
            <p className="text-amber-700 text-sm mt-0.5">
              {decision.divergenceJustification || 'The executive decision diverges from the AI recommendation.'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
