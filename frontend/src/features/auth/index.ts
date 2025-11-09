/**
 * Auth Feature Exports
 *
 * Central export point for auth feature
 */

// Stores
export { useAuthStore, type User, type AuthState } from './stores/authStore'

// Hooks
export { useAuth, type RegisterFormData, type UseAuthReturn } from './hooks/useAuth'

// Components
export { ProtectedRoute, type ProtectedRouteProps } from './components/ProtectedRoute'

// Pages
export { LoginPage } from './pages/LoginPage'
export { RegisterPage } from './pages/RegisterPage'
