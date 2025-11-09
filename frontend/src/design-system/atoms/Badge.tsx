import { ReactNode } from 'react'
import './Badge.css'

/**
 * Badge Atom
 *
 * Status indicators with semantic color variants
 * - Uses theme colors for manufacturing contexts
 * - Pill-shaped with optional dot indicator
 * - Accessible with proper ARIA attributes
 * - Responsive to theme changes
 */

export interface BadgeProps {
  variant: 'success' | 'warning' | 'error' | 'info' | 'neutral'
  size?: 'sm' | 'md' | 'lg'
  dot?: boolean
  children: ReactNode
  className?: string
}

export function Badge({
  variant,
  size = 'md',
  dot = false,
  children,
  className = '',
}: BadgeProps) {
  const classes = [
    'badge',
    `badge--${variant}`,
    `badge--${size}`,
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <span className={classes} role="status">
      {dot && <span className="badge__dot" aria-hidden="true" />}
      {children}
    </span>
  )
}

Badge.displayName = 'Badge'
