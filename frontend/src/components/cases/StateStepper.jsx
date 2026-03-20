import { Check } from 'lucide-react'

const STATES = [
  { key: 'DRAFT',        label: 'Rascunho' },
  { key: 'CLASSIFIED',   label: 'Classificado' },
  { key: 'STRUCTURED',   label: 'Estruturado' },
  { key: 'ANALYZED',     label: 'Analisado' },
  { key: 'RECOMMENDED',  label: 'Recomendado' },
  { key: 'DECIDED',      label: 'Decidido' },
  { key: 'UNDER_REVIEW', label: 'Em Revisão' },
  { key: 'CLOSED',       label: 'Encerrado' },
]

const ORDER = STATES.map((s) => s.key)

export function StateStepper({ currentState }) {
  const currentIdx = ORDER.indexOf(currentState)

  return (
    <div className="w-full overflow-x-auto">
      <div className="flex items-center min-w-max px-1">
        {STATES.map((step, idx) => {
          const done = idx < currentIdx
          const active = idx === currentIdx
          return (
            <div key={step.key} className="flex items-center">
              {/* Node */}
              <div className="flex flex-col items-center">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                    done
                      ? 'bg-brand-900 text-white'
                      : active
                      ? 'bg-blue-600 text-white ring-4 ring-blue-100'
                      : 'bg-gray-200 text-gray-400'
                  }`}
                >
                  {done ? <Check className="h-4 w-4" /> : <span>{idx + 1}</span>}
                </div>
                <span
                  className={`mt-1.5 text-xs font-medium whitespace-nowrap ${
                    active ? 'text-blue-600' : done ? 'text-brand-900' : 'text-gray-400'
                  }`}
                >
                  {step.label}
                </span>
              </div>
              {/* Connector */}
              {idx < STATES.length - 1 && (
                <div
                  className={`h-0.5 w-10 mx-1 mb-5 transition-colors ${
                    idx < currentIdx ? 'bg-brand-900' : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
