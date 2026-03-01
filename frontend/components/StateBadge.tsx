import { DecisionState } from '../types';

const STATE_CONFIG: Record<DecisionState, { label: string; classes: string }> = {
  DRAFT:         { label: 'Draft',          classes: 'bg-slate-100 text-slate-600 border border-slate-300' },
  CLASSIFIED:    { label: 'Classified',     classes: 'bg-blue-100 text-blue-700 border border-blue-300' },
  STRUCTURED:    { label: 'Structured',     classes: 'bg-yellow-100 text-yellow-700 border border-yellow-300' },
  ANALYZED:      { label: 'Analyzed',       classes: 'bg-orange-100 text-orange-700 border border-orange-300' },
  RECOMMENDED:   { label: 'Recommended',    classes: 'bg-purple-100 text-purple-700 border border-purple-300' },
  DECIDED:       { label: 'Decided',        classes: 'bg-green-100 text-green-700 border border-green-300' },
  UNDER_REVIEW:  { label: 'Under Review',   classes: 'bg-amber-100 text-amber-700 border border-amber-300' },
  CLOSED:        { label: 'Closed',         classes: 'bg-slate-200 text-slate-500 border border-slate-400' },
};

interface StateBadgeProps {
  state: DecisionState;
  size?: 'sm' | 'md' | 'lg';
}

export default function StateBadge({ state, size = 'md' }: StateBadgeProps) {
  const config = STATE_CONFIG[state] ?? { label: state, classes: 'bg-gray-100 text-gray-600 border border-gray-300' };

  const sizeClasses = {
    sm:  'text-xs px-2 py-0.5 rounded',
    md:  'text-xs px-2.5 py-1 rounded-md',
    lg:  'text-sm px-3 py-1 rounded-md font-semibold',
  }[size];

  return (
    <span className={`inline-flex items-center font-medium ${sizeClasses} ${config.classes}`}>
      {config.label}
    </span>
  );
}
