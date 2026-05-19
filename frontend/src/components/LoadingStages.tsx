import React from 'react'

type StageStatus = 'pending' | 'active' | 'done'

interface Stage {
  label: string
  status: StageStatus
}

interface LoadingStagesProps {
  stages: Stage[]
}

export function LoadingStages({ stages }: LoadingStagesProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {stages.map((stage, i) => (
        <div
          key={i}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 16px',
            borderRadius: 'var(--r-md)',
            background: stage.status === 'done' ? 'var(--accent-soft)' : 'var(--bg-raised)',
            border: stage.status === 'active' ? '1px solid var(--accent)' : '1px solid transparent',
            transition: `all var(--t-base) var(--ease)`,
          }}
        >
          {stage.status === 'pending' && (
            <i className="ti ti-circle" style={{ fontSize: 20, color: 'var(--text-dim)' }} />
          )}
          {stage.status === 'active' && (
            <span className="spinner" />
          )}
          {stage.status === 'done' && (
            <i className="ti ti-check" style={{ fontSize: 20, color: 'var(--accent)' }} />
          )}
          <span
            className="text-body"
            style={{ color: stage.status === 'pending' ? 'var(--text-dim)' : 'var(--text)' }}
          >
            {stage.label}
          </span>
        </div>
      ))}
    </div>
  )
}
