import { AlertCircle, CheckCircle, Info, XCircle } from 'lucide-react'

const VARIANTS = {
  error:   { bg: 'bg-red-50 border-red-200',    text: 'text-red-800',   icon: XCircle,       iconColor: 'text-red-500' },
  success: { bg: 'bg-green-50 border-green-200', text: 'text-green-800', icon: CheckCircle,   iconColor: 'text-green-500' },
  warning: { bg: 'bg-yellow-50 border-yellow-200', text: 'text-yellow-800', icon: AlertCircle, iconColor: 'text-yellow-500' },
  info:    { bg: 'bg-blue-50 border-blue-200',   text: 'text-blue-800',  icon: Info,          iconColor: 'text-blue-500' },
}

export function Alert({ variant = 'info', message, className = '' }) {
  if (!message) return null
  const { bg, text, icon: Icon, iconColor } = VARIANTS[variant]
  return (
    <div className={`flex gap-3 p-4 rounded-lg border ${bg} ${className}`}>
      <Icon className={`h-5 w-5 flex-shrink-0 mt-0.5 ${iconColor}`} />
      <p className={`text-sm ${text}`}>{message}</p>
    </div>
  )
}
