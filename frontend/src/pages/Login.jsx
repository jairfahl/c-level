import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../lib/api'
import { setToken, setUser } from '../lib/auth'
import { Spinner } from '../components/ui/Spinner'
import { Alert } from '../components/ui/Alert'

export default function Login() {
  const [username, setUsername] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    if (!username.trim()) return
    setLoading(true)
    setError('')
    try {
      const data = await login(username.trim())
      setToken(data.access_token)
      setUser(username.trim())
      navigate('/')
    } catch {
      setError('Não foi possível conectar à API. Verifique se o backend está rodando.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-900 to-brand-700 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Card */}
        <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="bg-brand-900 px-8 py-10 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-white/10 rounded-2xl mb-4">
              <span className="text-white font-bold text-2xl">CFO</span>
            </div>
            <h1 className="text-white text-2xl font-bold">Mentor C-Level</h1>
            <p className="text-white/60 text-sm mt-1">Governança Cognitiva de Decisões Financeiras</p>
          </div>

          {/* Form */}
          <div className="px-8 py-8">
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Seu nome
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Ex: João Silva"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-600 focus:border-transparent transition"
                  autoFocus
                  disabled={loading}
                />
              </div>

              {error && <Alert variant="error" message={error} />}

              <button
                type="submit"
                disabled={loading || !username.trim()}
                className="w-full flex items-center justify-center gap-2 bg-brand-900 hover:bg-brand-800 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-3 px-4 rounded-lg transition-colors"
              >
                {loading ? <Spinner size="sm" /> : null}
                {loading ? 'Entrando...' : 'Entrar'}
              </button>
            </form>

            <p className="text-center text-xs text-gray-400 mt-6">
              Qualquer nome é aceito — sistema de demonstração
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
