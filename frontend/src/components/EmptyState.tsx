import React from 'react'
import { Button } from './Button'

interface EmptyStateProps {
  icon?: string
  title: string
  description: string
  action?: {
    label: string
    onClick: () => void
  }
}

export function EmptyState({ icon = 'ti-search', title, description, action }: EmptyStateProps) {
  return (
    <div
      style={{
        padding: '48px 24px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        textAlign: 'center',
      }}
    >
      <div
        style={{
          width: 64,
          height: 64,
          background: 'var(--bg-raised)',
          borderRadius: 'var(--r-full)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: 16,
        }}
      >
        <i className={`ti ${icon}`} style={{ fontSize: 28, color: 'var(--text-dim)' }} />
      </div>
      <div style={{ fontSize: 17, fontWeight: 600, marginBottom: 6 }}>{title}</div>
      <div
        className="text-mute"
        style={{ fontSize: 13, maxWidth: 260, marginBottom: action ? 20 : 0 }}
      >
        {description}
      </div>
      {action && (
        <Button variant="primary" size="md" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  )
}
