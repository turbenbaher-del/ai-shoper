import React, { useState } from 'react'
import { ProductCard } from '../components/ProductCard'
import { EmptyState } from '../components/EmptyState'
import { BottomSheet } from '../components/BottomSheet'
import { Button } from '../components/Button'
import { addTracked } from '../api/tracked'
import { trackShare } from '../api/search'
import { useAppStore } from '../store/appStore'
import type { Product } from '../store/appStore'

export function Results() {
  const { searchResult, setScreen } = useAppStore()
  const [trackingProduct, setTrackingProduct] = useState<Product | null>(null)
  const [tracked, setTracked] = useState(false)

  if (!searchResult || searchResult.products.length === 0) {
    return (
      <EmptyState
        icon="ti-search-off"
        title="Ничего не нашли"
        description="Попробуй изменить запрос или выбрать другую категорию"
        action={{ label: 'Новый поиск', onClick: () => setScreen('input') }}
      />
    )
  }

  async function handleTrack(product: Product) {
    setTrackingProduct(product)
  }

  async function confirmTrack() {
    if (!trackingProduct || !searchResult) return
    const bestPrice = trackingProduct.prices.find((p) => p.is_best) ?? trackingProduct.prices[0]
    try {
      await addTracked({
        marketplace: trackingProduct.marketplace,
        sku: trackingProduct.sku,
        name: trackingProduct.name,
        url: bestPrice?.url ?? '',
        image_url: trackingProduct.image_url,
        initial_price: bestPrice?.price ?? 0,
      })
      setTracked(true)
    } catch {
      // paywall обрабатывается глобально
    }
    setTrackingProduct(null)
  }

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: '16px 16px 32px' }}>
      {/* Шапка */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
          <h1 className="text-h2">{searchResult.title}</h1>
          <button
            onClick={() => setScreen('input')}
            style={{ background: 'none', border: 'none', color: 'var(--text-mute)', cursor: 'pointer' }}
          >
            <i className="ti ti-x" style={{ fontSize: 20 }} />
          </button>
        </div>
        <div className="text-caption text-mute">{searchResult.subtitle}</div>
      </div>

      {/* Карточки */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {searchResult.products.map((product) => (
          <ProductCard
            key={`${product.rank}-${product.sku}`}
            product={product}
            queryId={searchResult.query_id}
            onTrack={handleTrack}
          />
        ))}
      </div>

      {/* Действия */}
      <div style={{ marginTop: 24, display: 'flex', gap: 8 }}>
        <Button variant="secondary" size="md" block onClick={() => setScreen('input')}>
          <i className="ti ti-search" style={{ fontSize: 18 }} />
          Новый поиск
        </Button>
        {searchResult.share_text && (
          <Button
            variant="secondary"
            size="md"
            onClick={async () => {
              if (searchResult.query_id) {
                trackShare(searchResult.query_id).catch(() => {})
              }
              if (navigator.share) {
                navigator.share({ text: searchResult.share_text }).catch(() => {})
              } else {
                navigator.clipboard?.writeText(searchResult.share_text).catch(() => {})
              }
            }}
            style={{ flexShrink: 0 }}
          >
            <i className="ti ti-share" style={{ fontSize: 18 }} />
          </Button>
        )}
      </div>

      {/* Bottom sheet для подтверждения отслеживания */}
      <BottomSheet
        open={!!trackingProduct}
        title="Следить за ценой"
        onClose={() => setTrackingProduct(null)}
      >
        {trackingProduct && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div className="text-body">{trackingProduct.name}</div>
            <div className="text-caption text-mute">
              Пришлю уведомление когда цена снизится на 5% или больше
            </div>
            <Button variant="primary" size="md" block onClick={confirmTrack}>
              <i className="ti ti-bell" style={{ fontSize: 18 }} />
              Следить
            </Button>
          </div>
        )}
      </BottomSheet>
    </div>
  )
}
