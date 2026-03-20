import { useQuery } from '@tanstack/react-query'
import { getTransitions } from '../../lib/api'
import { PageSpinner } from '../ui/Spinner'
import { ArrowRight, Clock } from 'lucide-react'

const STATE_LABELS = {
  DRAFT: 'Rascunho', CLASSIFIED: 'Classificado', STRUCTURED: 'Estruturado',
  ANALYZED: 'Analisado', RECOMMENDED: 'Recomendado', DECIDED: 'Decidido',
  UNDER_REVIEW: 'Em Revisão', CLOSED: 'Encerrado',
}

function fmt(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export function AuditTrail({ caseId }) {
  const { data, isLoading } = useQuery({
    queryKey: ['transitions', caseId],
    queryFn: () => getTransitions(caseId),
    enabled: !!caseId,
  })

  if (isLoading) return <PageSpinner />

  const transitions = data?.transitions || []

  if (transitions.length === 0) {
    return <p className="text-sm text-gray-400 py-4">Nenhuma transição registrada.</p>
  }

  return (
    <div className="space-y-3">
      {transitions.map((t) => (
        <div key={t.id} className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg border border-gray-100">
          <div className="flex-shrink-0 w-8 h-8 bg-brand-900 rounded-full flex items-center justify-center">
            <Clock className="h-4 w-4 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-medium text-gray-700">
                {t.from_state ? STATE_LABELS[t.from_state] || t.from_state : 'Criação'}
              </span>
              {t.from_state && (
                <>
                  <ArrowRight className="h-3.5 w-3.5 text-gray-400" />
                  <span className="text-sm font-semibold text-brand-900">
                    {STATE_LABELS[t.to_state] || t.to_state}
                  </span>
                </>
              )}
            </div>
            <p className="text-xs text-gray-400 mt-0.5">
              {fmt(t.transitioned_at)}
              {t.triggered_by ? ` · por ${t.triggered_by}` : ''}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}
