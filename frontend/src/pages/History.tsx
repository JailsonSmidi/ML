import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getSessions } from '../api'
import { StatusBadge, PageHeader, Loading, EmptyState } from '../components/Shell'
import type { Session } from '../types'

export default function History() {
  const navigate = useNavigate()
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getSessions().then(setSessions).finally(() => setLoading(false))
  }, [])

  if (loading) return <Loading text="Carregando histórico..." />

  return (
    <div>
      <PageHeader
        title="Histórico"
        sub={`${sessions.length} sessão${sessions.length !== 1 ? 'ões' : ''} registrada${sessions.length !== 1 ? 's' : ''}`}
        action={
          <button className="btn-primary" onClick={() => navigate('/')}>
            + Novo catálogo
          </button>
        }
      />

      {sessions.length === 0 ? (
        <EmptyState message="Nenhuma sessão encontrada. Faça upload de um catálogo para começar." />
      ) : (
        <div className="card card-flush">
          <table className="table">
            <thead>
              <tr>
                <th>Fornecedor</th>
                <th>Arquivo</th>
                <th>Imposto</th>
                <th>Produtos</th>
                <th>Status</th>
                <th>Data</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {sessions.map(s => (
                <SessionRow key={s.id} session={s} onClick={() => navigate(`/session/${s.id}`)} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function SessionRow({ session, onClick }: { session: Session; onClick: () => void }) {
  const counts = session.product_status_counts ?? {}
  const done = counts['done'] ?? 0
  const total = session.product_count ?? 0
  const awaiting = counts['awaiting_selection'] ?? 0

  return (
    <tr style={{ cursor: 'pointer' }} onClick={onClick}>
      <td>
        <span style={{ fontWeight: 500, color: 'var(--text0)' }}>{session.supplier_name}</span>
      </td>
      <td>
        <span className="mono-cell" style={{ fontSize: 11, color: 'var(--text2)' }}>
          {session.pdf_filename.length > 30 ? session.pdf_filename.slice(0, 28) + '…' : session.pdf_filename}
        </span>
      </td>
      <td>
        <span className="mono-cell">{session.tax_rate}%</span>
      </td>
      <td>
        <div className="flex items-center gap-6">
          <span className="mono-cell">{total}</span>
          {done > 0 && (
            <span style={{ fontSize: 10, color: 'var(--green)', fontFamily: 'var(--mono)' }}>
              {done} ✓
            </span>
          )}
          {awaiting > 0 && (
            <span style={{ fontSize: 10, color: 'var(--accent)', fontFamily: 'var(--mono)' }}>
              {awaiting} ⏳
            </span>
          )}
        </div>
      </td>
      <td><StatusBadge status={session.status} /></td>
      <td>
        <span className="mono-cell" style={{ fontSize: 11, color: 'var(--text2)' }}>
          {new Date(session.created_at).toLocaleDateString('pt-BR', {
            day: '2-digit', month: '2-digit', year: '2-digit',
            hour: '2-digit', minute: '2-digit',
          })}
        </span>
      </td>
      <td>
        <span style={{ fontSize: 11, color: 'var(--blue)' }}>→</span>
      </td>
    </tr>
  )
}
