import { api } from './client'
import type { SearchResult } from '../store/appStore'

export async function search(query: string): Promise<SearchResult> {
  return api.post<SearchResult>('/search', { query })
}

export async function getHistory(): Promise<SearchResult[]> {
  return api.get<SearchResult[]>('/search/history?limit=20')
}

export async function trackShare(queryId: number): Promise<void> {
  await api.post(`/search/${queryId}/share`, {})
}
