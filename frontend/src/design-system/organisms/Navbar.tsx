import React, { ReactNode } from 'react'
import { Menu } from 'lucide-react'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import './Navbar.css'

export interface NavbarProps {
  onMenuClick?: () => void
  title?: string
  actions?: ReactNode
  user?: {
    name: string
    email: string
    avatar?: string
  }
}

export function Navbar({ onMenuClick, title, actions, user }: NavbarProps) {
  return (
    <header className="navbar" role="banner">
      <div className="navbar__container">
        {/* Mobile menu button */}
        <button
          onClick={onMenuClick}
          className="navbar__menu-button"
          aria-label="Open menu"
        >
          <Menu size={24} />
        </button>

        {/* Page title */}
        {title && <h1 className="navbar__title">{title}</h1>}

        {/* Spacer */}
        <div className="navbar__spacer" />

        {/* Custom actions */}
        {actions && <div className="navbar__actions">{actions}</div>}

        {/* User menu */}
        {user && (
          <div className="navbar__user">
            <div className="navbar__user-info">
              <div className="navbar__user-name">{user.name}</div>
              <div className="navbar__user-email">{user.email}</div>
            </div>
            <Avatar className="navbar__user-avatar">
              {user.avatar && <AvatarImage src={user.avatar} alt={user.name} />}
              <AvatarFallback>
                {user.name
                  .split(' ')
                  .map(n => n[0])
                  .join('')
                  .toUpperCase()
                  .slice(0, 2)}
              </AvatarFallback>
            </Avatar>
          </div>
        )}
      </div>
    </header>
  )
}

Navbar.displayName = 'Navbar'
