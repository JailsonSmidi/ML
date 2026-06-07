import { useState, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { uploadCatalog } from '../api'
import { PageHeader } from '../components/Shell'

export default function Upload() {
  const navigate = useNavigate()
  const fileRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [supplier, setSupplier] = useState('')
  const [taxRate, setTaxRate] = useState(4)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)

  const handleFile = (f: File) => {
    if (!f.name.endsWith('.pdf')) { setError('Apenas arquivos PDF.'); return }
    if (f.size > 50 * 1024 * 1024) { setError('PDF deve ter no máximo 50MB.'); return }
    setFile(f)
    setError(null)
  }

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }, [])

  const handleSubmit = async () => {
    if (!file || !supplier.trim()) return
    setLoading(true)
    setError(null)
    try {
      const session = await uploadCatalog(file, supplier.trim(), taxRate)
      navigate(`/session/${session.id}`)
    } catch (e: any) {
      setError(e.message)
      setLoading(false)
    }
  }

  const canSubmit = file && supplier.trim() && !loading

  return (
    <div style={{ maxWidth: 560 }}>
      <PageHeader
        title="Novo catálogo"
        sub="Faça upload do PDF do fornecedor para iniciar a pesquisa de mercado."
      />

      {/* Drop zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => fileRef.current?.click()}
        style={{
          border: `1.5px dashed ${dragging ? 'var(--accent)' : file ? 'var(--green)' : 'var(--border2)'}`,
          borderRadius: 'var(--radius-md)',
          padding: '36px 24px',
          textAlign: 'center',
          cursor: 'pointer',
          background: dragging ? 'rgba(232,212,77,0.04)' : file ? 'rgba(76,175,120,0.04)' : 'var(--bg1)',
          transition: 'all 0.15s',
          marginBottom: 20,
        }}
      >
        <input ref={fileRef} type="file" accept=".pdf" style={{ display: 'none' }}
          onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f) }} />

        {file ? (
          <>
            <div style={{ fontSize: 28, marginBottom: 8 }}>◈</div>
            <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--green)', fontFamily: 'var(--mono)', marginBottom: 4 }}>
              {file.name}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text3)' }}>
              {(file.size / 1024 / 1024).toFixed(2)} MB · clique para trocar
            </div>
          </>
        ) : (
          <>
            <div style={{ fontSize: 32, marginBottom: 8, opacity: 0.3 }}>⊕</div>
            <div style={{ fontSize: 13, color: 'var(--text1)', marginBottom: 4 }}>
              Arraste o PDF aqui ou clique para selecionar
            </div>
            <div style={{ fontSize: 11, color: 'var(--text3)' }}>Máximo 50MB</div>
          </>
        )}
      </div>

      {/* Campos */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div>
          <label>Fornecedor</label>
          <input
            type="text"
            placeholder="Ex: Thor Import, Wei Import..."
            value={supplier}
            onChange={e => setSupplier(e.target.value)}
          />
        </div>

        <div>
          <label>Alíquota de imposto (%)</label>
          <input
            type="number"
            min={0} max={100} step={0.5}
            value={taxRate}
            onChange={e => setTaxRate(Number(e.target.value))}
            style={{ width: 120 }}
          />
          <p style={{ fontSize: 11, color: 'var(--text3)', marginTop: 4 }}>
            Padrão 4% (Simples Nacional planejado). Pode ser alterado por sessão.
          </p>
        </div>

        {error && (
          <div style={{ padding: '10px 14px', background: 'var(--red-bg)', border: '1px solid rgba(224,85,85,0.2)', borderRadius: 'var(--radius)', color: 'var(--red)', fontSize: 12 }}>
            {error}
          </div>
        )}

        <button
          className="btn-primary"
          onClick={handleSubmit}
          disabled={!canSubmit}
          style={{ alignSelf: 'flex-start', minWidth: 160 }}
        >
          {loading ? (
            <span className="flex items-center gap-8">
              <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
              Enviando...
            </span>
          ) : 'Iniciar análise →'}
        </button>
      </div>

      {/* Info */}
      <div className="card card-sm mt-24" style={{ background: 'var(--bg2)' }}>
        <div style={{ fontSize: 10, fontFamily: 'var(--mono)', color: 'var(--text3)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 8 }}>
          O que acontece após o upload
        </div>
        {[
          'A IA extrai todos os produtos do catálogo',
          'Gera e valida os melhores termos de busca',
          'Processa em lotes de 20 produtos a cada 30 min',
          'Você valida os anúncios encontrados e calcula a margem',
        ].map((step, i) => (
          <div key={i} className="flex items-center gap-8" style={{ fontSize: 12, color: 'var(--text2)', padding: '4px 0' }}>
            <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text3)', minWidth: 16 }}>{i + 1}.</span>
            {step}
          </div>
        ))}
      </div>
    </div>
  )
}
