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

      login: (user, accessToken, refreshToken) =>
        set({
          user,
          accessToken,
          refreshToken,
          isAuthenticated: true,
        }),

      logout: () =>
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          currentOrg: null,
          currentPlant: null,
        }),

      updateUser: (updatedUser) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...updatedUser } : null,
        })),

      setTokens: (accessToken, refreshToken) =>
        set((state) => ({
          accessToken,
          refreshToken: refreshToken ?? state.refreshToken,
          isAuthenticated: !!accessToken,
        })),

      setCurrentOrg: (org) =>
        set({ currentOrg: org }),

      setCurrentPlant: (plant) =>
        set({ currentPlant: plant }),
    }),
    {
      name: 'auth-storage', // localStorage key
    }
  )
)
