import { ButtonHTMLAttributes, forwardRef, ReactNode } from 'react'
import './IconButton.css'

/**
 * IconButton Atom
 *
 * Icon-only button component for toolbars and actions:
 * - Single Responsibility: Icon-based actions
 * - Accessibility: Mandatory aria-label for screen readers
 * - Variants: default, primary, danger, ghost for different contexts
 * - Focus-visible keyboard navigation
 */

export interface IconButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children'> {
  icon: ReactNode
  onClick?: () => void
  variant?: 'default' | 'primary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  'aria-label': string // Required for accessibility
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  (
    {
      icon,
      variant = 'default',
      size = 'md',
      disabled = false,
      type = 'button',
      className = '',
      'aria-label': ariaLabel,
      ...props
    },
    ref
  ) => {
    const classes = [
      'icon-button',
      `icon-button--${variant}`,
      `icon-button--${size}`,
      disabled && 'icon-button--disabled',
      className,
    ]
      .filter(Boolean)
      .join(' ')

    return (
      <button
        ref={ref}
        type={type}
        className={classes}
        disabled={disabled}
        aria-label={ariaLabel}
        {...props}
      >
        <span className="icon-button__icon" aria-hidden="true">
          {icon}
        </span>
      </button>
    )
  }
)

IconButton.displayName = 'IconButton'
