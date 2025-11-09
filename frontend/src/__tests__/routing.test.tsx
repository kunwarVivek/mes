import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { RouterProvider } from '@tanstack/react-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

/**
 * TanStack Router Tests
 *
 * Following TDD principles:
 * - Test route rendering
 * - Test protected routes redirect
 * - Test navigation works
 * - Test type safety
 */

// Mock auth store with getState
const mockAuthStore = {
  getState: vi.fn(),
}

vi.mock('../features/auth/stores/authStore', () => ({
  useAuthStore: Object.assign(vi.fn(), { getState: () => mockAuthStore.getState() }),
}))

// Mock pages to simplify testing
vi.mock('../pages/UsersPage', () => ({
  UsersPage: () => <div>Users Page</div>,
}))

vi.mock('../features/auth/pages/LoginPage', () => ({
  LoginPage: () => <div>Login Page</div>,
}))

vi.mock('../features/materials/pages/MaterialsPage', () => ({
  MaterialsPage: () => <div>Materials Page</div>,
}))

vi.mock('../pages/DashboardPage', () => ({
  DashboardPage: () => <div>Dashboard Page</div>,
}))

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

describe('TanStack Router', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Public Routes', () => {
    it('should render login page at /login', async () => {
      // Arrange: Import router dynamically
      const { router } = await import('../router')
      const queryClient = createTestQueryClient()

      // Mock unauthenticated state
      mockAuthStore.getState.mockReturnValue({
        isAuthenticated: false,
        user: null,
        token: null,
        isLoading: false,
        setUser: vi.fn(),
        clearAuth: vi.fn(),
        setLoading: vi.fn(),
      })

      // Navigate to login
      router.navigate({ to: '/login' })

      // Act
      render(
        <QueryClientProvider client={queryClient}>
          <RouterProvider router={router} />
        </QueryClientProvider>
      )

      // Assert
      await waitFor(() => {
        expect(screen.getByText('Login Page')).toBeInTheDocument()
      })
    })

    it('should render dashboard at root path /', async () => {
      // Arrange
      const { router } = await import('../router')
      const queryClient = createTestQueryClient()

      mockAuthStore.getState.mockReturnValue({
        isAuthenticated: true,
        user: { id: '1', email: 'test@test.com', name: 'Test User' },
        token: 'test-token',
        isLoading: false,
        setUser: vi.fn(),
        clearAuth: vi.fn(),
        setLoading: vi.fn(),
      })

      // Navigate to root
      router.navigate({ to: '/' })

      // Act
      render(
        <QueryClientProvider client={queryClient}>
          <RouterProvider router={router} />
        </QueryClientProvider>
      )

      // Assert
      await waitFor(() => {
        expect(screen.getByText('Dashboard Page')).toBeInTheDocument()
      })
    })
  })

  describe('Protected Routes', () => {
    it('should redirect unauthenticated users from protected routes to /login', async () => {
      // Arrange
      const { router } = await import('../router')
      const queryClient = createTestQueryClient()

      // Mock unauthenticated state
      mockAuthStore.getState.mockReturnValue({
        isAuthenticated: false,
        user: null,
        token: null,
        isLoading: false,
        setUser: vi.fn(),
        clearAuth: vi.fn(),
        setLoading: vi.fn(),
      })

      // Try to navigate to protected route
      router.navigate({ to: '/materials' })

      // Act
      render(
        <QueryClientProvider client={queryClient}>
          <RouterProvider router={router} />
        </QueryClientProvider>
      )

      // Assert - should redirect to login
      await waitFor(() => {
        expect(screen.getByText('Login Page')).toBeInTheDocument()
      })
    })

    it('should allow authenticated users to access protected routes', async () => {
      // Arrange
      const { router } = await import('../router')
      const queryClient = createTestQueryClient()

      // Mock authenticated state
      mockAuthStore.getState.mockReturnValue({
        isAuthenticated: true,
        user: { id: '1', email: 'test@test.com', name: 'Test User' },
        token: 'test-token',
        isLoading: false,
        setUser: vi.fn(),
        clearAuth: vi.fn(),
        setLoading: vi.fn(),
      })

      // Navigate to protected route
      router.navigate({ to: '/materials' })

      // Act
      render(
        <QueryClientProvider client={queryClient}>
          <RouterProvider router={router} />
        </QueryClientProvider>
      )

      // Assert
      await waitFor(() => {
        expect(screen.getByText('Materials Page')).toBeInTheDocument()
      })
    })
  })

  describe('Route Configuration', () => {
    it('should have router instance with correct type', async () => {
      // Arrange & Act
      const { router } = await import('../router')

      // Assert
      expect(router).toBeDefined()
      expect(router.state).toBeDefined()
    })

    it('should register routes in type system', async () => {
      // This test verifies TypeScript compilation
      // If types are wrong, the test file won't compile
      const { router } = await import('../router')

      // Type-safe navigation
      router.navigate({ to: '/' })
      router.navigate({ to: '/login' })
      router.navigate({ to: '/materials' })

      expect(router).toBeDefined()
    })
  })
})
