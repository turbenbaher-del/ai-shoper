import React from 'react'
import { Badge } from './Badge'
import { Button } from './Button'
import type { Product } from '../store/appStore'

const RANK_MEDALS = ['🥇', '🥈', '🥉']
const RANK_LABELS = ['Лучший', 'Хороший', 'Вариант']

interface ProductCardProps {
  product: Product
  queryId: number
  onTrack?: (product: Product) => void
}

export function ProductCard({ product, queryId, onTrack }: ProductCardProps) {
  const isWinner = product.rank === 1
  const medal = RANK_MEDALS[product.rank - 1] ?? ''
  const rankLabel = RANK_LABELS[product.rank - 1] ?? ''

  const bestPrice = product.prices.find((p) => p.is_best)

  function handleBuy() {
    const clickUrl = `/api/v1/search/${queryId}/${product.rank - 1}/click`
    window.open(clickUrl, '_blank')
  }

  function handleShare() {
    if (navigator.share) {
      navigator.share({ text: `${product.name}\n${bestPrice?.url ?? ''}` })
    }
  }

  return (
    <div
      style={{
        background: isWinner
          ? 'linear-gradient(180deg, rgba(0, 217, 166, 0.04) 0%, var(--bg-surface) 100%)'
          : 'var(--bg-surface)',
        border: `1px solid ${isWinner ? 'var(--accent)' : 'var(--border)'}`,
        borderRadius: 'var(--r-lg)',
        padding: 16,
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 20 }}>{medal}</span>
          <span className="text-body" style={{ fontWeight: 600 }}>{rankLabel}</span>
        </div>
        {isWinner && <Badge variant="success">Проверен</Badge>}
      </div>

      {/* Изображение */}
      <div
        style={{
          background: 'var(--bg-raised)',
          borderRadius: 'var(--r-md)',
          aspectRatio: '4/3',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden',
        }}
      >
        {product.image_url ? (
          <img src={product.image_url} alt={product.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        ) : (
          <i className="ti ti-photo" style={{ fontSize: 32, color: 'var(--text-dim)' }} />
        )}
      </div>

      {/* Название */}
      <div className="text-body-l" style={{ fontWeight: 600, lineHeight: 1.35 }}>
        {product.name}
      </div>

      {/* Причина выбора */}
      <div className="text-caption text-mute">
        {product.reason}
      </div>

      {/* Блок цен */}
      <div
        style={{
          background: 'var(--bg)',
          borderRadius: 'var(--r-md)',
          padding: '10px',
          display: 'flex',
          flexDirection: 'column',
          gap: 6,
        }}
      >
        {product.prices.map((p) => (
          <div key={p.marketplace} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="text-caption text-mute" style={{ textTransform: 'capitalize' }}>
              {p.marketplace.replace('_', ' ')}
            </span>
            <span
              className="tabular-nums"
              style={{
                fontSize: p.is_best ? 14 : 12,
                fontWeight: p.is_best ? 600 : 500,
                color: p.is_best ? 'var(--accent)' : 'var(--text)',
              }}
            >
              {p.price.toLocaleString('ru-RU')} ₽
            </span>
          </div>
        ))}
      </div>

      {/* Кнопки действий */}
      <div style={{ display: 'flex', gap: 8 }}>
        <Button variant="primary" size="sm" onClick={handleBuy} style={{ flex: 1 }}>
          <i className="ti ti-external-link" style={{ fontSize: 16 }} />
          Купить
        </Button>
        <Button variant="secondary" size="sm" onClick={handleShare} style={{ width: 36, padding: 0 }}>
          <i className="ti ti-share" style={{ fontSize: 18 }} />
        </Button>
        {onTrack && (
          <Button variant="secondary" size="sm" onClick={() => onTrack(product)} style={{ width: 36, padding: 0 }}>
            <i className="ti ti-bell" style={{ fontSize: 18 }} />
          </Button>
        )}
      </div>
    </div>
  )
}
