import { useState } from 'react'
import { toggleListing } from '../api'
import type { Listing } from '../types'

interface ListingCardProps {
  listing: Listing
  onToggle: (id: string, selected: boolean) => void
}

export function ListingCard({ listing, onToggle }: ListingCardProps) {
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState(listing.selected_by_user)

  const handleToggle = async () => {
    setLoading(true)
    try {
      await toggleListing(listing.id, !selected)
      setSelected(s => !s)
      onToggle(listing.id, !selected)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        background: selected ? 'rgba(232,212,77,0.04)' : 'var(--bg2)',
        border: `1px solid ${selected ? 'rgba(232,212,77,0.35)' : 'var(--border)'}`,
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden',
        transition: 'all 0.15s',
        cursor: 'pointer',
      }}
      onClick={handleToggle}
    >
      {/* Thumbnail */}
      <div style={{ position: 'relative', height: 120, background: 'var(--bg3)', overflow: 'hidden' }}>
        {listing.thumbnail_url ? (
          <img
            src={listing.thumbnail_url}
            alt={listing.title}
            style={{ width: '100%', height: '100%', objectFit: 'contain', padding: 8 }}
            onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
          />
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text3)', fontSize: 24 }}>◫</div>
        )}

        {/* Tags sobrepostas */}
        <div style={{ position: 'absolute', top: 6, left: 6, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          <span className={`badge ${listing.logistics === 'full' ? 'badge-green' : 'badge-gray'}`}>
            {listing.logistics === 'full' ? 'Full' : 'ME'}
          </span>
          <span className={`badge ${listing.ad_type === 'premium' ? 'badge-blue' : 'badge-gray'}`}>
            {listing.ad_type === 'premium' ? 'Premium' : 'Classic'}
          </span>
        </div>

        {/* Checkbox de seleção */}
        <div style={{
          position: 'absolute', top: 6, right: 6,
          width: 20, height: 20,
          background: selected ? 'var(--accent)' : 'var(--bg4)',
          border: `1.5px solid ${selected ? 'var(--accent)' : 'var(--border2)'}`,
          borderRadius: 3,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          transition: 'all 0.12s',
        }}>
          {loading ? (
            <span className="spinner" style={{ width: 10, height: 10, borderWidth: 1.5 }} />
          ) : selected ? (
            <svg width="11" height="11" viewBox="0 0 12 12" fill="none">
              <path d="M2 6l3 3 5-5" stroke="#0a0a0a" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          ) : null}
        </div>
      </div>

      {/* Dados */}
      <div style={{ padding: '10px 12px' }}>
        <p style={{ fontSize: 12, color: 'var(--text1)', lineHeight: 1.4, marginBottom: 10,
          display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {listing.title}
        </p>

        {/* Preço */}
        <div className="flex items-center gap-4 mb-10">
          <span style={{ fontSize: 16, fontWeight: 500, fontFamily: 'var(--mono)', color: 'var(--text0)' }}>
            {listing.price.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
          </span>
        </div>

        {/* Métricas */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 12px' }}>
          <Metric label="visitas/7d" value={listing.estimated_visits_7d != null ? `~${listing.estimated_visits_7d.toLocaleString('pt-BR')}` : '—'} />
          <Metric label="dias no ar" value={listing.listing_age_days != null ? `${listing.listing_age_days}d` : '—'} />
          <Metric
            label="vendas/dia"
            value={listing.sales_per_day_est != null ? `~${listing.sales_per_day_est.toFixed(1)}` : '—'}
            sub="estimado"
          />
          <Metric label="posição" value={listing.search_position != null ? `#${listing.search_position}` : '—'} />
        </div>
      </div>
    </div>
  )
}

function Metric({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div>
      <div style={{ fontSize: 9, color: 'var(--text3)', fontFamily: 'var(--mono)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
        {label}
      </div>
      <div style={{ fontSize: 12, fontFamily: 'var(--mono)', color: 'var(--text1)', marginTop: 1 }}>
        {value}
        {sub && <span style={{ fontSize: 9, color: 'var(--text3)', marginLeft: 3 }}>{sub}</span>}
      </div>
    </div>
  )
}
