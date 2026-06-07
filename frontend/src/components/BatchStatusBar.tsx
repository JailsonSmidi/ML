import { useBatches } from '../hooks'
import { StatusBadge } from './Shell'
import type { Batch } from '../types'

export function BatchStatusBar({ sessionId }: { sessionId: string }) {
  const { batches, loading } = useBatches(sessionId)

  if (loading) return null
  if (batches.length === 0) return null

  return (
    <div className="card card-flush mb-20" style={{ overflow: 'hidden' }}>
      <div style={{ padding: '10px 16px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: 10, fontFamily: 'var(--mono)', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text2)' }}>
          Lotes de processamento
        </span>
        <span style={{ fontSize: 10, fontFamily: 'var(--mono)', color: 'var(--text3)' }}>
          {batches.filter(b => b.status === 'done').length}/{batches.length} concluídos
        </span>
      </div>
      <div style={{ display: 'flex', overflowX: 'auto', padding: '12px 16px', gap: 8 }}>
        {batches.map(batch => (
          <BatchPill key={batch.id} batch={batch} />
        ))}
      </div>
    </div>
  )
}

function BatchPill({ batch }: { batch: Batch }) {
  const isActive = batch.status === 'processing' || batch.status === 'scraping'
  const isWaiting = batch.status === 'awaiting_selection'
  const isDone = batch.status === 'done'
  const isQueued = batch.status === 'queued'

  const borderColor = isActive ? 'var(--blue)'
    : isWaiting ? 'var(--accent)'
    : isDone ? 'var(--green)'
    : 'var(--border)'

  return (
    <div style={{
      flexShrink: 0,
      minWidth: 120,
      background: 'var(--bg2)',
      border: `1px solid ${borderColor}`,
      borderRadius: 'var(--radius)',
      padding: '8px 12px',
      transition: 'border-color 0.2s',
    }}>
      <div className="flex items-center justify-between mb-4">
        <span style={{ fontSize: 10, fontFamily: 'var(--mono)', color: 'var(--text2)', letterSpacing: '0.06em' }}>
          LOTE {batch.batch_number}
        </span>
        {isActive && <span className="pulse-dot" style={{ background: 'var(--blue)' }} />}
        {isWaiting && <span className="pulse-dot" style={{ background: 'var(--accent)' }} />}
      </div>

      <StatusBadge status={batch.status} />

      <div style={{ marginTop: 8, fontSize: 11, color: 'var(--text3)' }}>
        {batch.product_count ?? 0} produtos
      </div>

      {batch.finished_at && (
        <div style={{ fontSize: 10, color: 'var(--text3)', fontFamily: 'var(--mono)', marginTop: 2 }}>
          {new Date(batch.finished_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
        </div>
      )}
    </div>
  )
}
