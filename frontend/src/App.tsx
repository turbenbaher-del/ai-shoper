import React, { useEffect } from 'react'
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
import { setToken } from './api/client'
import { useAppStore } from './store/appStore'

function AppInner() {
  const { screen, setScreen, setUser, setToken: storeSetToken, user } = useAppStore()
  const { ready, initData, isInTelegram } = useTelegram()

  useEffect(() => {
    if (!ready) return

    async function init() {
      try {
        const data = initData || 'dev_mode'
        const { user: u, token } = await authTelegram(data)
        setToken(token)
        storeSetToken(token)
        setUser(u)
        setScreen(u.quiz_completed ? 'home' : 'welcome')
      } catch (e) {
        console.error('Auth failed:', e)
        // В dev-режиме продолжаем без авторизации
        setScreen('welcome')
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
      {screenMap[screen]}
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
