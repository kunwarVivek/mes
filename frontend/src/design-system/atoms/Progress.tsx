import './Progress.css'

/**
 * Progress Atom
 *
 * Linear progress bar component
 * - Value clamping (0-100)
 * - Color variants for different states
 * - Optional percentage label
 * - Accessible with ARIA attributes
 */

export interface ProgressProps {
  value: number
  max?: number
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'success' | 'warning' | 'error'
  showLabel?: boolean
  className?: string
}

export function Progress({
  value,
  max = 100,
  size = 'md',
  variant = 'default',
  showLabel = false,
  className = '',
}: ProgressProps) {
  // Clamp value between 0 and max
  const clampedValue = Math.max(0, Math.min(value, max))
  const percentage = (clampedValue / max) * 100

  const classes = [
    'progress',
    `progress--${size}`,
    className,
  ]
    .filter(Boolean)
    .join(' ')

  const barClasses = [
    'progress__bar',
    `progress__bar--${variant}`,
  ].join(' ')

  return (
    <div className="progress-wrapper">
      <div
        className={classes}
        role="progressbar"
        aria-valuenow={clampedValue}
        aria-valuemin={0}
        aria-valuemax={max}
      >
        <div
          className={barClasses}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <span className="progress__label" aria-live="polite">
          {Math.round(percentage)}%
        </span>
      )}
    </div>
  )
}

Progress.displayName = 'Progress'
