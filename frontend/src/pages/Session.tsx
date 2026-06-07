import { useParams, useNavigate } from 'react-router-dom'
import { useSession } from '../hooks'
import { BatchStatusBar } from '../components/BatchStatusBar'
import { StatusBadge, PageHeader, Loading, EmptyState } from '../components/Shell'

export default function Session() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { session, loading } = useSession(id ?? null)

  if (loading) return <Loading text="Carregando sessão..." />
  if (!session) return <EmptyState message="Sessão não encontrada." />

  const counts = session.product_status_counts ?? {}
  const total = session.product_count ?? 0
  const awaiting = (counts['awaiting_selection'] ?? 0)
  const done = (counts['done'] ?? 0)
  const errors = (counts['error'] ?? 0)

  return (
    <div>
      <PageHeader
        title={session.supplier_name}
        sub={`${session.pdf_filename} · ${total} produtos · imposto ${session.tax_rate}%`}
        action={<StatusBadge status={session.status} />}
      />

      {/* Resumo */}
      <div className="grid-4 mb-20">
        <StatCard label="Total" value={total} />
        <StatCard label="Aguardando seleção" value={awaiting} accent={awaiting > 0} />
        <StatCard label="Concluídos" value={done} color="green" />
        <StatCard label="Erros" value={errors} color={errors > 0 ? 'red' : undefined} />
      </div>

      {/* Fila de lotes */}
      <BatchStatusBar sessionId={id!} />

      {/* Produtos por lote */}
      {session.batches && session.batches.length > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {session.batches.map(batch => (
            <div key={batch.id} className="card card-flush">
              {/* Header do lote */}
              <div className="flex items-center justify-between" style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)' }}>
                <div className="flex items-center gap-12">
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--text2)' }}>
                    LOTE {batch.batch_number}
                  </span>
                  <StatusBadge status={batch.status} />
                </div>
                <div className="flex items-center gap-8">
                  <span style={{ fontSize: 11, color: 'var(--text3)' }}>
                    {batch.product_count ?? 0} produtos
                  </span>
                  {batch.status === 'awaiting_selection' && (
                    <button
                      className="btn-ghost"
                      style={{ fontSize: 11, padding: '5px 12px' }}
                      onClick={() => navigate(`/session/${id}/batch/${batch.id}`)}
                    >
                      Revisar →
                    </button>
                  )}
                </div>
              </div>

              {/* Mini progress bar */}
              <div style={{ height: 3, background: 'var(--bg3)' }}>
                {batch.product_count && batch.product_status_counts && (
                  <div style={{
                    height: '100%',
                    width: `${((batch.product_status_counts['done'] ?? 0) / batch.product_count) * 100}%`,
                    background: 'var(--green)',
                    transition: 'width 0.4s ease',
                  }} />
                )}
              </div>

              {/* Timing */}
              <div className="flex" style={{ padding: '8px 16px', gap: 16 }}>
                {batch.started_at && (
                  <Timing label="Início" value={new Date(batch.started_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })} />
                )}
                {batch.finished_at && (
                  <Timing label="Fim" value={new Date(batch.finished_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })} />
                )}
                {batch.started_at && batch.finished_at && (
                  <Timing
                    label="Duração"
                    value={`${Math.round((new Date(batch.finished_at).getTime() - new Date(batch.started_at).getTime()) / 60000)}min`}
                  />
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card" style={{ textAlign: 'center', padding: '32px 24px' }}>
          <div className="flex items-center gap-8" style={{ justifyContent: 'center', color: 'var(--text2)', fontSize: 13 }}>
            <span className="spinner" />
            Processando o catálogo... os lotes aparecerão aqui em instantes.
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, accent, color }: { label: string; value: number; accent?: boolean; color?: string }) {
  const textColor = color === 'green' ? 'var(--green)'
    : color === 'red' ? 'var(--red)'
    : accent ? 'var(--accent)'
    : 'var(--text0)'

  return (
    <div className="card card-sm">
      <div style={{ fontSize: 9, fontFamily: 'var(--mono)', color: 'var(--text3)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ fontSize: 28, fontFamily: 'var(--mono)', fontWeight: 500, color: textColor }}>
        {value}
      </div>
    </div>
  )
}

function Timing({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span style={{ fontSize: 9, color: 'var(--text3)', fontFamily: 'var(--mono)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>{label} </span>
      <span style={{ fontSize: 11, color: 'var(--text2)', fontFamily: 'var(--mono)' }}>{value}</span>
    </div>
  )
}
