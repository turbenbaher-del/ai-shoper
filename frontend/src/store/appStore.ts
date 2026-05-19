import { create } from 'zustand'

export type Screen =
  | 'welcome'
  | 'quiz'
  | 'home'
  | 'input'
  | 'processing'
  | 'results'
  | 'tracked'
  | 'paywall'

export interface ProductPrice {
  marketplace: string
  price: number
  url: string
  is_best: boolean
}

export interface Product {
  rank: number
  name: string
  image_url: string | null
  reason: string
  prices: ProductPrice[]
  sku: string
  marketplace: string
}

export interface SearchResult {
  query_id: number
  query: string
  title: string
  subtitle: string
  products: Product[]
  share_text: string
  processing_time_seconds: number
}

export interface User {
  id: number
  tg_user_id: number
  tg_username: string | null
  tg_first_name: string | null
  quiz_completed: boolean
  is_premium: boolean
  premium_until: string | null
  free_searches_used: number
  push_consent: boolean
}

interface AppState {
  screen: Screen
  token: string | null
  user: User | null
  searchResult: SearchResult | null
  currentQuery: string

  setScreen: (s: Screen) => void
  setToken: (t: string) => void
  setUser: (u: User) => void
  setSearchResult: (r: SearchResult | null) => void
  setCurrentQuery: (q: string) => void
}

export const useAppStore = create<AppState>((set) => ({
  screen: 'welcome',
  token: null,
  user: null,
  searchResult: null,
  currentQuery: '',

  setScreen: (screen) => set({ screen }),
  setToken: (token) => set({ token }),
  setUser: (user) => set({ user }),
  setSearchResult: (searchResult) => set({ searchResult }),
  setCurrentQuery: (currentQuery) => set({ currentQuery }),
}))
