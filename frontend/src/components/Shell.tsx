import { useState, useEffect } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { useNotifications } from '../hooks'
import { markRead, markAllRead } from '../api'
import type { Notification } from '../types'

// ─── App Shell ────────────────────────────────────────────────────────────────

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-shell">
      <Header />
      <Sidebar />
      <main className="app-main fade-in">{children}</main>
    </div>
  )
}

// ─── Header ───────────────────────────────────────────────────────────────────

function Header() {
  return (
    <header className="app-header">
      <div className="flex items-center gap-8" style={{ flex: 1 }}>
        <span className="mono" style={{ fontSize: 13, fontWeight: 500, letterSpacing: '0.12em', color: 'var(--accent)' }}>
          ML/RESEARCH
        </span>
        <span style={{ color: 'var(--border2)', fontSize: 12 }}>v1.0</span>
      </div>
      <NotificationBell />
    </header>
  )
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────

function Sidebar() {
  const navItems = [
    { to: '/', label: 'Novo catálogo', icon: '⊕' },
    { to: '/history', label: 'Histórico', icon: '◫' },
  ]
  return (
    <aside className="app-sidebar">
      <div style={{ padding: '0 12px', marginBottom: 8 }}>
        <span style={{ fontSize: 10, color: 'var(--text3)', letterSpacing: '0.1em', textTransform: 'uppercase', fontFamily: 'var(--mono)' }}>
          Navegação
        </span>
      </div>
      {navItems.map(({ to, label, icon }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          style={({ isActive }) => ({
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '9px 16px', fontSize: 13,
            color: isActive ? 'var(--text0)' : 'var(--text2)',
            textDecoration: 'none',
            background: isActive ? 'var(--bg2)' : 'transparent',
            borderLeft: isActive ? '2px solid var(--accent)' : '2px solid transparent',
            transition: 'all 0.12s',
          })}
        >
          <span style={{ fontFamily: 'var(--mono)', fontSize: 14, opacity: 0.7 }}>{icon}</span>
          {label}
        </NavLink>
      ))}
    </aside>
  )
}

// ─── Notification Bell ────────────────────────────────────────────────────────

function NotificationBell() {
  const { unreadCount, notifications, fetchAll } = useNotifications()
  const [open, setOpen] = useState(false)

  const handleOpen = () => {
    setOpen(o => !o)
    if (!open) fetchAll()
  }

  const handleMarkAll = async () => {
    await markAllRead()
    fetchAll()
  }

  return (
    <div style={{ position: 'relative' }}>
      <button
        className="btn-icon"
        onClick={handleOpen}
        style={{ position: 'relative', padding: 8 }}
        title="Notificações"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
          <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
        </svg>
        {unreadCount > 0 && (
          <span style={{
            position: 'absolute', top: 4, right: 4,
            background: 'var(--accent)', color: '#0a0a0a',
            width: 14, height: 14, borderRadius: '50%',
            fontSize: 9, fontWeight: 700, fontFamily: 'var(--mono)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div style={{
          position: 'absolute', right: 0, top: 'calc(100% + 8px)',
          width: 360, background: 'var(--bg1)',
          border: '1px solid var(--border)', borderRadius: 'var(--radius-md)',
          zIndex: 200, overflow: 'hidden',
        }}>
          <div className="flex items-center justify-between" style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)' }}>
            <span style={{ fontSize: 12, fontWeight: 500, letterSpacing: '0.06em', textTransform: 'uppercase', fontFamily: 'var(--mono)', color: 'var(--text2)' }}>
              Notificações
            </span>
            {unreadCount > 0 && (
              <button className="btn-ghost" style={{ padding: '4px 10px', fontSize: 11 }} onClick={handleMarkAll}>
                marcar todas como lidas
              </button>
            )}
          </div>
          <div style={{ maxHeight: 400, overflowY: 'auto' }}>
            {notifications.length === 0 ? (
              <div style={{ padding: 24, textAlign: 'center', color: 'var(--text3)', fontSize: 13 }}>
                Nenhuma notificação
              </div>
            ) : (
              notifications.map(n => <NotifItem key={n.id} n={n} onRead={fetchAll} />)
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function NotifItem({ n, onRead }: { n: Notification; onRead: () => void }) {
  const handleRead = async () => {
    if (!n.read) { await markRead(n.id); onRead() }
  }
  return (
    <div
      onClick={handleRead}
      style={{
        padding: '12px 16px', borderBottom: '1px solid var(--border)',
        background: n.read ? 'transparent' : 'rgba(232,212,77,0.04)',
        cursor: n.read ? 'default' : 'pointer',
        transition: 'background 0.12s',
      }}
    >
      <div className="flex items-center gap-8 mb-4">
        {!n.read && <span className="pulse-dot" style={{ background: 'var(--accent)', flexShrink: 0 }} />}
        <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text0)' }}>{n.title}</span>
        <span style={{ marginLeft: 'auto', fontSize: 10, color: 'var(--text3)', fontFamily: 'var(--mono)', whiteSpace: 'nowrap' }}>
          {new Date(n.created_at).toLocaleDateString('pt-BR')}
        </span>
      </div>
      <p style={{ fontSize: 11, color: 'var(--text2)', lineHeight: 1.5, whiteSpace: 'pre-line' }}>
        {n.body.slice(0, 160)}{n.body.length > 160 ? '…' : ''}
      </p>
    </div>
  )
}

// ─── Status Badge ─────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<string, { label: string; cls: string }> = {
  pending:            { label: 'na fila',     cls: 'badge badge-gray' },
  queued:             { label: 'na fila',     cls: 'badge badge-gray' },
  processing:         { label: 'processando', cls: 'badge badge-blue' },
  scraping:           { label: 'scraping',    cls: 'badge badge-blue' },
  awaiting_selection: { label: 'aguardando',  cls: 'badge badge-yellow' },
  awaiting_review:    { label: 'aguardando',  cls: 'badge badge-yellow' },
  analysing:          { label: 'analisando',  cls: 'badge badge-blue' },
  done:               { label: 'concluído',   cls: 'badge badge-green' },
  error:              { label: 'erro',        cls: 'badge badge-red' },
}

export function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] ?? { label: status, cls: 'badge badge-gray' }
  return (
    <span className={cfg.cls}>
      {(status === 'processing' || status === 'scraping') && (
        <span className="spinner" style={{ width: 8, height: 8, marginRight: 5, borderWidth: 1.5 }} />
      )}
      {cfg.label}
    </span>
  )
}

// ─── Metric Card ──────────────────────────────────────────────────────────────

export function MetricCard({
  label, value, unit, highlight, sub,
}: {
  label: string; value: string | number; unit?: string; highlight?: boolean; sub?: string
}) {
  return (
    <div className="card card-sm" style={{ background: highlight ? 'rgba(232,212,77,0.05)' : undefined, borderColor: highlight ? 'rgba(232,212,77,0.3)' : undefined }}>
      <div style={{ fontSize: 10, color: 'var(--text2)', letterSpacing: '0.08em', textTransform: 'uppercase', fontFamily: 'var(--mono)', marginBottom: 6 }}>
        {label}
      </div>
      <div className="flex items-center gap-4">
        <span style={{ fontSize: 22, fontWeight: 500, fontFamily: 'var(--mono)', color: highlight ? 'var(--accent)' : 'var(--text0)' }}>
          {value}
        </span>
        {unit && <span style={{ fontSize: 11, color: 'var(--text2)' }}>{unit}</span>}
      </div>
      {sub && <div style={{ fontSize: 11, color: 'var(--text3)', marginTop: 3 }}>{sub}</div>}
    </div>
  )
}

// ─── Page Header ─────────────────────────────────────────────────────────────

export function PageHeader({ title, sub, action }: { title: string; sub?: string; action?: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between mb-24">
      <div>
        <h1 style={{ fontSize: 20, fontWeight: 500, letterSpacing: '-0.01em' }}>{title}</h1>
        {sub && <p style={{ fontSize: 13, color: 'var(--text2)', marginTop: 3 }}>{sub}</p>}
      </div>
      {action}
    </div>
  )
}

// ─── Empty State ──────────────────────────────────────────────────────────────

export function EmptyState({ message }: { message: string }) {
  return (
    <div style={{ textAlign: 'center', padding: '48px 24px', color: 'var(--text3)', fontSize: 13 }}>
      <div style={{ fontSize: 28, marginBottom: 12, opacity: 0.4 }}>◫</div>
      {message}
    </div>
  )
}

// ─── Loading ──────────────────────────────────────────────────────────────────

export function Loading({ text = 'Carregando...' }: { text?: string }) {
  return (
    <div className="flex items-center gap-8" style={{ color: 'var(--text2)', fontSize: 13, padding: '32px 0' }}>
      <span className="spinner" />
      {text}
    </div>
  )
}
