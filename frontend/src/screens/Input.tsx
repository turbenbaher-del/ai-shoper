import React, { useRef, useState } from 'react'
import { Button } from '../components/Button'
import { useAppStore } from '../store/appStore'

export function Input() {
  const { setScreen, setCurrentQuery, currentQuery } = useAppStore()
  const [query, setQuery] = useState(currentQuery)
  const [listening, setListening] = useState(false)
  const recognitionRef = useRef<any>(null)

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

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', padding: '24px 20px' }}>
      {/* Назад */}
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

      {/* Поле ввода */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          background: 'var(--bg-raised)',
          border: `1px solid ${listening ? 'var(--red)' : 'var(--border)'}`,
          borderRadius: 'var(--r-lg)',
          padding: '6px 6px 6px 16px',
          marginBottom: 12,
          boxShadow: listening ? '0 0 0 3px rgba(248,81,73,0.15)' : undefined,
          transition: `all var(--t-base) var(--ease)`,
        }}
      >
        <i className="ti ti-search" style={{ fontSize: 20, color: 'var(--text-dim)' }} />
        <input
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
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

      {/* Подсказки */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 32 }}>
        {['до 30 000 ₽', 'для подарка', 'с хорошими отзывами', 'флагман'].map((chip) => (
          <button
            key={chip}
            onClick={() => setQuery((q) => q + ' ' + chip)}
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
