import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/**
 * Zustand Store: Authentication State
 *
 * Global state management for authentication.
 * Replaces prop drilling with centralized state.
 * Includes tenant context for RLS (Row Level Security).
 */

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

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  currentOrg: Organization | null
  currentPlant: Plant | null

  // Actions
  login: (user: User, accessToken: string, refreshToken: string) => void
  logout: () => void
  updateUser: (user: Partial<User>) => void
  setTokens: (accessToken: string, refreshToken?: string) => void
  setCurrentOrg: (org: Organization | null) => void
  setCurrentPlant: (plant: Plant | null) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      currentOrg: null,
      currentPlant: null,

      login: (user, accessToken, refreshToken) => {
        // Sync tokens to localStorage for API client
        if (typeof window !== 'undefined') {
          localStorage.setItem('access_token', accessToken)
          localStorage.setItem('refresh_token', refreshToken)
        }

        set({
          user,
          accessToken,
          refreshToken,
          isAuthenticated: true,
        })
      },

      logout: () => {
        // Clear tokens from localStorage
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('current_organization_id')
          localStorage.removeItem('current_plant_id')
        }

        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          currentOrg: null,
          currentPlant: null,
        })
      },

      updateUser: (updatedUser) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...updatedUser } : null,
        })),

      setTokens: (accessToken, refreshToken) => {
        // Sync tokens to localStorage for API client
        if (typeof window !== 'undefined') {
          localStorage.setItem('access_token', accessToken)
          if (refreshToken) {
            localStorage.setItem('refresh_token', refreshToken)
          }
        }

        set((state) => ({
          accessToken,
          refreshToken: refreshToken ?? state.refreshToken,
          isAuthenticated: !!accessToken,
        }))
      },

      setCurrentOrg: (org) => {
        // Sync org ID to localStorage for API client RLS context
        if (typeof window !== 'undefined' && org) {
          localStorage.setItem('current_organization_id', org.id.toString())
        } else if (typeof window !== 'undefined') {
          localStorage.removeItem('current_organization_id')
        }

        set({ currentOrg: org })
      },

      setCurrentPlant: (plant) => {
        // Sync plant ID to localStorage for API client RLS context
        if (typeof window !== 'undefined' && plant) {
          localStorage.setItem('current_plant_id', plant.id.toString())
        } else if (typeof window !== 'undefined') {
          localStorage.removeItem('current_plant_id')
        }

        set({ currentPlant: plant })
      },
    }),
    {
      name: 'auth-storage', // localStorage key
    }
  )
)
