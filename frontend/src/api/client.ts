const BASE_URL = import.meta.env.VITE_API_URL ?? '/api/v1'

let authToken: string | null = null

export function setToken(token: string) {
  authToken = token
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`
  }

  const resp = await fetch(`${BASE_URL}${path}`, { ...options, headers })

  if (resp.status === 402) {
    const data = await resp.json()
    throw Object.assign(new Error('paywall'), { paywall: true, detail: data })
  }

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }))
    throw new Error(err.detail || `HTTP ${resp.status}`)
  }

  return resp.json() as Promise<T>
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}
