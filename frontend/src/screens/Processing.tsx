import React, { useEffect, useState } from 'react'
import { LoadingStages } from '../components/LoadingStages'
import { search } from '../api/search'
import { useAppStore } from '../store/appStore'

const STAGE_LABELS = [
  'Понимаю запрос',
  'Сканирую Ozon',
  'Сканирую Wildberries',
  'Сканирую Я.Маркет',
  'Анализирую отзывы и ранжирую',
]

export function Processing() {
  const { currentQuery, setScreen, setSearchResult } = useAppStore()
  const [activeStage, setActiveStage] = useState(0)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let stageTimer: ReturnType<typeof setInterval>

    // Двигаем прогресс-бар пока идёт запрос
    stageTimer = setInterval(() => {
      setActiveStage((s) => {
        if (s < STAGE_LABELS.length - 1) return s + 1
        clearInterval(stageTimer)
        return s
      })
    }, 2500)

    search(currentQuery)
      .then((result) => {
        clearInterval(stageTimer)
        setSearchResult(result)
        setScreen('results')
      })
      .catch((err) => {
        clearInterval(stageTimer)
        if (err.paywall) {
          setScreen('paywall')
        } else {
          setError(err.message ?? 'Что-то пошло не так. Попробуй ещё раз.')
        }
      })

    return () => clearInterval(stageTimer)
  }, [])

  const stages = STAGE_LABELS.map((label, i) => ({
    label,
    status: i < activeStage ? 'done' : i === activeStage ? 'active' : 'pending',
  })) as Parameters<typeof LoadingStages>[0]['stages']

  if (error) {
    return (
      <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 24, gap: 16 }}>
        <i className="ti ti-alert-triangle" style={{ fontSize: 48, color: 'var(--red)' }} />
        <div className="text-body" style={{ textAlign: 'center' }}>{error}</div>
        <button
          onClick={() => setScreen('input')}
          style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontSize: 14 }}
        >
          Попробовать снова
        </button>
      </div>
    )
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', padding: '48px 20px 24px' }}>
      <div style={{ textAlign: 'center', marginBottom: 40 }}>
        <div className="text-h2" style={{ marginBottom: 8 }}>Ищу для тебя</div>
        <div className="text-body text-mute">"{currentQuery}"</div>
      </div>

      <LoadingStages stages={stages} />

      <div style={{ flex: 1 }} />

      <div className="text-caption text-dim" style={{ textAlign: 'center' }}>
        Обычно занимает 15-30 секунд
      </div>
    </div>
  )
}
