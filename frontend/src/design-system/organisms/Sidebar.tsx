import React, { useEffect, ReactNode } from 'react'
import { Link, useLocation } from '@tanstack/react-router'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import './Sidebar.css'

export interface NavItem {
  to: string
  label: string
  icon: ReactNode
  badge?: number | string
  children?: NavItem[]
}

export interface SidebarProps {
  open: boolean
  onClose: () => void
  items: NavItem[]
  collapsed?: boolean
  onToggleCollapse?: () => void
}

export function Sidebar({
  open,
  onClose,
  items,
  collapsed = false,
  onToggleCollapse,
}: SidebarProps) {
  const location = useLocation()

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) {
        onClose()
      }
    }

    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [open, onClose])

  const isActive = (path: string) => location.pathname === path

  return (
    <>
      {/* Backdrop (mobile only) */}
      {open && (
        <div
          className="sidebar-backdrop"
          onClick={onClose}
          role="presentation"
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`sidebar ${open ? 'sidebar--open' : ''} ${collapsed ? 'sidebar--collapsed' : ''}`}
        role="complementary"
        aria-label="Navigation"
      >
        <div className="sidebar__header">
          {onToggleCollapse && (
            <button
              onClick={onToggleCollapse}
              className="sidebar__toggle"
              aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {collapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
            </button>
          )}
        </div>

        <nav className="sidebar__nav">
          <ul className="sidebar__list">
            {items.map((item) => (
              <li key={item.to} className="sidebar__item">
                <Link
                  to={item.to}
                  className={`sidebar__link ${isActive(item.to) ? 'sidebar__link--active' : ''}`}
                  onClick={onClose}
                >
                  <span className="sidebar__icon">{item.icon}</span>
                  {!collapsed && (
                    <>
                      <span className="sidebar__label">{item.label}</span>
                      {item.badge && (
                        <Badge variant="secondary" className="sidebar__badge">
                          {item.badge}
                        </Badge>
                      )}
                    </>
                  )}
                </Link>

                {/* Nested items */}
                {!collapsed && item.children && (
                  <ul className="sidebar__sublist">
                    {item.children.map((child) => (
                      <li key={child.to}>
                        <Link
                          to={child.to}
                          className={`sidebar__link sidebar__link--child ${isActive(child.to) ? 'sidebar__link--active' : ''}`}
                          onClick={onClose}
                        >
                          <span className="sidebar__icon">{child.icon}</span>
                          <span className="sidebar__label">{child.label}</span>
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        </nav>
      </aside>
    </>
  )
}

Sidebar.displayName = 'Sidebar'
