import { forwardRef, ReactNode, useEffect } from 'react'
import { X } from 'lucide-react'
import { IconButton } from '../atoms/IconButton'
import './Sidebar.css'

/**
 * Sidebar Template Component
 *
 * Navigation sidebar for app layouts:
 * - Single Responsibility: Application navigation container
 * - Variants: permanent (desktop), temporary (mobile drawer)
 * - Accessibility: Proper ARIA labels and keyboard navigation
 * - Responsive: Adapts behavior based on variant
 */

export interface SidebarProps {
  isOpen: boolean
  onClose: () => void
  variant?: 'permanent' | 'temporary'
  children: ReactNode
  className?: string
}

export const Sidebar = forwardRef<HTMLDivElement, SidebarProps>(
  (
    {
      isOpen,
      onClose,
      variant = 'permanent',
      children,
      className = '',
    },
    ref
  ) => {
    const classes = [
      'sidebar',
      `sidebar--${variant}`,
      isOpen ? 'sidebar--open' : 'sidebar--closed',
      className,
    ]
      .filter(Boolean)
      .join(' ')

    // Handle Escape key to close temporary sidebar
    useEffect(() => {
      if (variant === 'temporary' && isOpen) {
        const handleEscape = (event: KeyboardEvent) => {
          if (event.key === 'Escape') {
            onClose()
          }
        }

        document.addEventListener('keydown', handleEscape)
        return () => {
          document.removeEventListener('keydown', handleEscape)
        }
      }
    }, [variant, isOpen, onClose])

    // Handle backdrop click for temporary sidebar
    const handleBackdropClick = (e: React.MouseEvent) => {
      if (e.target === e.currentTarget && variant === 'temporary') {
        onClose()
      }
    }

    return (
      <>
        {/* Backdrop for temporary variant */}
        {variant === 'temporary' && isOpen && (
          <div
            className="sidebar__backdrop"
            onClick={handleBackdropClick}
            aria-hidden="true"
          />
        )}

        {/* Sidebar */}
        <aside
          ref={ref}
          className={classes}
          role="complementary"
          aria-label="Application navigation"
        >
          {/* Close button for temporary variant */}
          {variant === 'temporary' && (
            <div className="sidebar__header">
              <IconButton
                icon={<X />}
                onClick={onClose}
                variant="ghost"
                aria-label="Close sidebar"
                className="sidebar__close-button"
              />
            </div>
          )}

          {/* Navigation content */}
          <div className="sidebar__content">
            {children}
          </div>
        </aside>
      </>
    )
  }
)

Sidebar.displayName = 'Sidebar'
