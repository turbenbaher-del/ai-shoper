import { api } from './client'
import type { User } from '../store/appStore'

export interface AuthResponse {
  user: User
  token: string
  is_new: boolean
}

export async function authTelegram(initData: string): Promise<AuthResponse> {
  return api.post<AuthResponse>('/auth/telegram', { init_data: initData })
}

export async function saveQuiz(data: {
  who: string
  marketplaces: string[]
  priority: string
  categories: string[]
  city?: string
}): Promise<void> {
  await api.post('/quiz', data)
}
