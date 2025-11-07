import { HTMLAttributes, forwardRef } from 'react'
import './Card.css'

/**
 * Card Atom
 *
 * A container component following Gestalt principles:
 * - Proximity: Groups related content
 * - Figure/Ground: Clear visual separation
 * - Elevation: Shadow hierarchy for depth
 */

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'outlined' | 'elevated'
  padding?: 'none' | 'sm' | 'md' | 'lg'
  hoverable?: boolean
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      variant = 'default',
      padding = 'md',
      hoverable = false,
      className = '',
      children,
      ...props
    },
    ref
  ) => {
    const classes = [
      'card',
      `card--${variant}`,
      `card--padding-${padding}`,
      hoverable && 'card--hoverable',
      className,
    ]
      .filter(Boolean)
      .join(' ')

    return (
      <div ref={ref} className={classes} {...props}>
        {children}
      </div>
    )
  }
)

Card.displayName = 'Card'
