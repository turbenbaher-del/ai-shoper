import React, { useState } from 'react'
import { Badge } from './Badge'
import { Button } from './Button'
import { api } from '../api/client'

interface PaywallProps {
  onClose?: () => void
  onSuccess?: () => void
}

const PLANS = [
  {
    id: 'year',
    label: 'Год',
    sub: '≈ 408 ₽/мес',
    price: '4 900 ₽',
    discount: 'Скидка 31%',
  },
  {
    id: 'month',
    label: 'Месяц',
    sub: 'Отмена в любой момент',
    price: '590 ₽',
    discount: null,
  },
]

const FEATURES = [
  'Безлимитные поиски',
  'Отслеживание цен без лимита',
  'История запросов навсегда',
  'Приоритетные уведомления',
]

export function Paywall({ onClose, onSuccess }: PaywallProps) {
  const [selectedPlan, setSelectedPlan] = useState('year')
  const [loading, setLoading] = useState(false)

  async function handleStart() {
    setLoading(true)
    try {
      const res = await api.post<{ redirect_url?: string; ok?: boolean }>(
        '/subscription/start',
        { plan: selectedPlan }
      )
      if (res.redirect_url) {
        window.open(res.redirect_url, '_blank')
      } else if (res.ok) {
        onSuccess?.()
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--accent)',
        borderRadius: 'var(--r-xl)',
        padding: 24,
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Декоративный градиент */}
      <div
        style={{
          position: 'absolute',
          top: -100,
          right: -100,
          width: 240,
          height: 240,
          background: 'radial-gradient(circle, var(--accent-soft) 0%, transparent 70%)',
          pointerEvents: 'none',
        }}
      />

      <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', gap: 16 }}>
        <Badge variant="accent" icon={<i className="ti ti-bolt" style={{ fontSize: 12 }} />}>
          Premium
        </Badge>

        <div style={{ fontSize: 22, fontWeight: 700 }}>
          Безлимитный поиск
        </div>
        <div className="text-body text-mute">
          3 поиска в месяц закончились. Получи Premium и ищи без ограничений.
        </div>

        {/* Фичи */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {FEATURES.map((f) => (
            <div key={f} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <i className="ti ti-check" style={{ fontSize: 18, color: 'var(--accent)' }} />
              <span className="text-body">{f}</span>
            </div>
          ))}
        </div>

        {/* Тарифы */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {PLANS.map((plan) => (
            <div
              key={plan.id}
              onClick={() => setSelectedPlan(plan.id)}
              style={{
                border: `1px solid ${selectedPlan === plan.id ? 'var(--accent)' : 'var(--border)'}`,
                background: selectedPlan === plan.id ? 'var(--accent-soft)' : 'transparent',
                padding: '14px 16px',
                borderRadius: 'var(--r-md)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                cursor: 'pointer',
                transition: `all var(--t-base) var(--ease)`,
              }}
            >
              <div>
                <div className="text-body" style={{ fontWeight: 500 }}>{plan.label}</div>
                <div className="text-caption text-mute">{plan.sub}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div className="tabular-nums" style={{ fontSize: 16, fontWeight: 600 }}>{plan.price}</div>
                {plan.discount && (
                  <div style={{ fontSize: 11, color: 'var(--accent)' }}>{plan.discount}</div>
                )}
              </div>
            </div>
          ))}
        </div>

        <Button variant="primary" size="lg" block loading={loading} onClick={handleStart}>
          7 дней бесплатно
        </Button>

        <div className="text-caption text-dim" style={{ textAlign: 'center' }}>
          Отмена в любой момент
        </div>

        {onClose && (
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-mute)',
              fontSize: 14,
              cursor: 'pointer',
              textAlign: 'center',
            }}
          >
            Не сейчас
          </button>
        )}
      </div>
    </div>
  )
}
