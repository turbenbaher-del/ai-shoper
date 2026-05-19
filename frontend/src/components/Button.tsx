import React from 'react'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'
type Size = 'sm' | 'md' | 'lg'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  icon?: React.ReactNode
  loading?: boolean
  block?: boolean
}

const variantStyles: Record<Variant, React.CSSProperties> = {
  primary: {
    background: 'var(--accent)',
    color: 'var(--bg)',
  },
  secondary: {
    background: 'var(--bg-raised)',
    color: 'var(--text)',
    border: '1px solid var(--border)',
  },
  ghost: {
    background: 'transparent',
    color: 'var(--text)',
  },
  danger: {
    background: 'rgba(248, 81, 73, 0.1)',
    color: 'var(--red)',
    border: '1px solid rgba(248, 81, 73, 0.2)',
  },
}

const sizeStyles: Record<Size, React.CSSProperties> = {
  sm: { height: 36, padding: '0 14px', fontSize: 14 },
  md: { height: 44, padding: '0 20px', fontSize: 15 },
  lg: { height: 52, padding: '0 28px', fontSize: 15 },
}

export function Button({
  variant = 'primary',
  size = 'md',
  icon,
  loading,
  block,
  children,
  disabled,
  style,
  ...props
}: ButtonProps) {
  return (
    <button
      {...props}
      disabled={disabled || loading}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
        borderRadius: 'var(--r-md)',
        fontFamily: 'inherit',
        fontWeight: 500,
        border: 'none',
        cursor: disabled || loading ? 'not-allowed' : 'pointer',
        opacity: disabled || loading ? 0.4 : 1,
        transition: `all var(--t-base) var(--ease)`,
        width: block ? '100%' : undefined,
        ...variantStyles[variant],
        ...sizeStyles[size],
        ...style,
      }}
    >
      {loading ? <span className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} /> : icon}
      {children}
    </button>
  )
}
