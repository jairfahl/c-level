import { useState, useRef, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getKnowledgeDocuments, getKnowledgeDocument, uploadKnowledgeDocument, deleteKnowledgeDocument, validateDocumentRelevance } from '../lib/api'
import { Layout } from '../components/layout/Layout'
import { Modal } from '../components/ui/Modal'
import { Alert } from '../components/ui/Alert'
import { PageSpinner } from '../components/ui/Spinner'
import { Badge } from '../components/ui/Badge'
import { Plus, FileText, Trash2, Eye, Upload, X, CheckCircle, AlertTriangle, XCircle, FileSpreadsheet, FileType, Presentation } from 'lucide-react'

const DOMAIN_LABELS = { planning: 'Planejamento', reporting: 'Relatorios', treasury: 'Tesouraria', funding: 'Captacao', risk: 'Risco' }
const TYPE_LABELS = {
  budget_adjustment: 'Ajuste de Orcamento', forecast_revision: 'Revisao de Forecast',
  capital_allocation: 'Alocacao de Capital', debt_structuring: 'Estruturacao de Divida',
  liquidity_management: 'Gestao de Liquidez', risk_hedging: 'Hedge de Risco',
  cost_reduction: 'Reducao de Custos', investment_evaluation: 'Avaliacao de Investimento',
}

const FILE_ICONS = {
  pdf:  { color: 'text-red-600',    bg: 'bg-red-50',    label: 'PDF' },
  docx: { color: 'text-blue-600',   bg: 'bg-blue-50',   label: 'Word' },
  xlsx: { color: 'text-green-600',  bg: 'bg-green-50',  label: 'Excel' },
  xls:  { color: 'text-green-600',  bg: 'bg-green-50',  label: 'Excel' },
  pptx: { color: 'text-orange-600', bg: 'bg-orange-50', label: 'PowerPoint' },
  csv:  { color: 'text-teal-600',   bg: 'bg-teal-50',   label: 'CSV' },
  txt:  { color: 'text-gray-600',   bg: 'bg-gray-50',   label: 'Texto' },
  md:   { color: 'text-purple-600', bg: 'bg-purple-50', label: 'Markdown' },
}

const ACCEPTED_EXTENSIONS = '.pdf,.docx,.txt,.xlsx,.xls,.pptx,.csv,.md'

function getFileExtension(filename) {
  return (filename || '').split('.').pop()?.toLowerCase() || ''
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function FileIcon({ ext, size = 'md' }) {
  const ft = FILE_ICONS[ext] || FILE_ICONS.txt
  const sizeClasses = size === 'lg' ? 'w-12 h-12' : 'w-10 h-10'
  const iconSize = size === 'lg' ? 'w-6 h-6' : 'w-5 h-5'
  return (
    <div className={`flex-shrink-0 ${sizeClasses} rounded-lg ${ft.bg} flex items-center justify-center`}>
      <FileText className={`${iconSize} ${ft.color}`} />
    </div>
  )
}

function DocumentCard({ doc, onPreview, onDelete }) {
  const ext = doc.file_type
  const ft = FILE_ICONS[ext] || FILE_ICONS.txt

  return (
    <div className="px-5 py-4 flex items-start gap-4">
      <FileIcon ext={ext} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5 flex-wrap">
          <button
            onClick={() => onPreview(doc.id)}
            className="text-sm font-semibold text-gray-900 hover:text-brand-700 hover:underline text-left"
          >
            {doc.title}
          </button>
          <Badge color="gray">{ft.label || ext.toUpperCase()}</Badge>
        </div>
        {doc.description && (
          <p className="text-xs text-gray-500 mb-2">{doc.description}</p>
        )}
        <div className="flex items-center gap-3 flex-wrap">
          <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-brand-50 text-brand-700 border border-brand-200">
            {DOMAIN_LABELS[doc.financial_domain] || doc.financial_domain}
          </span>
          {doc.decision_type && (
            <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border border-gray-200">
              {TYPE_LABELS[doc.decision_type] || doc.decision_type}
            </span>
          )}
          <span className="text-xs text-gray-400">
            {formatBytes(doc.file_size_bytes)}
          </span>
          <span className="text-xs text-gray-400">
            {doc.text_length.toLocaleString('pt-BR')} chars
          </span>
          <span className="text-xs text-gray-400">
            {formatDate(doc.created_at)}
          </span>
        </div>
      </div>
      <div className="flex-shrink-0 flex gap-2">
        <button
          onClick={() => onPreview(doc.id)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-brand-700 hover:bg-brand-50 rounded-lg border border-brand-200 transition-colors"
        >
          <Eye className="h-3.5 w-3.5" />
          Preview
        </button>
        <button
          onClick={() => onDelete(doc)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-red-600 hover:bg-red-50 rounded-lg border border-red-200 transition-colors"
        >
          <Trash2 className="h-3.5 w-3.5" />
          Excluir
        </button>
      </div>
    </div>
  )
}

function FormatBadge({ ext }) {
  const ft = FILE_ICONS[ext]
  if (!ft) return null
  return (
    <span className={`inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md ${ft.bg} ${ft.color} font-medium`}>
      {ft.label}
    </span>
  )
}

function UploadModal({ open, onClose }) {
  const qc = useQueryClient()
  const fileInputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [form, setForm] = useState({
    title: '',
    description: '',
    financial_domain: 'planning',
    decision_type: '',
  })
  const [error, setError] = useState('')
  const [step, setStep] = useState(1) // 1 = file+meta, 2 = relevance check
  const [relevanceResult, setRelevanceResult] = useState(null) // { verdict, confidence, reason, ... }
  const [validating, setValidating] = useState(false)

  function set(k, v) { setForm((prev) => ({ ...prev, [k]: v })) }

  function resetAll() {
    setFile(null)
    setForm({ title: '', description: '', financial_domain: 'planning', decision_type: '' })
    setError('')
    setStep(1)
    setRelevanceResult(null)
    setValidating(false)
  }

  function handleClose() {
    resetAll()
    onClose()
  }

  const handleDragOver = useCallback((e) => { e.preventDefault(); setDragging(true) }, [])
  const handleDragEnter = useCallback((e) => { e.preventDefault(); setDragging(true) }, [])
  const handleDragLeave = useCallback((e) => { e.preventDefault(); setDragging(false) }, [])
  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const dropped = e.dataTransfer.files?.[0]
    if (dropped) setFile(dropped)
  }, [])

  const uploadMut = useMutation({
    mutationFn: (confirmRelevance = false) => {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('title', form.title)
      fd.append('financial_domain', form.financial_domain)
      if (form.decision_type) fd.append('decision_type', form.decision_type)
      if (form.description) fd.append('description', form.description)
      if (confirmRelevance) fd.append('confirm_relevance', 'true')
      return uploadKnowledgeDocument(fd)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['knowledge-documents'] })
      handleClose()
    },
    onError: (e) => setError(e.response?.data?.message || e.message || 'Erro ao fazer upload.'),
  })

  async function handleValidateAndUpload() {
    setError('')
    setValidating(true)
    setStep(2)
    setRelevanceResult(null)

    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('financial_domain', form.financial_domain)
      const result = await validateDocumentRelevance(fd)
      setRelevanceResult(result)

      if (result.verdict === 'relevant') {
        // Auto-upload
        uploadMut.mutate(false)
      }
    } catch (e) {
      setError(e.response?.data?.message || e.message || 'Erro na validacao de relevancia.')
      setRelevanceResult({ verdict: 'error' })
    } finally {
      setValidating(false)
    }
  }

  function handleConfirmBorderline() {
    setError('')
    uploadMut.mutate(true)
  }

  const inputCls = 'w-full px-3 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-600'
  const labelCls = 'block text-sm font-medium text-gray-700 mb-1'
  const canProceed = file && form.title

  return (
    <Modal open={open} onClose={handleClose} title="Upload de Documento" size="md">
      {step === 1 ? (
        <div className="space-y-4">
          {/* Drop zone */}
          <div>
            <label className={labelCls}>Arquivo *</label>
            {!file ? (
              <div
                onDragOver={handleDragOver}
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`flex flex-col items-center justify-center min-h-[160px] border-2 border-dashed rounded-xl cursor-pointer transition-all ${
                  dragging
                    ? 'border-brand-600 bg-brand-50'
                    : 'border-gray-300 hover:border-brand-400 hover:bg-gray-50'
                }`}
              >
                <Upload className={`h-8 w-8 mb-3 ${dragging ? 'text-brand-600' : 'text-gray-400'}`} />
                <p className="text-sm text-gray-600 font-medium mb-2">
                  Arraste seu arquivo aqui ou clique para selecionar
                </p>
                <div className="flex flex-wrap gap-1.5 justify-center px-4">
                  {Object.keys(FILE_ICONS).map((ext) => (
                    <FormatBadge key={ext} ext={ext} />
                  ))}
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={ACCEPTED_EXTENSIONS}
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="hidden"
                />
              </div>
            ) : (
              <div className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg bg-gray-50">
                <FileIcon ext={getFileExtension(file.name)} size="lg" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                  <p className="text-xs text-gray-500">{formatBytes(file.size)}</p>
                </div>
                <button
                  onClick={() => setFile(null)}
                  className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            )}
          </div>

          <div>
            <label className={labelCls}>Titulo *</label>
            <input type="text" value={form.title} onChange={(e) => set('title', e.target.value)}
              placeholder="Ex: Politica de Hedge Cambial 2026" className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Descricao</label>
            <textarea value={form.description} onChange={(e) => set('description', e.target.value)}
              rows={2} placeholder="Descricao opcional do documento"
              className={`${inputCls} resize-none`} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelCls}>Dominio Financeiro *</label>
              <select value={form.financial_domain} onChange={(e) => set('financial_domain', e.target.value)} className={inputCls}>
                {Object.entries(DOMAIN_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <div>
              <label className={labelCls}>Tipo de Decisao</label>
              <select value={form.decision_type} onChange={(e) => set('decision_type', e.target.value)} className={inputCls}>
                <option value="">Todos (generico)</option>
                {Object.entries(TYPE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
          </div>

          {error && <Alert variant="error" message={error} />}

          <div className="flex gap-3 pt-2">
            <button onClick={handleClose} className="flex-1 px-4 py-2.5 border border-gray-300 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-50">
              Cancelar
            </button>
            <button
              onClick={handleValidateAndUpload}
              disabled={!canProceed}
              className="flex-1 px-4 py-2.5 bg-brand-900 hover:bg-brand-800 text-white text-sm font-medium rounded-lg disabled:opacity-50"
            >
              Verificar e Enviar
            </button>
          </div>
        </div>
      ) : (
        /* Step 2: Relevance check result */
        <div className="space-y-4">
          {/* File summary */}
          <div className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg bg-gray-50">
            <FileIcon ext={getFileExtension(file?.name)} />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">{file?.name}</p>
              <p className="text-xs text-gray-500">{DOMAIN_LABELS[form.financial_domain]}</p>
            </div>
          </div>

          {/* Validating spinner */}
          {validating && (
            <div className="flex flex-col items-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600 mb-4"></div>
              <p className="text-sm text-gray-600">
                Verificando se o documento e relevante para <strong>{DOMAIN_LABELS[form.financial_domain]}</strong>...
              </p>
            </div>
          )}

          {/* Result: RELEVANT */}
          {relevanceResult?.verdict === 'relevant' && (
            <div className="flex flex-col items-center py-6">
              <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mb-3">
                <CheckCircle className="h-7 w-7 text-green-600" />
              </div>
              <p className="text-base font-semibold text-green-700 mb-1">Documento relevante!</p>
              <p className="text-sm text-gray-500 text-center">{relevanceResult.reason}</p>
              {uploadMut.isPending && (
                <p className="text-sm text-brand-600 mt-3">Fazendo upload...</p>
              )}
            </div>
          )}

          {/* Result: BORDERLINE */}
          {relevanceResult?.verdict === 'borderline' && (
            <div className="space-y-4">
              <div className="flex flex-col items-center py-4">
                <div className="w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center mb-3">
                  <AlertTriangle className="h-7 w-7 text-amber-600" />
                </div>
                <p className="text-base font-semibold text-amber-700 mb-1">Relevancia incerta</p>
                <p className="text-sm text-gray-600 text-center max-w-md">{relevanceResult.reason}</p>
              </div>
              {relevanceResult.domain_keywords_found?.length > 0 && (
                <div className="text-xs text-gray-500">
                  <span className="font-medium">Termos financeiros:</span> {relevanceResult.domain_keywords_found.join(', ')}
                </div>
              )}
              {relevanceResult.off_topic_keywords_found?.length > 0 && (
                <div className="text-xs text-gray-500">
                  <span className="font-medium">Termos fora do dominio:</span> {relevanceResult.off_topic_keywords_found.join(', ')}
                </div>
              )}
              <div className="flex gap-3 pt-2">
                <button onClick={() => { setStep(1); setRelevanceResult(null); setError('') }}
                  className="flex-1 px-4 py-2.5 border border-gray-300 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-50">
                  Voltar
                </button>
                <button
                  onClick={handleConfirmBorderline}
                  disabled={uploadMut.isPending}
                  className="flex-1 px-4 py-2.5 bg-amber-600 hover:bg-amber-700 text-white text-sm font-medium rounded-lg disabled:opacity-50"
                >
                  {uploadMut.isPending ? 'Enviando...' : 'Enviar mesmo assim'}
                </button>
              </div>
            </div>
          )}

          {/* Result: IRRELEVANT */}
          {relevanceResult?.verdict === 'irrelevant' && (
            <div className="space-y-4">
              <div className="flex flex-col items-center py-4">
                <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mb-3">
                  <XCircle className="h-7 w-7 text-red-600" />
                </div>
                <p className="text-base font-semibold text-red-700 mb-1">Documento nao relevante</p>
                <p className="text-sm text-gray-600 text-center max-w-md">{relevanceResult.reason}</p>
              </div>
              <p className="text-sm text-gray-500 text-center">
                Verifique se o dominio financeiro esta correto ou escolha outro documento.
              </p>
              <div className="flex gap-3 pt-2">
                <button onClick={() => { setStep(1); setRelevanceResult(null); setError('') }}
                  className="flex-1 px-4 py-2.5 border border-gray-300 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-50">
                  Voltar e corrigir
                </button>
              </div>
            </div>
          )}

          {/* Result: error */}
          {relevanceResult?.verdict === 'error' && (
            <div className="space-y-4">
              {error && <Alert variant="error" message={error} />}
              <div className="flex gap-3 pt-2">
                <button onClick={() => { setStep(1); setRelevanceResult(null); setError('') }}
                  className="flex-1 px-4 py-2.5 border border-gray-300 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-50">
                  Voltar
                </button>
              </div>
            </div>
          )}

          {error && !relevanceResult?.verdict?.startsWith('error') && (
            <Alert variant="error" message={error} />
          )}
        </div>
      )}
    </Modal>
  )
}

function PreviewModal({ open, onClose, documentId }) {
  const { data, isLoading } = useQuery({
    queryKey: ['knowledge-document', documentId],
    queryFn: () => getKnowledgeDocument(documentId),
    enabled: !!documentId && open,
  })

  return (
    <Modal open={open} onClose={onClose} title={data?.title || 'Preview'} size="lg">
      {isLoading ? (
        <div className="py-8 text-center text-gray-400">Carregando...</div>
      ) : data ? (
        <div className="space-y-4">
          <div className="flex items-center gap-3 flex-wrap text-xs text-gray-500">
            <Badge color="gray">{(FILE_ICONS[data.file_type]?.label || data.file_type).toUpperCase()}</Badge>
            <span>{formatBytes(data.file_size_bytes)}</span>
            <span>{data.text_length.toLocaleString('pt-BR')} caracteres</span>
            <span>{DOMAIN_LABELS[data.financial_domain]}</span>
            {data.decision_type && <span>{TYPE_LABELS[data.decision_type]}</span>}
          </div>
          {data.description && (
            <p className="text-sm text-gray-600">{data.description}</p>
          )}
          <div className="max-h-[60vh] overflow-y-auto border border-gray-200 rounded-lg p-4 bg-gray-50">
            <pre className="text-sm text-gray-800 whitespace-pre-wrap font-sans leading-relaxed">
              {data.extracted_text}
            </pre>
          </div>
        </div>
      ) : null}
    </Modal>
  )
}

function DeleteConfirmModal({ open, onClose, doc, onConfirm, isPending }) {
  return (
    <Modal open={open} onClose={onClose} title="Confirmar Exclusao" size="sm">
      <div className="space-y-4">
        <p className="text-sm text-gray-600">
          Deseja realmente excluir o documento <strong>{doc?.title}</strong>?
          O documento sera desativado e nao aparecera mais nas analises.
        </p>
        <div className="flex gap-3 pt-2">
          <button onClick={onClose} className="flex-1 px-4 py-2.5 border border-gray-300 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-50">
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            disabled={isPending}
            className="flex-1 px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg disabled:opacity-50"
          >
            {isPending ? 'Excluindo...' : 'Excluir'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

export default function KnowledgeBase() {
  const qc = useQueryClient()
  const [filters, setFilters] = useState({ domain: '', decision_type: '' })
  const [showUpload, setShowUpload] = useState(false)
  const [previewId, setPreviewId] = useState(null)
  const [deleteDoc, setDeleteDoc] = useState(null)

  const { data, isLoading } = useQuery({
    queryKey: ['knowledge-documents', filters],
    queryFn: () => getKnowledgeDocuments({
      domain: filters.domain || undefined,
      decision_type: filters.decision_type || undefined,
    }),
  })

  const deleteMut = useMutation({
    mutationFn: (id) => deleteKnowledgeDocument(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['knowledge-documents'] })
      setDeleteDoc(null)
    },
  })

  const selectCls = 'px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-600 bg-white'

  return (
    <Layout>
      <div className="p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Base de Conhecimento</h1>
            <p className="text-sm text-gray-500 mt-0.5">Documentos organizacionais para enriquecer analises</p>
          </div>
          <button onClick={() => setShowUpload(true)} className="flex items-center gap-2 bg-brand-900 hover:bg-brand-800 text-white px-4 py-2.5 rounded-lg text-sm font-medium">
            <Plus className="h-4 w-4" />
            Upload Documento
          </button>
        </div>

        {/* Filters */}
        <div className="flex gap-3 mb-6 flex-wrap">
          <select value={filters.domain} onChange={(e) => setFilters((p) => ({ ...p, domain: e.target.value }))} className={selectCls}>
            <option value="">Todos os dominios</option>
            {Object.entries(DOMAIN_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <select value={filters.decision_type} onChange={(e) => setFilters((p) => ({ ...p, decision_type: e.target.value }))} className={selectCls}>
            <option value="">Todos os tipos</option>
            {Object.entries(TYPE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </div>

        {isLoading ? (
          <PageSpinner />
        ) : !data?.documents?.length ? (
          <div className="text-center py-20">
            <FileText className="h-12 w-12 text-gray-200 mx-auto mb-4" />
            <p className="text-gray-500 font-medium">Nenhum documento na base</p>
            <p className="text-gray-400 text-sm mt-1">Faca upload de documentos (PDF, Excel, Word, PowerPoint, CSV e mais) para enriquecer as analises do Mentor</p>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-5 py-3 border-b border-gray-100 bg-gray-50 text-xs uppercase tracking-wide font-semibold text-gray-500">
              {data.total} documento{data.total !== 1 ? 's' : ''}
            </div>
            <div className="divide-y divide-gray-100">
              {data.documents.map((doc) => (
                <DocumentCard
                  key={doc.id}
                  doc={doc}
                  onPreview={(id) => setPreviewId(id)}
                  onDelete={(d) => setDeleteDoc(d)}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      <UploadModal open={showUpload} onClose={() => setShowUpload(false)} />
      <PreviewModal open={!!previewId} onClose={() => setPreviewId(null)} documentId={previewId} />
      <DeleteConfirmModal
        open={!!deleteDoc}
        onClose={() => setDeleteDoc(null)}
        doc={deleteDoc}
        onConfirm={() => deleteMut.mutate(deleteDoc?.id)}
        isPending={deleteMut.isPending}
      />
    </Layout>
  )
}
