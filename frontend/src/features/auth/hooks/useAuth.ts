import { useCallback } from 'react'
import { useAuthStore } from '../../../stores/auth.store'
import apiClient from '../../../lib/api-client'
import axios from 'axios'

/**
 * useAuth Hook
 *
 * Central authentication hook providing:
 * - Auth state: user, isAuthenticated
 * - Auth operations: login, register, logout
 * - Real API integration with JWT tokens
 */

export interface RegisterFormData {
  email: string
  password: string
  confirmPassword: string
  organizationName: string
  fullName: string
}

interface User {
  id: number
  email: string
  username: string
  is_active: boolean
  is_superuser: boolean
}

interface Organization {
  id: number
  org_code: string
  org_name: string
}

interface Plant {
  id: number
  plant_code: string
  plant_name: string
}

interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
  default_organization?: Organization
  default_plant?: Plant
}

export interface UseAuthReturn {
  user: User | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: RegisterFormData) => Promise<void>
  logout: () => void
}

export const useAuth = (): UseAuthReturn => {
  const authStore = useAuthStore()

  const login = useCallback(
    async (email: string, password: string) => {
      try {
        // Use form data for OAuth2 password flow
        const formData = new FormData()
        formData.append('username', email)
        formData.append('password', password)

        const response = await axios.post<LoginResponse>(
          `${apiClient.defaults.baseURL}/auth/login`,
          formData,
          {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
          }
        )

        const { access_token, refresh_token, user, default_organization, default_plant } = response.data

        // Store tokens and user in auth store
        authStore.login(user, access_token, refresh_token)

        // Set default organization and plant if available
        if (default_organization) {
          authStore.setCurrentOrg(default_organization)
        }

        if (default_plant) {
          authStore.setCurrentPlant(default_plant)
        }
      } catch (error: any) {
        const message = error.response?.data?.detail || 'Login failed'
        throw new Error(message)
      }
    },
    [authStore]
  )

  const register = useCallback(async (data: RegisterFormData) => {
    try {
      await apiClient.post('/auth/register', {
        email: data.email,
        password: data.password,
        full_name: data.fullName,
        organization_name: data.organizationName,
      })
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Registration failed'
      throw new Error(message)
    }
  }, [])

  const logout = useCallback(() => {
    authStore.logout()
  }, [authStore])

  return {
    user: authStore.user,
    isAuthenticated: authStore.isAuthenticated,
    login,
    register,
    logout,
  }
}
