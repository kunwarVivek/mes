import { HTMLAttributes, forwardRef } from 'react'
import './Divider.css'

/**
 * Divider Atom
 *
 * Visual separator component:
 * - Single Responsibility: Visual separation of content
 * - Accessibility: Proper ARIA role and orientation
 * - Orientation options: horizontal (default), vertical
 * - Style variants: solid, dashed, dotted
 */

export interface DividerProps extends HTMLAttributes<HTMLDivElement> {
  orientation?: 'horizontal' | 'vertical'
  variant?: 'solid' | 'dashed' | 'dotted'
  spacing?: 'sm' | 'md' | 'lg' // Margin around divider
  thickness?: 'thin' | 'medium' | 'thick'
}

export const Divider = forwardRef<HTMLDivElement, DividerProps>(
  (
    {
      orientation = 'horizontal',
      variant = 'solid',
      spacing = 'md',
      thickness = 'medium',
      className = '',
      ...props
    },
    ref
  ) => {
    const classes = [
      'divider',
      `divider--${orientation}`,
      `divider--${variant}`,
      `divider--spacing-${spacing}`,
      `divider--${thickness}`,
      className,
    ]
      .filter(Boolean)
      .join(' ')

    return (
      <div
        ref={ref}
        role="separator"
        aria-orientation={orientation}
        className={classes}
        {...props}
      />
    )
  }
)

Divider.displayName = 'Divider'
