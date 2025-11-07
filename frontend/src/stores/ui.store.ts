import { create } from 'zustand'

/**
 * Zustand Store: UI State
 *
 * Global state for UI-related concerns like modals, toasts, etc.
 */

interface UIState {
  isLoginModalOpen: boolean
  isCreateUserModalOpen: boolean
  sidebarOpen: boolean

  // Actions
  openLoginModal: () => void
  closeLoginModal: () => void
  openCreateUserModal: () => void
  closeCreateUserModal: () => void
  toggleSidebar: () => void
}

export const useUIStore = create<UIState>((set) => ({
  isLoginModalOpen: false,
  isCreateUserModalOpen: false,
  sidebarOpen: true,

  openLoginModal: () => set({ isLoginModalOpen: true }),
  closeLoginModal: () => set({ isLoginModalOpen: false }),
  openCreateUserModal: () => set({ isCreateUserModalOpen: true }),
  closeCreateUserModal: () => set({ isCreateUserModalOpen: false }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}))
