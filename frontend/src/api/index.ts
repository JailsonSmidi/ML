import type { Session, Batch, Product, ListingsResponse, Analysis, Notification } from '../types'

const BASE = '/api'

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Erro desconhecido')
  }
  return res.json()
}

// ─── Sessions ────────────────────────────────────────────────────────────────

export async function uploadCatalog(file: File, supplierName: string, taxRate: number): Promise<Session> {
  const form = new FormData()
  form.append('file', file)
  form.append('supplier_name', supplierName)
  form.append('tax_rate', String(taxRate))
  const res = await fetch(`${BASE}/sessions/`, { method: 'POST', body: form })
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail) }
  return res.json()
}

export const getSessions = () => req<Session[]>('/sessions/')
export const getSession = (id: string) => req<Session>(`/sessions/${id}`)

// ─── Batches ─────────────────────────────────────────────────────────────────

export const getBatches = (sessionId: string) =>
  req<Batch[]>(`/batches/sessions/${sessionId}/batches`)

// ─── Products ────────────────────────────────────────────────────────────────

export const getProduct = (id: string) => req<Product>(`/products/${id}`)

// ─── Listings ────────────────────────────────────────────────────────────────

export const getListings = (productId: string) =>
  req<ListingsResponse>(`/listings/products/${productId}/listings`)

export const toggleListing = (listingId: string, selected: boolean) =>
  req<{ id: string; selected_by_user: boolean }>(`/listings/listings/${listingId}/select?selected=${selected}`, {
    method: 'PATCH',
  })

// ─── Analyses ────────────────────────────────────────────────────────────────

export const runAnalysis = (
  productId: string,
  logistics: string,
  adType: string,
  categoryId: string,
) =>
  req<Analysis>(
    `/analyses/products/${productId}/analyse?logistics_mode=${logistics}&ad_type=${adType}&category_id=${categoryId}`,
    { method: 'POST' },
  )

export const getAnalyses = (productId: string) =>
  req<Analysis[]>(`/analyses/products/${productId}/analyses`)

// ─── Notifications ───────────────────────────────────────────────────────────

export const getNotifications = () => req<Notification[]>('/notifications/notifications/')
export const getUnreadCount = () => req<{ count: number }>('/notifications/notifications/unread-count')
export const markRead = (id: string) =>
  req<{ id: string; read: boolean }>(`/notifications/notifications/${id}/read`, { method: 'PATCH' })
export const markAllRead = () =>
  req<{ marked: boolean }>('/notifications/notifications/read-all', { method: 'PATCH' })
