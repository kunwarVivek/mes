import { create } from 'zustand'

/**
 * Auth Store
 *
 * Central authentication state management using Zustand:
 * - Single Responsibility: Authentication state
 * - Persistence: Token stored in localStorage
 * - State: user, token, isAuthenticated, isLoading
 */

export interface User {
  id: string
  email: string
  name: string
}

export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  setUser: (user: User, token: string) => void
  clearAuth: () => void
  setLoading: (isLoading: boolean) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: typeof window !== 'undefined' ? localStorage.getItem('token') : null,
  isAuthenticated: typeof window !== 'undefined' ? !!localStorage.getItem('token') : false,
  isLoading: false,

  setUser: (user: User, token: string) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('token', token)
    }
    set({ user, token, isAuthenticated: true })
  },

  clearAuth: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token')
    }
    set({ user: null, token: null, isAuthenticated: false })
  },

  setLoading: (isLoading: boolean) => {
    set({ isLoading })
  },
}))
