import { HTMLAttributes, ReactNode } from 'react'
import './Typography.css'

/**
 * Typography Atoms
 *
 * Text components following typography hierarchy:
 * - Visual Hierarchy: Clear importance levels
 * - Readability: Proper line height and spacing
 * - Consistency: Unified text styling
 */

interface BaseTypographyProps extends HTMLAttributes<HTMLElement> {
  children: ReactNode
}

export const Heading1 = ({ className = '', children, ...props }: BaseTypographyProps) => (
  <h1 className={`heading-1 ${className}`} {...props}>
    {children}
  </h1>
)

export const Heading2 = ({ className = '', children, ...props }: BaseTypographyProps) => (
  <h2 className={`heading-2 ${className}`} {...props}>
    {children}
  </h2>
)

export const Heading3 = ({ className = '', children, ...props }: BaseTypographyProps) => (
  <h3 className={`heading-3 ${className}`} {...props}>
    {children}
  </h3>
)

export const Body = ({ className = '', children, ...props }: BaseTypographyProps) => (
  <p className={`body ${className}`} {...props}>
    {children}
  </p>
)

export const Caption = ({ className = '', children, ...props }: BaseTypographyProps) => (
  <span className={`caption ${className}`} {...props}>
    {children}
  </span>
)
