import React, { useState } from 'react'
import { Button } from '../components/Button'
import { saveQuiz } from '../api/auth'
import { useAppStore } from '../store/appStore'

const STEPS = [
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

export function Quiz() {
  const setScreen = useAppStore((s) => s.setScreen)
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({})
  const [loading, setLoading] = useState(false)

  const currentStep = STEPS[step]

  function toggleOption(option: string) {
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
    const val = answers[currentStep.id]
    if (!val) return false
    if (Array.isArray(val)) return val.includes(option)
    return val === option
  }

  function canNext() {
    const val = answers[currentStep.id]
    if (!val) return false
    if (Array.isArray(val)) return val.length > 0
    return true
  }

  async function handleNext() {
    if (step < STEPS.length - 1) {
      setStep((s) => s + 1)
    } else {
      setLoading(true)
      try {
        await saveQuiz({
          who: (answers['who'] as string) ?? '',
          marketplaces: (answers['marketplaces'] as string[]) ?? [],
          priority: (answers['priority'] as string) ?? '',
          categories: (answers['categories'] as string[]) ?? [],
        })
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
        {STEPS.map((_, i) => (
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
        <h2 className="text-h2" style={{ marginBottom: 24 }}>
          {currentStep.question}
        </h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {currentStep.options.map((option) => (
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
              <div
                style={{
                  width: 20,
                  height: 20,
                  borderRadius: currentStep.type === 'multi' ? 4 : '50%',
                  border: `2px solid ${isSelected(option) ? 'var(--accent)' : 'var(--border)'}`,
                  background: isSelected(option) ? 'var(--accent)' : 'transparent',
                  flexShrink: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {isSelected(option) && (
                  <i className="ti ti-check" style={{ fontSize: 12, color: 'var(--bg)' }} />
                )}
              </div>
              {option}
            </button>
          ))}
        </div>
      </div>

      <Button
        variant="primary"
        size="lg"
        block
        disabled={!canNext()}
        loading={loading}
        onClick={handleNext}
      >
        {step < STEPS.length - 1 ? 'Далее' : 'Готово'}
      </Button>
    </div>
  )
}
