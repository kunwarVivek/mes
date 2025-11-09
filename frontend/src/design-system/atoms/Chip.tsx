import { ReactNode } from 'react'
import './Chip.css'

/**
 * Chip Atom
 *
 * Removable tag component with delete functionality
 * - Optional delete callback shows X button
 * - Filled and outlined variants
 * - Icon support for leading indicators
 */

export interface ChipProps {
  label: string
  onDelete?: () => void
  variant?: 'filled' | 'outlined'
  size?: 'sm' | 'md'
  icon?: ReactNode
  className?: string
}

export function Chip({
  label,
  onDelete,
  variant = 'filled',
  size = 'md',
  icon,
  className = '',
}: ChipProps) {
  const classes = [
    'chip',
    `chip--${variant}`,
    `chip--${size}`,
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className={classes}>
      {icon && <span className="chip__icon" aria-hidden="true">{icon}</span>}
      <span className="chip__label">{label}</span>
      {onDelete && (
        <button
          type="button"
          className="chip__delete"
          onClick={onDelete}
          aria-label={`Remove ${label}`}
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 14 14"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            <path
              d="M10.5 3.5L3.5 10.5M3.5 3.5L10.5 10.5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
        </button>
      )}
    </div>
  )
}

Chip.displayName = 'Chip'
