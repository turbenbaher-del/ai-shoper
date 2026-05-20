import React, { useEffect, useState } from 'react'
import { Welcome } from './screens/Welcome'
import { Quiz } from './screens/Quiz'
import { Home } from './screens/Home'
import { Input } from './screens/Input'
import { Processing } from './screens/Processing'
import { Results } from './screens/Results'
import { Tracked } from './screens/Tracked'
import { PaywallScreen } from './screens/PaywallScreen'
import { ErrorBoundary } from './components/ErrorBoundary'
import { useTelegram } from './hooks/useTelegram'
import { authTelegram } from './api/auth'
import { setToken, api } from './api/client'
import { useAppStore } from './store/appStore'

function AppInner() {
  const { screen, setScreen, setUser, setToken: storeSetToken, user } = useAppStore()
  const { ready, initData, isInTelegram } = useTelegram()
  const [authError, setAuthError] = useState<string | null>(null)

  useEffect(() => {
    if (!ready) return

    async function init() {
      try {
        const data = initData || 'dev_mode'
        const { user: u, token } = await authTelegram(data)
        setToken(token)
        storeSetToken(token)
        setUser(u)
        // Сброс счётчика поисков на период тестирования
        api.post('/search/reset-limit', {}).catch(() => {})
        setScreen(u.quiz_completed ? 'home' : 'welcome')
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e)
        console.error('Auth failed:', msg)
        if (initData) {
          // In Telegram: auth should always work — show error instead of silently proceeding
          setAuthError(msg)
        } else {
          // Dev mode without Telegram: continue without auth
          setScreen('welcome')
        }
      }
    }

    init()
  }, [ready])

  const screenMap = {
    welcome: <Welcome />,
    quiz: <Quiz />,
    home: <Home />,
    input: <Input />,
    processing: <Processing />,
    results: <Results />,
    tracked: <Tracked />,
    paywall: <PaywallScreen />,
  }

  // Paywall отключён на время тестирования — редиректим на home
  const activeScreen = screen === 'paywall' ? 'home' : screen

  if (authError) {
    return (
      <div style={{ height: '100dvh', background: 'var(--bg)', color: 'var(--text)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 24, gap: 16 }}>
        <i className="ti ti-alert-triangle" style={{ fontSize: 48, color: 'var(--red)' }} />
        <div style={{ textAlign: 'center', fontSize: 16 }}>Ошибка авторизации</div>
        <div style={{ textAlign: 'center', fontSize: 13, color: 'var(--text-mute)' }}>{authError}</div>
        <button
          onClick={() => { setAuthError(null); window.location.reload() }}
          style={{ background: 'var(--accent)', color: '#fff', border: 'none', borderRadius: 12, padding: '12px 24px', fontSize: 15, cursor: 'pointer' }}
        >
          Попробовать снова
        </button>
      </div>
    )
  }

  return (
    <div
      style={{
        height: '100dvh',
        background: 'var(--bg)',
        color: 'var(--text)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {screenMap[activeScreen]}
    </div>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <AppInner />
    </ErrorBoundary>
  )
}
