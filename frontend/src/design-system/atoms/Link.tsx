import { AnchorHTMLAttributes, forwardRef, ReactNode } from 'react'
import './Link.css'

/**
 * Link Atom
 *
 * Navigation link component:
 * - Single Responsibility: Navigation and external links
 * - Accessibility: Proper attributes for external links
 * - Variants: default, primary, muted for different contexts
 * - Underline options for different styles
 */

export interface LinkProps extends AnchorHTMLAttributes<HTMLAnchorElement> {
  href: string
  children: ReactNode
  variant?: 'default' | 'primary' | 'muted'
  external?: boolean // Opens in new tab if true
  underline?: 'always' | 'hover' | 'none'
  disabled?: boolean
  onClick?: (e: React.MouseEvent) => void
}

export const Link = forwardRef<HTMLAnchorElement, LinkProps>(
  (
    {
      href,
      children,
      variant = 'default',
      external = false,
      underline = 'hover',
      disabled = false,
      className = '',
      onClick,
      ...props
    },
    ref
  ) => {
    const classes = [
      'link',
      `link--${variant}`,
      `link--underline-${underline}`,
      disabled && 'link--disabled',
      className,
    ]
      .filter(Boolean)
      .join(' ')

    const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
      if (disabled) {
        e.preventDefault()
      }
      onClick?.(e)
    }

    const externalProps = external
      ? {
          target: '_blank',
          rel: 'noopener noreferrer',
        }
      : {}

    return (
      <a
        ref={ref}
        href={href}
        className={classes}
        onClick={handleClick}
        aria-disabled={disabled ? 'true' : undefined}
        {...externalProps}
        {...props}
      >
        {children}
      </a>
    )
  }
)

Link.displayName = 'Link'
