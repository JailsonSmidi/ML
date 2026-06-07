import { useState } from 'react'
import { runAnalysis, getAnalyses } from '../api'
import type { Analysis, Logistics, AdType } from '../types'

interface MarginSimulatorProps {
  productId: string
  onAnalysed: (a: Analysis) => void
}

const CATEGORIES = [
  { id: 'MLB1648', name: 'Eletrônicos, Áudio e Vídeo' },
  { id: 'MLB1051', name: 'Casa, Móveis e Decoração' },
  { id: 'MLB1500', name: 'Calçados, Roupas e Bolsas' },
  { id: 'MLB218519', name: 'Esportes e Fitness' },
  { id: 'MLB1246', name: 'Beleza e Cuidado Pessoal' },
  { id: 'MLB1144', name: 'Bebês' },
  { id: 'MLB4655', name: 'Jardim e Animais' },
  { id: 'MLB1196', name: 'Ferramentas e Construção' },
  { id: 'MLB1499', name: 'Informática' },
  { id: 'MLB1540', name: 'Telefonia e Celulares' },
  { id: 'MLB3913', name: 'Eletrodomésticos' },
  { id: 'MLB1132', name: 'Brinquedos e Hobbies' },
  { id: 'MLB2531', name: 'Alimentos e Bebidas' },
  { id: 'MLB1743', name: 'Indústria e Comércio' },
  { id: 'MLB174391', name: 'Acessórios para Veículos' },
  { id: 'MLB1000', name: 'Antiguidades e Coleções' },
  { id: 'MLB2197', name: 'Livros, Revistas e Comics' },
  { id: 'MLB1182', name: 'Saúde' },
  { id: 'MLB3937', name: 'Iluminação e Elétrica' },
  { id: 'MLB1071', name: 'Instrumentos Musicais' },
  { id: 'MLB1168', name: 'Games' },
  { id: 'MLB1039', name: 'Câmeras e Acessórios' },
]

export function MarginSimulator({ productId, onAnalysed }: MarginSimulatorProps) {
  const [logistics, setLogistics] = useState<Logistics>('full')
  const [adType, setAdType] = useState<AdType>('premium')
  const [categoryId, setCategoryId] = useState('MLB1648')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<Analysis | null>(null)

  const handleCalculate = async () => {
    setLoading(true)
    setError(null)
    try {
      const analysis = await runAnalysis(productId, logistics, adType, categoryId)
      setResult(analysis)
      onAnalysed(analysis)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      {/* Seletor de combinação */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
        <div>
          <label>Logística</label>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
            {(['full', 'mercado_envios'] as Logistics[]).map(l => (
              <ToggleBtn
                key={l}
                active={logistics === l}
                onClick={() => setLogistics(l)}
                label={l === 'full' ? 'Full' : 'Mercado Envios'}
              />
            ))}
          </div>
        </div>
        <div>
          <label>Tipo de anúncio</label>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
            {(['classic', 'premium'] as AdType[]).map(t => (
              <ToggleBtn
                key={t}
                active={adType === t}
                onClick={() => setAdType(t)}
                label={t === 'classic' ? 'Clássico' : 'Premium'}
              />
            ))}
          </div>
        </div>
      </div>

      <div style={{ marginBottom: 16 }}>
        <label>Categoria do produto</label>
        <select value={categoryId} onChange={e => setCategoryId(e.target.value)}>
          {CATEGORIES.map(c => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      <button
        className="btn-primary w-full"
        onClick={handleCalculate}
        disabled={loading}
        style={{ marginBottom: result || error ? 20 : 0 }}
      >
        {loading ? (
          <span className="flex items-center gap-8" style={{ justifyContent: 'center' }}>
            <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
            Calculando...
          </span>
        ) : 'Calcular margem'}
      </button>

      {error && (
        <div style={{ padding: '10px 14px', background: 'var(--red-bg)', border: '1px solid rgba(224,85,85,0.2)', borderRadius: 'var(--radius)', color: 'var(--red)', fontSize: 12, marginBottom: 16 }}>
          {error}
        </div>
      )}

      {result && <AnalysisResult analysis={result} />}
    </div>
  )
}

function ToggleBtn({ active, onClick, label }: { active: boolean; onClick: () => void; label: string }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '8px 12px', borderRadius: 'var(--radius)', fontSize: 12, fontWeight: 500,
        background: active ? 'rgba(232,212,77,0.12)' : 'var(--bg2)',
        border: `1px solid ${active ? 'rgba(232,212,77,0.4)' : 'var(--border)'}`,
        color: active ? 'var(--accent)' : 'var(--text2)',
        cursor: 'pointer', transition: 'all 0.12s',
      }}
    >
      {label}
    </button>
  )
}

export function AnalysisResult({ analysis }: { analysis: Analysis }) {
  const approved = analysis.verdict === 'approved'

  return (
    <div style={{
      background: approved ? 'rgba(76,175,120,0.06)' : 'rgba(224,85,85,0.06)',
      border: `1px solid ${approved ? 'rgba(76,175,120,0.25)' : 'rgba(224,85,85,0.25)'}`,
      borderRadius: 'var(--radius-md)',
      overflow: 'hidden',
    }}>
      {/* Cabeçalho veredito */}
      <div style={{
        padding: '12px 16px',
        background: approved ? 'rgba(76,175,120,0.1)' : 'rgba(224,85,85,0.1)',
        borderBottom: `1px solid ${approved ? 'rgba(76,175,120,0.2)' : 'rgba(224,85,85,0.2)'}`,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div className="flex items-center gap-8">
          <span style={{ fontSize: 16 }}>{approved ? '✓' : '✗'}</span>
          <span style={{ fontSize: 13, fontWeight: 600, color: approved ? 'var(--green)' : 'var(--red)' }}>
            {approved ? 'APROVADO' : 'REPROVADO'}
          </span>
        </div>
        <div className="flex gap-4">
          <span className="badge badge-gray">
            {analysis.logistics_mode === 'full' ? 'Full' : 'ME'}
          </span>
          <span className="badge badge-gray">
            {analysis.ad_type === 'premium' ? 'Premium' : 'Classic'}
          </span>
        </div>
      </div>

      {analysis.rejection_reason && (
        <div style={{ padding: '8px 16px', borderBottom: `1px solid ${approved ? 'rgba(76,175,120,0.15)' : 'rgba(224,85,85,0.15)'}`, fontSize: 11, color: 'var(--red)' }}>
          {analysis.rejection_reason}
        </div>
      )}

      {/* Métricas */}
      <div style={{ padding: 16 }}>
        {/* Margens em destaque */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
          <MarginBox
            label="Pós-ranqueamento"
            value={analysis.margin_post_ranking}
            target={15}
            highlight
          />
          <MarginBox
            label="Ranqueamento"
            value={analysis.margin_ranking}
            target={0}
          />
        </div>

        {/* Breakdown de custos */}
        <div style={{ fontSize: 11, color: 'var(--text2)' }}>
          <div style={{ fontSize: 9, fontFamily: 'var(--mono)', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text3)', marginBottom: 8 }}>
            Composição de custos
          </div>
          <CostRow label="Preço sugerido" value={analysis.suggested_price} accent />
          <CostRow label={`Comissão ML (${analysis.ml_commission_rate}%)`} value={-analysis.suggested_price * analysis.ml_commission_rate / 100} />
          <CostRow label="Frete" value={-analysis.shipping_cost} />
          <CostRow label="Imposto" value={-analysis.tax_cost} />
          <div style={{ borderTop: '1px solid var(--border)', marginTop: 6, paddingTop: 6 }}>
            <CostRow label="Custo total" value={analysis.total_cost} />
          </div>
        </div>

        {/* Faixa de preços */}
        {analysis.min_competitor_price != null && (
          <div style={{ marginTop: 12, padding: '8px 10px', background: 'var(--bg3)', borderRadius: 'var(--radius)', fontSize: 11 }}>
            <span style={{ color: 'var(--text3)', fontFamily: 'var(--mono)', fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Faixa concorrentes selecionados</span>
            <div className="flex items-center gap-8 mt-4">
              <span style={{ fontFamily: 'var(--mono)', color: 'var(--red)' }}>
                {analysis.min_competitor_price.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
              </span>
              <span style={{ color: 'var(--text3)' }}>→</span>
              <span style={{ fontFamily: 'var(--mono)', color: 'var(--green)' }}>
                {analysis.max_competitor_price!.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
              </span>
              <span style={{ color: 'var(--text2)', marginLeft: 'auto', fontFamily: 'var(--mono)' }}>
                sugerido: {analysis.suggested_price.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function MarginBox({ label, value, target, highlight }: { label: string; value: number; target: number; highlight?: boolean }) {
  const ok = value >= target
  const color = ok ? 'var(--green)' : 'var(--red)'
  return (
    <div style={{ background: 'var(--bg2)', borderRadius: 'var(--radius)', padding: '10px 12px', border: `1px solid ${ok ? 'rgba(76,175,120,0.2)' : 'rgba(224,85,85,0.2)'}` }}>
      <div style={{ fontSize: 9, fontFamily: 'var(--mono)', color: 'var(--text3)', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ fontSize: 22, fontFamily: 'var(--mono)', fontWeight: 500, color }}>
        {value.toFixed(1)}%
      </div>
      <div style={{ fontSize: 9, color: 'var(--text3)', marginTop: 2 }}>
        mín. {target}%
      </div>
    </div>
  )
}

function CostRow({ label, value, accent }: { label: string; value: number; accent?: boolean }) {
  const formatted = Math.abs(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
  return (
    <div className="flex justify-between" style={{ padding: '3px 0' }}>
      <span style={{ color: 'var(--text2)' }}>{label}</span>
      <span style={{ fontFamily: 'var(--mono)', color: accent ? 'var(--text0)' : value < 0 ? 'var(--red)' : 'var(--text1)' }}>
        {value < 0 ? '-' : ''}{formatted}
      </span>
    </div>
  )
}
