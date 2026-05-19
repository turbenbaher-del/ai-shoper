import { useEffect, useState } from 'react'

declare global {
  interface Window {
    Telegram?: {
      WebApp: {
        initData: string
        initDataUnsafe: {
          user?: {
            id: number
            first_name: string
            username?: string
            language_code?: string
          }
        }
        ready: () => void
        expand: () => void
        close: () => void
        BackButton: {
          show: () => void
          hide: () => void
          onClick: (fn: () => void) => void
          offClick: (fn: () => void) => void
        }
        MainButton: {
          setText: (text: string) => void
          show: () => void
          hide: () => void
          onClick: (fn: () => void) => void
        }
        colorScheme: 'light' | 'dark'
        themeParams: Record<string, string>
        isExpanded: boolean
      }
    }
  }
}

export function useTelegram() {
  const tg = window.Telegram?.WebApp
  const [ready, setReady] = useState(false)

  useEffect(() => {
    if (tg) {
      tg.ready()
      tg.expand()
      setReady(true)
    } else {
      // В браузере без TG — режим разработки
      setReady(true)
    }
  }, [tg])

  return {
    tg,
    ready,
    initData: tg?.initData ?? '',
    user: tg?.initDataUnsafe?.user,
    isInTelegram: !!tg,
  }
}
