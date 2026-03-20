const STATE_COLORS = {
  DRAFT:        'bg-gray-100 text-gray-700 border-gray-200',
  CLASSIFIED:   'bg-blue-100 text-blue-700 border-blue-200',
  STRUCTURED:   'bg-indigo-100 text-indigo-700 border-indigo-200',
  ANALYZED:     'bg-yellow-100 text-yellow-700 border-yellow-200',
  RECOMMENDED:  'bg-amber-100 text-amber-700 border-amber-200',
  DECIDED:      'bg-green-100 text-green-700 border-green-200',
  UNDER_REVIEW: 'bg-orange-100 text-orange-700 border-orange-200',
  CLOSED:       'bg-purple-100 text-purple-700 border-purple-200',
}

const STATE_LABELS = {
  DRAFT:        'Rascunho',
  CLASSIFIED:   'Classificado',
  STRUCTURED:   'Estruturado',
  ANALYZED:     'Analisado',
  RECOMMENDED:  'Recomendado',
  DECIDED:      'Decidido',
  UNDER_REVIEW: 'Em Revisão',
  CLOSED:       'Encerrado',
}

export function StateBadge({ state }) {
  const color = STATE_COLORS[state] || 'bg-gray-100 text-gray-600'
  const label = STATE_LABELS[state] || state
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${color}`}>
      {label}
    </span>
  )
}

export function Badge({ children, color = 'gray' }) {
  const colors = {
    gray:   'bg-gray-100 text-gray-700',
    blue:   'bg-blue-100 text-blue-700',
    green:  'bg-green-100 text-green-700',
    red:    'bg-red-100 text-red-700',
    yellow: 'bg-yellow-100 text-yellow-700',
    purple: 'bg-purple-100 text-purple-700',
  }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colors[color] || colors.gray}`}>
      {children}
    </span>
  )
}
