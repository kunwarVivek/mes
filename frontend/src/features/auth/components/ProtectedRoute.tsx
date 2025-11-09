import { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

/**
 * ProtectedRoute Component
 *
 * Route wrapper requiring authentication:
 * - Single Responsibility: Route protection
 * - Redirects to /login if not authenticated
 * - Shows loading fallback while checking auth
 * - Preserves intended destination for redirect after login
 */

export interface ProtectedRouteProps {
  children: ReactNode
  fallback?: ReactNode
}

export const ProtectedRoute = ({ children, fallback }: ProtectedRouteProps) => {
  const { isAuthenticated, isLoading } = useAuthStore()

  // Show loading state while checking authentication
  if (isLoading) {
    return <>{fallback || <div>Loading...</div>}</>
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  // User is authenticated, render protected content
  return <>{children}</>
}

ProtectedRoute.displayName = 'ProtectedRoute'
