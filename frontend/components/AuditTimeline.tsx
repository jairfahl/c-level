import { AuditLog, StateTransition } from '../types';

type TimelineEvent =
  | { type: 'audit'; data: AuditLog }
  | { type: 'transition'; data: StateTransition };

interface AuditTimelineProps {
  auditLogs?: AuditLog[];
  stateTransitions?: StateTransition[];
}

export default function AuditTimeline({ auditLogs = [], stateTransitions = [] }: AuditTimelineProps) {
  const events: TimelineEvent[] = [
    ...auditLogs.map((l) => ({ type: 'audit' as const, data: l })),
    ...stateTransitions.map((t) => ({ type: 'transition' as const, data: t })),
  ].sort((a, b) => {
    const aTime = a.type === 'audit' ? a.data.performedAt : a.data.transitionedAt;
    const bTime = b.type === 'audit' ? b.data.performedAt : b.data.transitionedAt;
    return new Date(bTime).getTime() - new Date(aTime).getTime();
  });

  if (events.length === 0) {
    return (
      <div className="text-center py-8 text-slate-400 text-sm">
        No audit events recorded yet.
      </div>
    );
  }

  return (
    <div className="flow-root">
      <ul className="-mb-8">
        {events.map((event, idx) => {
          const isLast = idx === events.length - 1;
          const isTransition = event.type === 'transition';
          const timestamp = isTransition
            ? (event.data as StateTransition).transitionedAt
            : (event.data as AuditLog).performedAt;

          return (
            <li key={isTransition ? (event.data as StateTransition).id : (event.data as AuditLog).id}>
              <div className="relative pb-8">
                {!isLast && (
                  <span className="absolute top-5 left-5 -ml-px h-full w-0.5 bg-slate-200" aria-hidden="true" />
                )}
                <div className="relative flex items-start space-x-3">
                  {/* Icon */}
                  <div className={`relative flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full ring-8 ring-white ${
                    isTransition ? 'bg-blue-600' : 'bg-slate-700'
                  }`}>
                    {isTransition ? (
                      <svg className="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M13 9l3 3m0 0l-3 3m3-3H8m13 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    ) : (
                      <svg className="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                      </svg>
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0 bg-white rounded-lg border border-slate-100 p-3 shadow-sm">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        {isTransition ? (
                          <div>
                            <p className="text-sm font-medium text-slate-800">
                              State Transition
                            </p>
                            <p className="text-sm text-slate-600 mt-0.5">
                              <span className="font-medium text-slate-700">{(event.data as StateTransition).fromState}</span>
                              <span className="mx-2 text-slate-400">→</span>
                              <span className="font-medium text-blue-700">{(event.data as StateTransition).toState}</span>
                            </p>
                            {(event.data as StateTransition).reason && (
                              <p className="text-xs text-slate-500 mt-1 italic">
                                {(event.data as StateTransition).reason}
                              </p>
                            )}
                          </div>
                        ) : (
                          <div>
                            <p className="text-sm font-medium text-slate-800">
                              {(event.data as AuditLog).action}
                            </p>
                            {(event.data as AuditLog).metadata && (
                              <p className="text-xs text-slate-500 mt-1 font-mono bg-slate-50 rounded p-1">
                                {JSON.stringify((event.data as AuditLog).metadata, null, 2)}
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                      <time className="text-xs text-slate-400 whitespace-nowrap flex-shrink-0">
                        {new Date(timestamp).toLocaleString()}
                      </time>
                    </div>
                  </div>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
