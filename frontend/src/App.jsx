import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { isAuthenticated } from './lib/auth'

import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import CaseDetail from './pages/CaseDetail'
import Heuristics from './pages/Heuristics'
import Admin from './pages/Admin'
import KnowledgeBase from './pages/KnowledgeBase'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
    },
  },
})

function RequireAuth({ children }) {
  return isAuthenticated() ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
          <Route path="/cases/:id" element={<RequireAuth><CaseDetail /></RequireAuth>} />
          <Route path="/heuristics" element={<RequireAuth><Heuristics /></RequireAuth>} />
          <Route path="/knowledge-base" element={<RequireAuth><KnowledgeBase /></RequireAuth>} />
          <Route path="/admin" element={<RequireAuth><Admin /></RequireAuth>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
