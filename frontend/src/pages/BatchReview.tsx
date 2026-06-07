import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getBatches, getProduct, getListings } from '../api'
import { ListingCard } from '../components/ListingCard'
import { MarginSimulator, AnalysisResult } from '../components/MarginSimulator'
import { StatusBadge, PageHeader, Loading, EmptyState } from '../components/Shell'
import type { Product, ListingsResponse, Analysis } from '../types'

export default function BatchReview() {
  const { sessionId, batchId } = useParams<{ sessionId: string; batchId: string }>()
  const navigate = useNavigate()

  const [products, setProducts] = useState<Product[]>([])
  const [currentIdx, setCurrentIdx] = useState(0)
  const [listings, setListings] = useState<ListingsResponse | null>(null)
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [loadingProducts, setLoadingProducts] = useState(true)
  const [loadingListings, setLoadingListings] = useState(false)

  // Carrega produtos do lote
  useEffect(() => {
    if (!sessionId || !batchId) return
    const load = async () => {
      try {
        const batches = await getBatches(sessionId)
        const batch = batches.find(b => b.id === batchId)
        if (!batch) return
        // Aqui precisaríamos de um endpoint de produtos por lote
        // Por ora carregamos via session detail — simplificado
        setLoadingProducts(false)
      } catch { setLoadingProducts(false) }
    }
    load()
  }, [sessionId, batchId])

  const currentProduct = products[currentIdx]

  // Carrega anúncios do produto atual
  useEffect(() => {
    if (!currentProduct) return
    setListings(null)
    setAnalysis(null)
    setLoadingListings(true)
    getListings(currentProduct.id)
      .then(setListings)
      .finally(() => setLoadingListings(false))
  }, [currentProduct?.id])

  const totalSelected = listings
    ? [...listings.catalog, ...listings.organic].filter(l => l.selected_by_user).length
    : 0

  const handleToggle = (id: string, selected: boolean) => {
    if (!listings) return
    const update = (arr: typeof listings.catalog) =>
      arr.map(l => l.id === id ? { ...l, selected_by_user: selected } : l)
    setListings({ catalog: update(listings.catalog), organic: update(listings.organic) })
  }

  if (loadingProducts) return <Loading text="Carregando lote..." />

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 24, alignItems: 'start' }}>

      {/* Painel esquerdo — listagem de anúncios */}
      <div>
        <PageHeader
          title="Revisar anúncios"
          sub={currentProduct ? `${currentProduct.catalog_name} · busca: "${currentProduct.best_search_term}"` : 'Selecione os anúncios de referência'}
          action={
            <div className="flex items-center gap-8">
              {currentProduct && <StatusBadge status={currentProduct.status} />}
              <button className="btn-ghost" style={{ fontSize: 12 }} onClick={() => navigate(`/session/${sessionId}`)}>
                ← Voltar
              </button>
            </div>
          }
        />

        {/* Navegação entre produtos do lote */}
        {products.length > 1 && (
          <div className="flex items-center gap-8 mb-16" style={{ overflowX: 'auto', paddingBottom: 4 }}>
            {products.map((p, i) => (
              <button
                key={p.id}
                onClick={() => setCurrentIdx(i)}
                style={{
                  flexShrink: 0, padding: '6px 12px', borderRadius: 'var(--radius)',
                  fontSize: 11, fontFamily: 'var(--mono)',
                  background: i === currentIdx ? 'var(--bg3)' : 'transparent',
                  border: `1px solid ${i === currentIdx ? 'var(--border2)' : 'transparent'}`,
                  color: i === currentIdx ? 'var(--text0)' : 'var(--text3)',
                  cursor: 'pointer',
                }}
              >
                {i + 1}. {p.catalog_name.slice(0, 20)}{p.catalog_name.length > 20 ? '…' : ''}
              </button>
            ))}
          </div>
        )}

        {loadingListings ? (
          <Loading text="Buscando anúncios..." />
        ) : !listings ? (
          <EmptyState message="Nenhum anúncio encontrado para este produto." />
        ) : (
          <>
            {/* Anúncios de catálogo */}
            {listings.catalog.length > 0 && (
              <section className="mb-20">
                <SectionHeader label="Catálogo" count={listings.catalog.length} />
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 10 }}>
                  {listings.catalog.map(l => (
                    <ListingCard key={l.id} listing={l} onToggle={handleToggle} />
                  ))}
                </div>
              </section>
            )}

            {/* Anúncios orgânicos */}
            {listings.organic.length > 0 && (
              <section>
                <SectionHeader label="Orgânicos" count={listings.organic.length} />
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 10 }}>
                  {listings.organic.map(l => (
                    <ListingCard key={l.id} listing={l} onToggle={handleToggle} />
                  ))}
                </div>
              </section>
            )}

            {listings.catalog.length === 0 && listings.organic.length === 0 && (
              <EmptyState message="Nenhum anúncio passou pelo filtro de visitação mínima." />
            )}
          </>
        )}
      </div>

      {/* Painel direito — simulador de margem */}
      <div style={{ position: 'sticky', top: 72 }}>
        <div className="card">
          <div style={{ fontSize: 10, fontFamily: 'var(--mono)', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text2)', marginBottom: 14 }}>
            Simulador de margem
          </div>

          {totalSelected === 0 ? (
            <div style={{ color: 'var(--text3)', fontSize: 12, textAlign: 'center', padding: '24px 0' }}>
              Selecione ao menos um anúncio de referência para calcular a margem.
            </div>
          ) : (
            <>
              <div className="flex items-center gap-6 mb-16" style={{ padding: '8px 10px', background: 'rgba(232,212,77,0.06)', borderRadius: 'var(--radius)', border: '1px solid rgba(232,212,77,0.15)' }}>
                <span style={{ fontSize: 10, fontFamily: 'var(--mono)', color: 'var(--accent)' }}>
                  {totalSelected} anúncio{totalSelected > 1 ? 's' : ''} selecionado{totalSelected > 1 ? 's' : ''}
                </span>
              </div>

              {currentProduct && (
                <MarginSimulator
                  productId={currentProduct.id}
                  onAnalysed={setAnalysis}
                />
              )}
            </>
          )}
        </div>

        {/* Análises anteriores do produto */}
        {analysis && (
          <div className="card mt-12">
            <div style={{ fontSize: 10, fontFamily: 'var(--mono)', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text2)', marginBottom: 14 }}>
              Último resultado
            </div>
            <AnalysisResult analysis={analysis} />
          </div>
        )}
      </div>
    </div>
  )
}

function SectionHeader({ label, count }: { label: string; count: number }) {
  return (
    <div className="flex items-center gap-8 mb-10">
      <span style={{ fontSize: 10, fontFamily: 'var(--mono)', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text2)' }}>
        {label}
      </span>
      <span style={{ fontSize: 10, fontFamily: 'var(--mono)', color: 'var(--text3)' }}>
        {count}
      </span>
      <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
    </div>
  )
}
