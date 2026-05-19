import { api } from './client'

export interface TrackedItem {
  id: number
  marketplace: string
  sku: string
  name: string
  url: string
  image_url: string | null
  initial_price: number
  current_price: number
  last_checked_at: string
  alert_threshold_pct: number
  is_active: boolean
  created_at: string
}

export interface PricePoint {
  price: number
  captured_at: string
}

export async function getTracked(): Promise<TrackedItem[]> {
  return api.get<TrackedItem[]>('/tracked')
}

export async function addTracked(data: {
  marketplace: string
  sku: string
  name: string
  url: string
  image_url?: string | null
  initial_price: number
}): Promise<TrackedItem> {
  return api.post<TrackedItem>('/tracked', data)
}

export async function removeTracked(id: number): Promise<void> {
  await api.delete(`/tracked/${id}`)
}

export async function getPriceHistory(id: number): Promise<PricePoint[]> {
  return api.get<PricePoint[]>(`/tracked/${id}/history`)
}
