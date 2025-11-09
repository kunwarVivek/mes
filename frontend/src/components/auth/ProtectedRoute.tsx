import { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../../features/auth/hooks/useAuth'

/**
 * ProtectedRoute Component
 *
 * Wrapper that checks authentication and redirects to login if not authenticated:
 * - Single Responsibility: Route authentication guard
 * - Checks isAuthenticated from useAuth hook
 * - Redirects to /login if not authenticated
 * - Renders children if authenticated
 */

export interface ProtectedRouteProps {
  children: ReactNode
}

export const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  const { isAuthenticated } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

ProtectedRoute.displayName = 'ProtectedRoute'
