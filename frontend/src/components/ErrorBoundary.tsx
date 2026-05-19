import React, { Component } from 'react'

interface Props {
  children: React.ReactNode
}

interface State {
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('App crash:', error, info)
  }

  render() {
    const { error } = this.state
    if (!error) return this.props.children

    return (
      <div
        style={{
          height: '100dvh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 32,
          gap: 20,
          textAlign: 'center',
        }}
      >
        <i className="ti ti-mood-sad" style={{ fontSize: 56, color: 'var(--text-dim)' }} />
        <div>
          <div className="text-h2" style={{ marginBottom: 8 }}>Что-то пошло не так</div>
          <div className="text-body text-mute">Закрой и открой приложение заново</div>
        </div>
        <button
          onClick={() => this.setState({ error: null })}
          style={{
            background: 'var(--accent)',
            color: '#fff',
            border: 'none',
            borderRadius: 'var(--r-md)',
            padding: '12px 24px',
            fontSize: 14,
            fontWeight: 500,
            cursor: 'pointer',
            fontFamily: 'inherit',
          }}
        >
          Попробовать снова
        </button>
      </div>
    )
  }
}
