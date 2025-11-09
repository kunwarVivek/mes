import React, { ReactNode } from 'react'
import { Link, useLocation } from '@tanstack/react-router'
import './MobileNav.css'

export interface NavItem {
  to: string
  label: string
  icon: ReactNode
  badge?: number
}

export interface MobileNavProps {
  items: NavItem[]
}

export function MobileNav({ items }: MobileNavProps) {
  const location = useLocation()

  // Limit to max 5 items
  const limitedItems = items.slice(0, 5)

  const isActive = (path: string) => location.pathname === path

  return (
    <nav className="mobile-nav" role="navigation" aria-label="Mobile navigation">
      <ul className="mobile-nav__list">
        {limitedItems.map((item) => (
          <li key={item.to} className="mobile-nav__item">
            <Link
              to={item.to}
              className={`mobile-nav__link ${isActive(item.to) ? 'mobile-nav__link--active' : ''}`}
            >
              <span className="mobile-nav__icon">
                {item.icon}
                {item.badge && (
                  <span className="mobile-nav__badge">{item.badge}</span>
                )}
              </span>
              <span className="mobile-nav__label">{item.label}</span>
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  )
}

MobileNav.displayName = 'MobileNav'
