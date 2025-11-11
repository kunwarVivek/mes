import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/auth.store'

/**
 * Axios API Client
 *
 * Centralized HTTP client with interceptors:
 * - Request: Adds JWT token and tenant context headers
 * - Response: Handles token refresh on 401
 *
 * Headers added:
 * - Authorization: Bearer {jwt_token}
 * - X-Organization-ID: {current_org_id}
 * - X-Plant-ID: {current_plant_id}
 */

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor: Add JWT token and tenant context
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const { accessToken, currentOrg, currentPlant } = useAuthStore.getState()

    // Add JWT token
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`
    }

    // Add tenant context for RLS (Row Level Security)
    if (currentOrg) {
      config.headers['X-Organization-ID'] = currentOrg.id.toString()
    }

    if (currentPlant) {
      config.headers['X-Plant-ID'] = currentPlant.id.toString()
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor: Handle 401 with token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    // If 401 and not already retried, attempt token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const { refreshToken, setTokens, logout } = useAuthStore.getState()

        if (!refreshToken) {
          logout()
          window.location.href = '/login'
          return Promise.reject(error)
        }

        // Attempt to refresh token
        const response = await axios.post(
          `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/v1/auth/refresh`,
          { refresh_token: refreshToken }
        )

        const newAccessToken = response.data.access_token
        setTokens(newAccessToken)

        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        return apiClient(originalRequest)
      } catch (refreshError) {
        // Refresh failed, logout user
        const { logout } = useAuthStore.getState()
        logout()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient
