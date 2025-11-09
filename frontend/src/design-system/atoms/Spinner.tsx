import './Spinner.css'

/**
 * Spinner Atom
 *
 * Loading spinner component with theme integration
 * - CSS animation for smooth spinning
 * - Multiple size variants
 * - Accessible with ARIA attributes
 * - Uses theme colors dynamically
 */

export interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  color?: 'primary' | 'secondary' | 'neutral'
  label?: string
  className?: string
}

export function Spinner({
  size = 'md',
  color = 'primary',
  label = 'Loading...',
  className = '',
}: SpinnerProps) {
  const classes = [
    'spinner',
    `spinner--${size}`,
    `spinner--${color}`,
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className={classes} role="status" aria-live="polite">
      <svg
        className="spinner__svg"
        viewBox="0 0 50 50"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <circle
          className="spinner__circle"
          cx="25"
          cy="25"
          r="20"
          fill="none"
          strokeWidth="5"
        />
      </svg>
      <span className="spinner__label">{label}</span>
    </div>
  )
}

Spinner.displayName = 'Spinner'
