import React, { useEffect, useState } from 'react'
import { getTracked, removeTracked } from '../api/tracked'
import type { TrackedItem } from '../api/tracked'
import { EmptyState } from '../components/EmptyState'
import { useAppStore } from '../store/appStore'

function PriceBar({ initial, current }: { initial: number; current: number }) {
  const diff = current - initial
  const pct = Math.round((diff / initial) * 100)
  const isDown = diff < 0
  return (
    <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
      <span className="text-body tabular-nums" style={{ fontWeight: 600 }}>
        {current.toLocaleString('ru-RU')} ₽
      </span>
      {diff !== 0 && (
        <span
          className="text-caption"
          style={{ color: isDown ? 'var(--green)' : 'var(--red)' }}
        >
          {isDown ? '' : '+'}{pct}%
        </span>
      )}
    </div>
  )
}

export function Tracked() {
  const setScreen = useAppStore((s) => s.setScreen)
  const [items, setItems] = useState<TrackedItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [removing, setRemoving] = useState<number | null>(null)

  useEffect(() => {
    getTracked()
      .then(setItems)
      .catch(() => setError('Не удалось загрузить список. Попробуй позже.'))
      .finally(() => setLoading(false))
  }, [])

  async function handleRemove(id: number) {
    setRemoving(id)
    try {
      await removeTracked(id)
      setItems((prev) => prev.filter((i) => i.id !== id))
    } catch {
      setError('Не удалось удалить. Попробуй снова.')
    } finally {
      setRemoving(null)
    }
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Шапка */}
      <div style={{ padding: '20px 16px 16px', display: 'flex', alignItems: 'center', gap: 12 }}>
        <button
          onClick={() => setScreen('home')}
          style={{ background: 'none', border: 'none', color: 'var(--text-mute)', cursor: 'pointer' }}
        >
          <i className="ti ti-arrow-left" style={{ fontSize: 20 }} />
        </button>
        <h2 className="text-h2">Отслеживаю цены</h2>
      </div>

      {error && (
        <div style={{ margin: '0 16px 8px', padding: '10px 12px', background: 'rgba(255,60,60,.12)', borderRadius: 'var(--r-md)', display: 'flex', alignItems: 'center', gap: 8 }}>
          <i className="ti ti-alert-circle" style={{ color: 'var(--red)', fontSize: 16, flexShrink: 0 }} />
          <span className="text-caption" style={{ color: 'var(--red)' }}>{error}</span>
          <button onClick={() => setError(null)} style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--red)' }}>
            <i className="ti ti-x" style={{ fontSize: 14 }} />
          </button>
        </div>
      )}

      {loading ? (
        <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 12 }}>
          {[1, 2, 3].map((i) => (
            <div key={i} className="skeleton" style={{ height: 80, borderRadius: 'var(--r-lg)' }} />
          ))}
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          icon="ti-bell-off"
          title="Нет отслеживаемых товаров"
          description="Добавь товар из результатов поиска — оповещу когда подешевеет"
          action={{ label: 'Найти товар', onClick: () => setScreen('input') }}
        />
      ) : (
        <div style={{ flex: 1, overflowY: 'auto', padding: '0 16px 24px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {items.map((item) => (
              <div
                key={item.id}
                style={{
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--r-lg)',
                  padding: 16,
                  display: 'flex',
                  gap: 12,
                }}
              >
                {/* Изображение */}
                <div
                  style={{
                    width: 56,
                    height: 56,
                    background: 'var(--bg-raised)',
                    borderRadius: 'var(--r-md)',
                    flexShrink: 0,
                    overflow: 'hidden',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {item.image_url ? (
                    <img src={item.image_url} alt={item.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  ) : (
                    <i className="ti ti-photo" style={{ fontSize: 24, color: 'var(--text-dim)' }} />
                  )}
                </div>

                {/* Инфо */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    className="text-body"
                    style={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginBottom: 4 }}
                  >
                    {item.name}
                  </div>
                  <div className="text-caption text-mute" style={{ marginBottom: 6, textTransform: 'capitalize' }}>
                    {item.marketplace.replace('_', ' ')}
                  </div>
                  <PriceBar initial={item.initial_price} current={item.current_price} />
                </div>

                {/* Удалить */}
                <button
                  onClick={() => handleRemove(item.id)}
                  disabled={removing === item.id}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: removing === item.id ? 'var(--text-dim)' : 'var(--text-dim)',
                    cursor: removing === item.id ? 'default' : 'pointer',
                    flexShrink: 0,
                    alignSelf: 'flex-start',
                    opacity: removing === item.id ? 0.4 : 1,
                  }}
                >
                  <i className={removing === item.id ? 'ti ti-loader-2' : 'ti ti-x'} style={{ fontSize: 18 }} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
