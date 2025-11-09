import { ReactNode } from 'react'
import './AuthLayout.css'

/**
 * AuthLayout Template Component
 *
 * Layout for authentication pages (login, register, reset password):
 * - Single Responsibility: Authentication page layout
 * - Centered card design
 * - Optional logo, title, subtitle
 * - Responsive: Full-width on mobile, card on desktop
 */

export interface AuthLayoutProps {
  children: ReactNode
  title?: string
  subtitle?: string
  logo?: ReactNode
  className?: string
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({
  children,
  title,
  subtitle,
  logo,
  className = '',
}) => {
  const classes = [
    'auth-layout',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className={classes}>
      <div className="auth-layout__card">
        {/* Logo */}
        {logo && (
          <div className="auth-layout__logo">
            {logo}
          </div>
        )}

        {/* Title */}
        {title && (
          <h1 className="auth-layout__title">{title}</h1>
        )}

        {/* Subtitle */}
        {subtitle && (
          <p className="auth-layout__subtitle">{subtitle}</p>
        )}

        {/* Content (form, etc.) */}
        <div className="auth-layout__content">
          {children}
        </div>
      </div>
    </div>
  )
}

AuthLayout.displayName = 'AuthLayout'
