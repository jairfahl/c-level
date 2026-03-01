import { DecisionState } from '../types';

const STATES: { state: DecisionState; label: string; short: string }[] = [
  { state: 'DRAFT',        label: 'Draft',        short: 'Draft' },
  { state: 'CLASSIFIED',   label: 'Classified',   short: 'Classified' },
  { state: 'STRUCTURED',   label: 'Structured',   short: 'Structured' },
  { state: 'ANALYZED',     label: 'Analyzed',     short: 'Analyzed' },
  { state: 'RECOMMENDED',  label: 'Recommended',  short: 'Recommend' },
  { state: 'DECIDED',      label: 'Decided',      short: 'Decided' },
  { state: 'UNDER_REVIEW', label: 'Under Review', short: 'Review' },
  { state: 'CLOSED',       label: 'Closed',       short: 'Closed' },
];

interface StateStepperProps {
  currentState: DecisionState;
}

export default function StateStepper({ currentState }: StateStepperProps) {
  const currentIndex = STATES.findIndex((s) => s.state === currentState);

  return (
    <div className="w-full overflow-x-auto">
      <div className="flex items-center min-w-max">
        {STATES.map((step, index) => {
          const isPast      = index < currentIndex;
          const isCurrent   = index === currentIndex;
          const isFuture    = index > currentIndex;

          return (
            <div key={step.state} className="flex items-center">
              {/* Step node */}
              <div className="flex flex-col items-center">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-all ${
                    isCurrent
                      ? 'bg-blue-600 border-blue-600 text-white shadow-lg shadow-blue-200'
                      : isPast
                      ? 'bg-slate-700 border-slate-700 text-white'
                      : 'bg-white border-slate-300 text-slate-400'
                  }`}
                >
                  {isPast ? (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    index + 1
                  )}
                </div>
                <span
                  className={`mt-1 text-xs font-medium whitespace-nowrap ${
                    isCurrent ? 'text-blue-600' : isPast ? 'text-slate-600' : 'text-slate-400'
                  }`}
                >
                  {step.short}
                </span>
              </div>

              {/* Connector line */}
              {index < STATES.length - 1 && (
                <div
                  className={`h-0.5 w-8 mx-1 mt-[-10px] transition-all ${
                    isPast ? 'bg-slate-700' : 'bg-slate-200'
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
