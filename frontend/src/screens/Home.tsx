import React from 'react'
import { Button } from '../components/Button'
import { useAppStore } from '../store/appStore'

export function Home() {
  const { setScreen, user } = useAppStore()
  const name = user?.tg_first_name ?? 'друг'
  const used = user?.free_searches_used ?? 0
  const FREE_LIMIT = 3

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', padding: '24px 20px' }}>
      {/* Шапка */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
        <div>
          <div className="text-caption text-mute">Привет,</div>
          <div className="text-h2">{name}</div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => setScreen('tracked')}
            style={{
              width: 40,
              height: 40,
              background: 'var(--bg-raised)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--r-md)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              color: 'var(--text)',
            }}
          >
            <i className="ti ti-bell" style={{ fontSize: 20 }} />
          </button>
        </div>
      </div>

      {/* Главный CTA */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 32,
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <h1 className="text-h1" style={{ marginBottom: 8 }}>Что найти?</h1>
          <p className="text-body text-mute">
            Опиши товар голосом или текстом — найду лучшее за 30 секунд
          </p>
        </div>

        <Button
          variant="primary"
          size="lg"
          onClick={() => setScreen('input')}
          icon={<i className="ti ti-search" style={{ fontSize: 20 }} />}
          style={{ width: 200 }}
        >
          Поиск
        </Button>

        {/* Счётчик запросов */}
        {!user?.is_premium && (
          <div
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--r-md)',
              padding: '12px 16px',
              textAlign: 'center',
              width: '100%',
            }}
          >
            <div className="text-caption text-mute" style={{ marginBottom: 8 }}>
              Бесплатных поисков в этом месяце
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginBottom: 8 }}>
              {Array.from({ length: FREE_LIMIT }).map((_, i) => (
                <div
                  key={i}
                  style={{
                    width: 40,
                    height: 6,
                    borderRadius: 'var(--r-full)',
                    background: i < used ? 'var(--text-dim)' : 'var(--accent)',
                    transition: `background var(--t-base) var(--ease)`,
                  }}
                />
              ))}
            </div>
            <div className="text-caption text-dim">
              {FREE_LIMIT - used} из {FREE_LIMIT} осталось
            </div>
          </div>
        )}
      </div>

      {/* Быстрые примеры */}
      <div>
        <div className="text-caption text-mute" style={{ marginBottom: 10 }}>Примеры запросов</div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {[
            'Робот-пылесос до 30к',
            'Наушники с ANC',
            'Кофемашина для офиса',
          ].map((example) => (
            <button
              key={example}
              onClick={() => {
                useAppStore.getState().setCurrentQuery(example)
                setScreen('input')
              }}
              style={{
                background: 'var(--bg-raised)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--r-full)',
                padding: '6px 12px',
                fontSize: 12,
                color: 'var(--text-mute)',
                cursor: 'pointer',
                fontFamily: 'inherit',
              }}
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
