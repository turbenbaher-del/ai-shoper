import React from 'react'
import { Paywall } from '../components/Paywall'
import { useAppStore } from '../store/appStore'

export function PaywallScreen() {
  const { setScreen, setUser, user } = useAppStore()

  function handleSuccess() {
    if (user) {
      setUser({ ...user, is_premium: true })
    }
    setScreen('home')
  }

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: '24px 16px 32px' }}>
      <button
        onClick={() => setScreen('home')}
        style={{
          background: 'none',
          border: 'none',
          color: 'var(--text-mute)',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          fontSize: 14,
          marginBottom: 24,
          fontFamily: 'inherit',
        }}
      >
        <i className="ti ti-arrow-left" style={{ fontSize: 18 }} />
        Назад
      </button>

      <Paywall onClose={() => setScreen('home')} onSuccess={handleSuccess} />
    </div>
  )
}
