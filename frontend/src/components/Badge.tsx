import React from 'react'

type BadgeVariant = 'success' | 'accent' | 'warning' | 'danger' | 'info' | 'mute'

const variantStyles: Record<BadgeVariant, React.CSSProperties> = {
  success: { background: 'rgba(63, 185, 80, 0.15)', color: 'var(--green)' },
  accent:  { background: 'var(--accent-soft)', color: 'var(--accent)' },
  warning: { background: 'rgba(210, 153, 34, 0.15)', color: 'var(--amber)' },
  danger:  { background: 'rgba(248, 81, 73, 0.15)', color: 'var(--red)' },
  info:    { background: 'rgba(88, 166, 255, 0.15)', color: 'var(--blue)' },
  mute:    { background: 'var(--bg-raised)', color: 'var(--text-mute)' },
}

interface BadgeProps {
  variant?: BadgeVariant
  icon?: React.ReactNode
  children: React.ReactNode
}

export function Badge({ variant = 'mute', icon, children }: BadgeProps) {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: '4px 10px',
        borderRadius: 'var(--r-full)',
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: '0.03em',
        textTransform: 'uppercase',
        ...variantStyles[variant],
      }}
    >
      {icon}
      {children}
    </span>
  )
}
