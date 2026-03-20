import { NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Brain, FileText, Settings, LogOut, ShieldAlert } from 'lucide-react'
import { clearAuth, getUser } from '../../lib/auth'

const NAV = [
  { to: '/',            label: 'Dashboard',    icon: LayoutDashboard },
  { to: '/heuristics',  label: 'Heurísticas',  icon: Brain },
  { to: '/knowledge-base', label: 'Conhecimento', icon: FileText },
  { to: '/admin',       label: 'Admin',         icon: ShieldAlert },
]

export function Sidebar() {
  const navigate = useNavigate()
  const user = getUser()

  function handleLogout() {
    clearAuth()
    navigate('/login')
  }

  return (
    <aside className="w-56 flex-shrink-0 bg-brand-900 flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="px-5 py-6 border-b border-white/10">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-white/10 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">CFO</span>
          </div>
          <div>
            <p className="text-white font-semibold text-sm leading-tight">Mentor</p>
            <p className="text-white/50 text-xs">C-Level</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-white/15 text-white'
                  : 'text-white/60 hover:bg-white/10 hover:text-white'
              }`
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* User + Logout */}
      <div className="px-3 py-4 border-t border-white/10">
        <div className="flex items-center gap-3 px-3 py-2 mb-1">
          <div className="w-7 h-7 rounded-full bg-white/20 flex items-center justify-center">
            <span className="text-white text-xs font-bold uppercase">{user?.[0] || 'U'}</span>
          </div>
          <span className="text-white/70 text-sm truncate">{user || 'Usuário'}</span>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-white/60 hover:bg-white/10 hover:text-white transition-colors"
        >
          <LogOut className="h-4 w-4" />
          Sair
        </button>
      </div>
    </aside>
  )
}
