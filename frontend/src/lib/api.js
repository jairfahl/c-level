import axios from 'axios'
import { getToken, clearAuth } from './auth'

const api = axios.create({
  baseURL: '/v1',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      clearAuth()
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// Auth
export const login = (username) =>
  api.post('/auth/token', { username }).then((r) => r.data)

// Cases
export const getCases = (params) =>
  api.get('/financial-decision-cases', { params }).then((r) => r.data)

export const getCase = (id) =>
  api.get(`/financial-decision-cases/${id}`).then((r) => r.data)

export const createCase = (data) =>
  api.post('/financial-decision-cases', data).then((r) => r.data)

// State transitions
export const classifyCase = (id, data) =>
  api.put(`/financial-decision-cases/${id}/classify`, data).then((r) => r.data)

export const structureCase = (id, data) =>
  api.put(`/financial-decision-cases/${id}/structure`, data).then((r) => r.data)

export const suggestMethods = (id) =>
  api.get(`/financial-decision-cases/${id}/suggest-methods`).then((r) => r.data)

export const analyzeCase = (id, body = null) =>
  api.put(`/financial-decision-cases/${id}/analyze`, body).then((r) => r.data)

export const suggestReclassification = (id) =>
  api.get(`/financial-decision-cases/${id}/suggest-reclassification`).then(r => r.data)

export const reclassifyCase = (id, body) =>
  api.patch(`/financial-decision-cases/${id}/reclassify`, body).then(r => r.data)

export const reanalyzeCase = (id) =>
  api.put(`/financial-decision-cases/${id}/reanalyze`).then((r) => r.data)

export const recordHypothesis = (id, data) =>
  api.put(`/financial-decision-cases/${id}/hypothesis`, data).then((r) => r.data)

export const decideCase = (id, data) =>
  api.put(`/financial-decision-cases/${id}/decide`, data).then((r) => r.data)

export const reviewCase = (id, data) =>
  api.put(`/financial-decision-cases/${id}/review`, data).then((r) => r.data)

// Audit
export const getTransitions = (id) =>
  api.get(`/financial-decision-cases/${id}/state-transitions`).then((r) => r.data)

// Heuristics
export const getHeuristics = (params) =>
  api.get('/heuristics', { params }).then((r) => r.data)

export const createHeuristic = (data) =>
  api.post('/heuristics', data).then((r) => r.data)

export const deactivateHeuristic = (id) =>
  api.put(`/heuristics/${id}/deactivate`).then((r) => r.data)

export const getLearningSummary = () =>
  api.get('/heuristics/learning-summary').then((r) => r.data)

// Knowledge Base
export const getKnowledgeDocuments = (params) =>
  api.get('/knowledge-base', { params }).then((r) => r.data)

export const getKnowledgeDocument = (id) =>
  api.get(`/knowledge-base/${id}`).then((r) => r.data)

export const uploadKnowledgeDocument = (formData) =>
  api.post('/knowledge-base/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data)

export const deleteKnowledgeDocument = (id) =>
  api.delete(`/knowledge-base/${id}`).then((r) => r.data)

export const validateDocumentRelevance = (formData) =>
  api.post('/knowledge-base/validate-relevance', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data)

// Admin
export const getPendingReviews = () =>
  api.get('/admin/pending-reviews').then((r) => r.data)

export const getDecisionIntelligence = () =>
  api.get('/admin/decision-intelligence').then((r) => r.data)

export const getApiBalance = () =>
  api.get('/admin/api-balance').then((r) => r.data)

// Framework Catalog
export const getFrameworkCatalog = () =>
  api.get('/financial-decision-cases/framework-catalog').then((r) => r.data)

// Intelligence — Heuristic Alerts & Benchmark
export const getHeuristicAlerts = (id) =>
  api.get(`/financial-decision-cases/${id}/heuristic-alerts`).then((r) => r.data)
