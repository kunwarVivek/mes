import { forwardRef, ReactNode } from 'react'
import { Menu } from 'lucide-react'
import { IconButton } from '../atoms/IconButton'
import './Navbar.css'

/**
 * Navbar Template Component
 *
 * Top navigation bar for app layouts:
 * - Single Responsibility: Top-level navigation and actions
 * - Accessibility: Proper ARIA labels and semantic HTML
 * - Responsive: Shows menu button on mobile
 * - Flexible: Supports title and custom actions
 */

export interface NavbarProps {
  title?: string
  actions?: ReactNode
  onMenuClick?: () => void
  showMenuButton?: boolean
  className?: string
}

export const Navbar = forwardRef<HTMLElement, NavbarProps>(
  (
    {
      title,
      actions,
      onMenuClick,
      showMenuButton = false,
      className = '',
    },
    ref
  ) => {
    const classes = [
      'navbar',
      className,
    ]
      .filter(Boolean)
      .join(' ')

    return (
      <header
        ref={ref}
        className={classes}
        role="banner"
      >
        <div className="navbar__container">
          {/* Left: Menu button (mobile) + Title */}
          <div className="navbar__left">
            {showMenuButton && onMenuClick && (
              <IconButton
                icon={<Menu />}
                onClick={onMenuClick}
                variant="ghost"
                aria-label="Open menu"
                className="navbar__menu-button"
              />
            )}
            {title && (
              <h1 className="navbar__title">{title}</h1>
            )}
          </div>

          {/* Right: Actions */}
          {actions && (
            <div className="navbar__actions">
              {actions}
            </div>
          )}
        </div>
      </header>
    )
  }
)

Navbar.displayName = 'Navbar'
