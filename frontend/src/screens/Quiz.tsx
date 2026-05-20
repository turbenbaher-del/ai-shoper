import React, { useState } from 'react'
import { Button } from '../components/Button'
import { saveQuiz } from '../api/auth'
import { useAppStore } from '../store/appStore'

const CHOICE_STEPS = [
  {
    id: 'who',
    question: 'Для кого ищем?',
    type: 'single',
    options: ['Для себя', 'Для семьи', 'В подарок', 'Для работы'],
  },
  {
    id: 'marketplaces',
    question: 'Какие маркетплейсы предпочитаешь?',
    type: 'multi',
    options: ['Ozon', 'Wildberries', 'Я.Маркет'],
  },
  {
    id: 'priority',
    question: 'Что важнее при выборе?',
    type: 'single',
    options: ['Цена', 'Качество', 'Быстрая доставка', 'Известный бренд'],
  },
  {
    id: 'categories',
    question: 'Что обычно покупаешь?',
    type: 'multi',
    options: ['Электроника', 'Бытовая техника', 'Одежда', 'Спорт', 'Дом и сад'],
  },
]

const TOTAL_STEPS = CHOICE_STEPS.length + 1 // +1 для города

const POPULAR_CITIES = [
  'Москва', 'Санкт-Петербург', 'Новосибирск', 'Екатеринбург', 'Казань',
  'Ростов-на-Дону', 'Краснодар', 'Нижний Новгород', 'Самара', 'Омск',
  'Уфа', 'Красноярск', 'Воронеж', 'Пермь', 'Волгоград', 'Саратов',
  'Тюмень', 'Тольятти', 'Ижевск', 'Барнаул', 'Ульяновск', 'Иркутск',
  'Хабаровск', 'Владивосток', 'Ярославль', 'Махачкала', 'Томск',
  'Оренбург', 'Кемерово', 'Рязань', 'Астрахань', 'Набережные Челны',
  'Пенза', 'Липецк', 'Тула', 'Киров', 'Чебоксары', 'Калининград',
  'Брянск', 'Курск', 'Магнитогорск', 'Сочи', 'Белгород', 'Сургут',
]

async function detectCity(): Promise<string> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) { reject(new Error('no geo')); return }
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const { latitude, longitude } = pos.coords
          const res = await fetch(
            `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json&accept-language=ru`,
            { headers: { 'User-Agent': 'ai-shoper-app' } }
          )
          const data = await res.json()
          const city = data.address?.city || data.address?.town || data.address?.village || data.address?.county || ''
          resolve(city)
        } catch { reject(new Error('geocode failed')) }
      },
      (err) => reject(err),
      { timeout: 8000 }
    )
  })
}

export function Quiz() {
  const { setScreen, setUser, user } = useAppStore()
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({})
  const [city, setCity] = useState('')
  const [loading, setLoading] = useState(false)
  const [geoLoading, setGeoLoading] = useState(false)
  const [geoError, setGeoError] = useState('')

  const isCityStep = step === CHOICE_STEPS.length
  const currentStep = isCityStep ? null : CHOICE_STEPS[step]

  const filteredCities = city.length >= 2
    ? POPULAR_CITIES.filter(c => c.toLowerCase().includes(city.toLowerCase()) && c.toLowerCase() !== city.toLowerCase())
    : []

  async function handleDetectCity() {
    setGeoLoading(true)
    setGeoError('')
    try {
      const detected = await detectCity()
      if (detected) setCity(detected)
      else setGeoError('Не удалось определить город')
    } catch {
      setGeoError('Нет доступа к геолокации')
    } finally {
      setGeoLoading(false)
    }
  }

  function toggleOption(option: string) {
    if (!currentStep) return
    const key = currentStep.id
    if (currentStep.type === 'single') {
      setAnswers((prev) => ({ ...prev, [key]: option }))
    } else {
      const current = (answers[key] as string[]) ?? []
      const next = current.includes(option)
        ? current.filter((o) => o !== option)
        : [...current, option]
      setAnswers((prev) => ({ ...prev, [key]: next }))
    }
  }

  function isSelected(option: string) {
    if (!currentStep) return false
    const val = answers[currentStep.id]
    if (!val) return false
    if (Array.isArray(val)) return val.includes(option)
    return val === option
  }

  function canNext() {
    if (isCityStep) return true // город необязателен
    const val = answers[currentStep!.id]
    if (!val) return false
    if (Array.isArray(val)) return val.length > 0
    return true
  }

  async function handleNext() {
    if (step < TOTAL_STEPS - 1) {
      setStep((s) => s + 1)
    } else {
      setLoading(true)
      try {
        await saveQuiz({
          who: (answers['who'] as string) ?? '',
          marketplaces: (answers['marketplaces'] as string[]) ?? [],
          priority: (answers['priority'] as string) ?? '',
          categories: (answers['categories'] as string[]) ?? [],
          city: city.trim(),
        })
        if (user) setUser({ ...user, city: city.trim() || null })
      } catch {
        // Продолжаем даже при ошибке
      } finally {
        setLoading(false)
        setScreen('home')
      }
    }
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', padding: '32px 20px 24px' }}>
      {/* Прогресс */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 32 }}>
        {Array.from({ length: TOTAL_STEPS }).map((_, i) => (
          <div
            key={i}
            style={{
              flex: 1,
              height: 3,
              borderRadius: 'var(--r-full)',
              background: i <= step ? 'var(--accent)' : 'var(--bg-raised)',
              transition: `background var(--t-base) var(--ease)`,
            }}
          />
        ))}
      </div>

      <div style={{ flex: 1 }}>
        {isCityStep ? (
          <>
            <h2 className="text-h2" style={{ marginBottom: 8 }}>
              Твой город?
            </h2>
            <p className="text-caption text-mute" style={{ marginBottom: 16 }}>
              Учту доставку и наличие в твоём регионе
            </p>

            {/* Кнопка автоопределения */}
            <button
              onClick={handleDetectCity}
              disabled={geoLoading}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                width: '100%',
                padding: '12px 16px',
                marginBottom: 12,
                background: 'var(--accent-soft)',
                border: '1px solid var(--accent)',
                borderRadius: 'var(--r-lg)',
                cursor: geoLoading ? 'default' : 'pointer',
                color: 'var(--accent)',
                fontSize: 14,
                fontFamily: 'inherit',
                fontWeight: 500,
              }}
            >
              <i className={`ti ${geoLoading ? 'ti-loader-2' : 'ti-current-location'}`}
                style={{ fontSize: 18, animation: geoLoading ? 'spin 1s linear infinite' : 'none' }} />
              {geoLoading ? 'Определяю...' : 'Определить автоматически'}
            </button>
            {geoError && (
              <div className="text-caption" style={{ color: 'var(--red)', marginBottom: 8 }}>{geoError}</div>
            )}

            <div style={{ position: 'relative' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                background: 'var(--bg-raised)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--r-lg)',
                padding: '6px 6px 6px 16px',
              }}>
                <i className="ti ti-map-pin" style={{ fontSize: 20, color: 'var(--text-dim)' }} />
                <input
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  placeholder="Или введи вручную..."
                  style={{
                    flex: 1,
                    background: 'transparent',
                    border: 'none',
                    outline: 'none',
                    color: 'var(--text)',
                    fontSize: 16,
                    fontFamily: 'inherit',
                    padding: '10px 0',
                  }}
                />
                {city && (
                  <button onClick={() => setCity('')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-dim)', padding: 8 }}>
                    <i className="ti ti-x" style={{ fontSize: 16 }} />
                  </button>
                )}
              </div>

              {filteredCities.length > 0 && (
                <div style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  right: 0,
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--r-md)',
                  marginTop: 4,
                  zIndex: 10,
                  overflow: 'hidden',
                }}>
                  {filteredCities.slice(0, 5).map((c) => (
                    <button
                      key={c}
                      onClick={() => setCity(c)}
                      style={{
                        display: 'block',
                        width: '100%',
                        padding: '12px 16px',
                        background: 'none',
                        border: 'none',
                        borderBottom: '1px solid var(--border)',
                        textAlign: 'left',
                        cursor: 'pointer',
                        color: 'var(--text)',
                        fontSize: 15,
                        fontFamily: 'inherit',
                      }}
                    >
                      <i className="ti ti-map-pin" style={{ fontSize: 14, marginRight: 8, color: 'var(--accent)' }} />
                      {c}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {!city && (
              <div style={{ marginTop: 16, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {['Москва', 'Санкт-Петербург', 'Ростов-на-Дону', 'Краснодар', 'Казань'].map((c) => (
                  <button
                    key={c}
                    onClick={() => setCity(c)}
                    style={{
                      background: 'var(--bg-raised)',
                      border: '1px solid var(--border)',
                      borderRadius: 'var(--r-full)',
                      padding: '6px 12px',
                      fontSize: 13,
                      color: 'var(--text-mute)',
                      cursor: 'pointer',
                      fontFamily: 'inherit',
                    }}
                  >
                    {c}
                  </button>
                ))}
              </div>
            )}
          </>
        ) : (
          <>
            <h2 className="text-h2" style={{ marginBottom: 24 }}>
              {currentStep!.question}
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {currentStep!.options.map((option) => (
                <button
                  key={option}
                  onClick={() => toggleOption(option)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: '14px 16px',
                    background: isSelected(option) ? 'var(--accent-soft)' : 'var(--bg-surface)',
                    border: `1px solid ${isSelected(option) ? 'var(--accent)' : 'var(--border)'}`,
                    borderRadius: 'var(--r-md)',
                    cursor: 'pointer',
                    color: 'var(--text)',
                    fontSize: 15,
                    fontFamily: 'inherit',
                    textAlign: 'left',
                    transition: `all var(--t-base) var(--ease)`,
                  }}
                >
                  <div style={{
                    width: 20, height: 20,
                    borderRadius: currentStep!.type === 'multi' ? 4 : '50%',
                    border: `2px solid ${isSelected(option) ? 'var(--accent)' : 'var(--border)'}`,
                    background: isSelected(option) ? 'var(--accent)' : 'transparent',
                    flexShrink: 0,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    {isSelected(option) && (
                      <i className="ti ti-check" style={{ fontSize: 12, color: 'var(--bg)' }} />
                    )}
                  </div>
                  {option}
                </button>
              ))}
            </div>
          </>
        )}
      </div>

      <Button
        variant="primary"
        size="lg"
        block
        disabled={!canNext()}
        loading={loading}
        onClick={handleNext}
      >
        {step < TOTAL_STEPS - 1 ? 'Далее' : 'Готово'}
      </Button>

      {isCityStep && (
        <button
          onClick={handleNext}
          style={{ marginTop: 12, background: 'none', border: 'none', color: 'var(--text-dim)', fontSize: 13, cursor: 'pointer', fontFamily: 'inherit' }}
        >
          Пропустить
        </button>
      )}
    </div>
  )
}
