export type SessionStatus = 'pending' | 'processing' | 'awaiting_review' | 'done' | 'error'
export type BatchStatus = 'queued' | 'processing' | 'awaiting_selection' | 'done' | 'error'
export type ProductStatus = 'pending' | 'scraping' | 'awaiting_selection' | 'analysing' | 'done' | 'error'
export type ListingType = 'catalog' | 'organic'
export type Logistics = 'full' | 'mercado_envios'
export type AdType = 'classic' | 'premium'
export type Verdict = 'approved' | 'rejected'

export interface Session {
  id: string
  supplier_name: string
  pdf_filename: string
  tax_rate: number
  status: SessionStatus
  created_at: string
  finished_at: string | null
  product_count?: number
  product_status_counts?: Record<string, number>
  batches?: Batch[]
}

export interface Batch {
  id: string
  batch_number: number
  status: BatchStatus
  product_count?: number
  product_status_counts?: Record<string, number>
  scheduled_at: string
  started_at: string | null
  finished_at: string | null
}

export interface Product {
  id: string
  session_id: string
  batch_id: string | null
  catalog_name: string
  description: string | null
  cost_price: number
  units_per_box: number | null
  weight_kg: number | null
  dimensions_cm: { length: number; width: number; height: number } | null
  search_terms: string[]
  best_search_term: string | null
  status: ProductStatus
  batch_number: number | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface Listing {
  id: string
  ml_item_id: string
  title: string
  price: number
  thumbnail_url: string | null
  listing_type: ListingType
  logistics: Logistics
  ad_type: AdType
  sales_tag: number | null
  listing_age_days: number | null
  search_position: number | null
  estimated_visits_7d: number | null
  sales_per_day_est: number | null
  selected_by_user: boolean
}

export interface ListingsResponse {
  catalog: Listing[]
  organic: Listing[]
}

export interface Analysis {
  id: string
  logistics_mode: Logistics
  ad_type: AdType
  suggested_price: number
  min_competitor_price: number | null
  max_competitor_price: number | null
  ml_commission_rate: number
  shipping_cost: number
  tax_cost: number
  total_cost: number
  margin_ranking: number
  margin_post_ranking: number
  verdict: Verdict
  rejection_reason: string | null
  calculated_at: string
}

export interface Notification {
  id: string
  type: string
  title: string
  body: string
  read: boolean
  created_at: string
}
