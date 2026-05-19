import React, { useEffect } from 'react'

interface BottomSheetProps {
  open: boolean
  title?: string
  onClose: () => void
  children: React.ReactNode
}

export function BottomSheet({ open, title, onClose, children }: BottomSheetProps) {
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => { document.body.style.overflow = '' }
  }, [open])

  if (!open) return null

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.5)',
          zIndex: 100,
        }}
      />
      {/* Sheet */}
      <div
        style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          maxWidth: 480,
          margin: '0 auto',
          background: 'var(--bg-surface)',
          borderTopLeftRadius: 'var(--r-xl)',
          borderTopRightRadius: 'var(--r-xl)',
          borderTop: '1px solid var(--border)',
          padding: '8px 20px 24px',
          boxShadow: '0 -8px 32px rgba(0,0,0,0.5)',
          zIndex: 101,
          animation: `slideUp var(--t-slow) var(--ease)`,
        }}
      >
        {/* Handle */}
        <div
          onClick={onClose}
          style={{
            width: 40,
            height: 4,
            background: 'var(--bg-high)',
            borderRadius: 'var(--r-full)',
            margin: '0 auto 16px',
            cursor: 'pointer',
          }}
        />
        {title && (
          <div style={{ fontSize: 17, fontWeight: 600, marginBottom: 16 }}>{title}</div>
        )}
        {children}
      </div>
      <style>{`
        @keyframes slideUp {
          from { transform: translateY(100%); }
          to { transform: translateY(0); }
        }
      `}</style>
    </>
  )
}
