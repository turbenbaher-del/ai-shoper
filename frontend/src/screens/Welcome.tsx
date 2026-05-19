import React, { useState } from 'react'
import { Button } from '../components/Button'
import { api } from '../api/client'
import { useAppStore } from '../store/appStore'

export function Welcome() {
  const setScreen = useAppStore((s) => s.setScreen)
  const [consent, setConsent] = useState(false)

  async function handleStart() {
    if (!consent) return
    try {
      await api.post('/auth/consent', {})
    } catch {
      // Не блокируем если запрос упал
    }
    setScreen('quiz')
  }

  return (
    <div
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        padding: '48px 24px 32px',
      }}
    >
      {/* Hero */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', gap: 24 }}>
        <div
          style={{
            width: 80,
            height: 80,
            background: 'var(--accent-soft)',
            borderRadius: 'var(--r-xl)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <i className="ti ti-shopping-cart" style={{ fontSize: 40, color: 'var(--accent)' }} />
        </div>

        <div>
          <h1 className="text-h1" style={{ marginBottom: 12 }}>
            Найду лучший товар за 30 секунд
          </h1>
          <p className="text-body text-mute">
            Говори что нужно — найду на Ozon, Wildberries и Я.Маркет, прочитаю отзывы и покажу топ-3
          </p>
        </div>

        {/* Фичи */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, width: '100%', textAlign: 'left' }}>
          {[
            { icon: 'ti-bolt', text: 'Сравниваю цены на 3 маркетплейсах' },
            { icon: 'ti-shield-check', text: 'Отсекаю накрученные отзывы' },
            { icon: 'ti-bell', text: 'Слежу за ценами и оповещаю' },
          ].map(({ icon, text }) => (
            <div key={text} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div
                style={{
                  width: 36,
                  height: 36,
                  background: 'var(--bg-raised)',
                  borderRadius: 'var(--r-md)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                <i className={`ti ${icon}`} style={{ fontSize: 18, color: 'var(--accent)' }} />
              </div>
              <span className="text-body">{text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* CTA */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {/* PDN согласие (ТЗ раздел 8) */}
        <label
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: 10,
            cursor: 'pointer',
          }}
        >
          <div
            onClick={() => setConsent((v) => !v)}
            style={{
              width: 20,
              height: 20,
              borderRadius: 4,
              border: `2px solid ${consent ? 'var(--accent)' : 'var(--border)'}`,
              background: consent ? 'var(--accent)' : 'transparent',
              flexShrink: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginTop: 1,
              transition: 'all var(--t-base) var(--ease)',
            }}
          >
            {consent && <i className="ti ti-check" style={{ fontSize: 12, color: 'var(--bg)' }} />}
          </div>
          <span className="text-caption text-mute">
            Соглашаюсь с{' '}
            <a href="#" style={{ color: 'var(--accent)' }}>офертой</a> и{' '}
            <a href="#" style={{ color: 'var(--accent)' }}>политикой конфиденциальности</a>
          </span>
        </label>

        <Button variant="primary" size="lg" block disabled={!consent} onClick={handleStart}>
          Начать
        </Button>
        <div className="text-caption text-dim" style={{ textAlign: 'center' }}>
          3 поиска бесплатно каждый месяц
        </div>
      </div>
    </div>
  )
}
