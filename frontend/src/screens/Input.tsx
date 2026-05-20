import React, { useRef, useState } from 'react'
import { Button } from '../components/Button'
import { useAppStore } from '../store/appStore'

const SUGGESTIONS = [
  'Робот-пылесос для шерсти',
  'Робот-пылесос до 30000',
  'Беспроводные наушники с шумоподавлением',
  'Наушники для спорта',
  'Смартфон до 20000',
  'Смартфон до 50000 флагман',
  'Ноутбук для работы до 60000',
  'Ноутбук для учёбы',
  'Умная колонка',
  'Bluetooth-колонка',
  'Кофемашина для дома',
  'Кофемашина рожковая',
  'Электрическая зубная щётка',
  'Умные часы',
  'Фитнес-браслет',
  'Планшет для детей',
  'Планшет для рисования',
  'Телевизор 55 дюймов',
  'Игровая мышь',
  'Механическая клавиатура',
  'Увлажнитель воздуха',
  'Очиститель воздуха',
  'Электросамокат',
  'Фотоаппарат',
  'Пылесос беспроводной',
  'Кроссовки для бега',
  'Зимняя куртка',
  'Рюкзак для ноутбука',
  'Мультиварка',
  'Фен для волос профессиональный',
]

const CATEGORY_CHIPS = [
  'до 10 000 ₽',
  'до 30 000 ₽',
  'для подарка',
  'с хорошими отзывами',
  'флагман',
  'для детей',
]

export function Input() {
  const { setScreen, setCurrentQuery, currentQuery } = useAppStore()
  const [query, setQuery] = useState(currentQuery)
  const [listening, setListening] = useState(false)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const recognitionRef = useRef<any>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const filteredSuggestions = query.trim().length >= 2
    ? SUGGESTIONS.filter(s =>
        s.toLowerCase().includes(query.toLowerCase()) &&
        s.toLowerCase() !== query.toLowerCase()
      ).slice(0, 5)
    : []

  function startVoice() {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognition) return

    const recognition = new SpeechRecognition()
    recognition.lang = 'ru-RU'
    recognition.interimResults = true

    recognition.onresult = (event: any) => {
      const transcript = Array.from(event.results)
        .map((r: any) => r[0].transcript)
        .join('')
      setQuery(transcript)
    }

    recognition.onend = () => setListening(false)
    recognition.onerror = () => setListening(false)

    recognitionRef.current = recognition
    recognition.start()
    setListening(true)
  }

  function stopVoice() {
    recognitionRef.current?.stop()
    setListening(false)
  }

  function handleSearch() {
    if (!query.trim()) return
    setCurrentQuery(query.trim())
    setScreen('processing')
  }

  function selectSuggestion(s: string) {
    setQuery(s)
    setShowSuggestions(false)
    inputRef.current?.focus()
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', padding: '24px 20px' }}>
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

      <h2 className="text-h2" style={{ marginBottom: 24 }}>Что ищем?</h2>

      <div style={{ position: 'relative' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            background: 'var(--bg-raised)',
            border: `1px solid ${listening ? 'var(--red)' : 'var(--border)'}`,
            borderRadius: 'var(--r-lg)',
            padding: '6px 6px 6px 16px',
            boxShadow: listening ? '0 0 0 3px rgba(248,81,73,0.15)' : undefined,
            transition: `all var(--t-base) var(--ease)`,
          }}
        >
          <i className="ti ti-search" style={{ fontSize: 20, color: 'var(--text-dim)' }} />
          <input
            ref={inputRef}
            autoFocus
            value={query}
            onChange={(e) => { setQuery(e.target.value); setShowSuggestions(true) }}
            onFocus={() => setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Робот-пылесос до 30к для кота..."
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text)',
              fontSize: 15,
              fontFamily: 'inherit',
              padding: '8px 0',
            }}
          />
          {query.length > 0 && (
            <button
              onMouseDown={(e) => { e.preventDefault(); setQuery(''); setShowSuggestions(false) }}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-dim)', padding: '8px 4px' }}
            >
              <i className="ti ti-x" style={{ fontSize: 16 }} />
            </button>
          )}
          <button
            onClick={listening ? stopVoice : startVoice}
            style={{
              width: 40,
              height: 40,
              background: listening ? 'rgba(248, 81, 73, 0.1)' : 'var(--accent)',
              border: listening ? '1px solid var(--red)' : 'none',
              borderRadius: 'var(--r-md)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              flexShrink: 0,
              animation: listening ? 'pulse 1.5s ease-in-out infinite' : 'none',
            }}
          >
            <i
              className={`ti ${listening ? 'ti-player-stop-filled' : 'ti-microphone'}`}
              style={{ fontSize: 20, color: listening ? 'var(--red)' : 'var(--bg)' }}
            />
          </button>
        </div>

        {showSuggestions && filteredSuggestions.length > 0 && (
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
            {filteredSuggestions.map((s) => (
              <button
                key={s}
                onMouseDown={(e) => { e.preventDefault(); selectSuggestion(s) }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  width: '100%',
                  padding: '11px 16px',
                  background: 'none',
                  border: 'none',
                  borderBottom: '1px solid var(--border)',
                  textAlign: 'left',
                  cursor: 'pointer',
                  color: 'var(--text)',
                  fontSize: 14,
                  fontFamily: 'inherit',
                }}
              >
                <i className="ti ti-search" style={{ fontSize: 14, color: 'var(--text-dim)', flexShrink: 0 }} />
                {s}
              </button>
            ))}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 12, marginBottom: 32 }}>
        {CATEGORY_CHIPS.map((chip) => (
          <button
            key={chip}
            onClick={() => { setQuery((q) => (q.trim() ? q.trimEnd() + ' ' + chip : chip)); inputRef.current?.focus() }}
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
            {chip}
          </button>
        ))}
      </div>

      <div style={{ flex: 1 }} />

      <Button
        variant="primary"
        size="lg"
        block
        disabled={!query.trim()}
        onClick={handleSearch}
      >
        Найти
      </Button>
    </div>
  )
}
