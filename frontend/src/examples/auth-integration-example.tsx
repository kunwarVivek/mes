/**
 * JWT Authentication Integration Example
 *
 * This file demonstrates how to use the JWT authentication system
 * with axios interceptors and tenant context.
 *
 * DO NOT import this file in production code.
 * This is for documentation and testing purposes only.
 */

import { useAuth } from '../features/auth/hooks/useAuth'
import { TenantSelector } from '../components/TenantSelector'
import { useAuthStore } from '../stores/auth.store'
import apiClient from '../lib/api-client'

/**
 * Example 1: Login Flow
 *
 * When a user logs in:
 * 1. useAuth.login() calls backend /auth/login endpoint
 * 2. Backend returns access_token, refresh_token, user, and optional default org/plant
 * 3. Tokens are stored in Zustand auth store (persisted to localStorage)
 * 4. All subsequent API calls automatically include:
 *    - Authorization: Bearer <access_token>
 *    - X-Organization-ID: <current_org_id>
 *    - X-Plant-ID: <current_plant_id>
 */
function LoginExample() {
  const { login, user, isAuthenticated } = useAuth()

  const handleLogin = async () => {
    try {
      await login('user@example.com', 'password')
      console.log('Login successful')
    } catch (error) {
      console.error('Login failed:', error)
    }
  }

  return (
    <div>
      <button onClick={handleLogin}>Login</button>
      {isAuthenticated && <p>Welcome {user?.email}</p>}
    </div>
  )
}

/**
 * Example 2: Tenant Context Selection
 *
 * Users can switch between organizations and plants.
 * This updates the X-Organization-ID and X-Plant-ID headers
 * sent with all API requests for Row Level Security (RLS).
 */
function TenantExample() {
  const { currentOrg, currentPlant } = useAuthStore()

  return (
    <div>
      <h2>Current Context</h2>
      <p>Organization: {currentOrg?.org_name || 'None selected'}</p>
      <p>Plant: {currentPlant?.plant_name || 'None selected'}</p>

      <TenantSelector />
    </div>
  )
}

/**
 * Example 3: Making Authenticated API Calls
 *
 * All requests through apiClient automatically include:
 * - JWT token in Authorization header
 * - Tenant context in X-Organization-ID and X-Plant-ID headers
 *
 * If a 401 error occurs:
 * 1. Interceptor attempts to refresh token using /auth/refresh endpoint
 * 2. If refresh succeeds, original request is retried with new token
 * 3. If refresh fails, user is logged out and redirected to /login
 */
async function ApiCallExample() {
  try {
    // This request will automatically include:
    // Authorization: Bearer <token>
    // X-Organization-ID: <current_org_id>
    // X-Plant-ID: <current_plant_id>
    const response = await apiClient.get('/materials')
    console.log('Materials:', response.data)
  } catch (error) {
    console.error('API call failed:', error)
  }
}

/**
 * Example 4: Token Refresh Flow
 *
 * Automatic token refresh happens transparently:
 * 1. User makes API request
 * 2. Token is expired, backend returns 401
 * 3. Response interceptor catches 401
 * 4. POST to /auth/refresh with refresh_token
 * 5. New access_token is stored in auth store
 * 6. Original request is retried with new token
 * 7. User never notices the token was refreshed
 */
function TokenRefreshExample() {
  const { accessToken, refreshToken } = useAuthStore()

  return (
    <div>
      <h2>Token Status</h2>
      <p>Access Token: {accessToken ? 'Valid' : 'None'}</p>
      <p>Refresh Token: {refreshToken ? 'Valid' : 'None'}</p>
      <p>Token refresh happens automatically when access token expires</p>
    </div>
  )
}

/**
 * Example 5: Logout Flow
 *
 * When a user logs out:
 * 1. useAuth.logout() clears all auth state
 * 2. User, tokens, and tenant context are removed
 * 3. localStorage is cleared (via Zustand persist)
 * 4. Subsequent API calls will not include auth headers
 */
function LogoutExample() {
  const { logout, isAuthenticated } = useAuth()

  const handleLogout = () => {
    logout()
    console.log('Logged out successfully')
  }

  return (
    <div>
      {isAuthenticated && <button onClick={handleLogout}>Logout</button>}
    </div>
  )
}

/**
 * Example 6: Manual API Call (bypass interceptors)
 *
 * To make a request without automatic auth headers
 * (e.g., for login/register endpoints), use axios directly:
 */
async function UnauthenticatedApiCallExample() {
  const axios = (await import('axios')).default

  try {
    const response = await axios.post('http://localhost:8000/api/v1/auth/register', {
      email: 'newuser@example.com',
      password: 'password123',
      full_name: 'New User',
      organization_name: 'New Org',
    })
    console.log('Registration successful:', response.data)
  } catch (error) {
    console.error('Registration failed:', error)
  }
}

export {
  LoginExample,
  TenantExample,
  ApiCallExample,
  TokenRefreshExample,
  LogoutExample,
  UnauthenticatedApiCallExample,
}
