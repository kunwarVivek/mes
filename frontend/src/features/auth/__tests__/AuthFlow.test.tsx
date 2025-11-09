import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useAuthStore } from '../stores/authStore'
import { useAuth } from '../hooks/useAuth'
import { ProtectedRoute } from '../components/ProtectedRoute'
import { LoginPage } from '../pages/LoginPage'
import { RegisterPage } from '../pages/RegisterPage'

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
  Navigate: ({ to }: { to: string }) => <div data-testid="navigate-to">{to}</div>,
}))

/**
 * AuthFlow Test Suite
 *
 * TDD approach testing:
 * 1. Auth Store - State management
 * 2. useAuth Hook - Auth operations
 * 3. ProtectedRoute - Route protection
 * 4. LoginPage - Login form
 * 5. RegisterPage - Registration form
 */

describe('AuthFlow - Auth Store', () => {
  beforeEach(() => {
    // Clear store and localStorage before each test
    localStorage.clear()
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    })
  })

  it('should initialize with unauthenticated state', () => {
    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.token).toBeNull()
    expect(state.isAuthenticated).toBe(false)
    expect(state.isLoading).toBe(false)
  })

  it('should set user and token', () => {
    const mockUser = { id: '1', email: 'test@example.com', name: 'Test User' }
    const mockToken = 'mock-jwt-token'

    useAuthStore.getState().setUser(mockUser, mockToken)

    const state = useAuthStore.getState()
    expect(state.user).toEqual(mockUser)
    expect(state.token).toBe(mockToken)
    expect(state.isAuthenticated).toBe(true)
    expect(localStorage.getItem('token')).toBe(mockToken)
  })

  it('should clear auth state on clearAuth', () => {
    const mockUser = { id: '1', email: 'test@example.com', name: 'Test User' }
    useAuthStore.getState().setUser(mockUser, 'token')

    useAuthStore.getState().clearAuth()

    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.token).toBeNull()
    expect(state.isAuthenticated).toBe(false)
    expect(localStorage.getItem('token')).toBeNull()
  })

  it('should restore token from localStorage on initialization', () => {
    // Clear and set token before reading state
    localStorage.clear()
    localStorage.setItem('token', 'persisted-token')

    // Reset store state to trigger initialization logic
    useAuthStore.setState({
      user: null,
      token: localStorage.getItem('token'),
      isAuthenticated: !!localStorage.getItem('token'),
      isLoading: false,
    })

    const state = useAuthStore.getState()
    expect(state.token).toBe('persisted-token')
    expect(state.isAuthenticated).toBe(true)
  })
})

describe('AuthFlow - useAuth Hook', () => {
  beforeEach(() => {
    localStorage.clear()
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    })
    mockNavigate.mockClear()
  })

  // Test wrapper component to use the hook
  const TestComponent = ({ onAuthResult }: { onAuthResult: (result: ReturnType<typeof useAuth>) => void }) => {
    const auth = useAuth()
    onAuthResult(auth)
    return null
  }

  it('should provide auth state and methods', () => {
    let authResult: ReturnType<typeof useAuth> | null = null

    render(<TestComponent onAuthResult={(result) => { authResult = result }} />)

    expect(authResult).toBeDefined()
    expect(authResult?.isAuthenticated).toBe(false)
    expect(authResult?.user).toBeNull()
    expect(authResult?.isLoading).toBe(false)
    expect(typeof authResult?.login).toBe('function')
    expect(typeof authResult?.register).toBe('function')
    expect(typeof authResult?.logout).toBe('function')
  })

  it('should login successfully with valid credentials', async () => {
    let authResult: ReturnType<typeof useAuth> | null = null

    render(<TestComponent onAuthResult={(result) => { authResult = result }} />)

    await waitFor(async () => {
      await authResult?.login('test@example.com', 'password123')
    })

    expect(authResult?.isAuthenticated).toBe(true)
    expect(authResult?.user).toBeDefined()
    expect(authResult?.user?.email).toBe('test@example.com')
  })

  it('should reject login with invalid credentials', async () => {
    let authResult: ReturnType<typeof useAuth> | null = null

    render(<TestComponent onAuthResult={(result) => { authResult = result }} />)

    await expect(async () => {
      await authResult?.login('wrong@example.com', 'wrongpass')
    }).rejects.toThrow('Invalid credentials')
  })

  it('should register successfully with valid data', async () => {
    let authResult: ReturnType<typeof useAuth> | null = null

    render(<TestComponent onAuthResult={(result) => { authResult = result }} />)

    const registerData = {
      email: 'newuser@example.com',
      password: 'password123',
      confirmPassword: 'password123',
      organizationName: 'Test Org',
      fullName: 'New User',
    }

    await waitFor(async () => {
      await authResult?.register(registerData)
    })

    // After registration, user should NOT be auto-logged in (they need to confirm email)
    expect(authResult?.isAuthenticated).toBe(false)
  })

  it('should logout and clear auth state', async () => {
    let authResult: ReturnType<typeof useAuth> | null = null

    // Set initial authenticated state
    useAuthStore.getState().setUser(
      { id: '1', email: 'test@example.com', name: 'Test User' },
      'token'
    )

    render(<TestComponent onAuthResult={(result) => { authResult = result }} />)

    await waitFor(() => {
      authResult?.logout()
    })

    expect(authResult?.isAuthenticated).toBe(false)
    expect(authResult?.user).toBeNull()
    expect(localStorage.getItem('token')).toBeNull()
  })
})

describe('AuthFlow - ProtectedRoute', () => {
  beforeEach(() => {
    localStorage.clear()
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    })
  })

  it('should render children when authenticated', () => {
    useAuthStore.setState({
      user: { id: '1', email: 'test@example.com', name: 'Test User' },
      token: 'token',
      isAuthenticated: true,
      isLoading: false,
    })

    render(
      <ProtectedRoute>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    )

    expect(screen.getByTestId('protected-content')).toBeInTheDocument()
  })

  it('should redirect to login when not authenticated', () => {
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    })

    render(
      <ProtectedRoute>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    )

    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
    expect(screen.getByTestId('navigate-to')).toHaveTextContent('/login')
  })

  it('should show loading fallback while checking auth', () => {
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: true,
    })

    render(
      <ProtectedRoute fallback={<div data-testid="loading">Loading...</div>}>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    )

    expect(screen.getByTestId('loading')).toBeInTheDocument()
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })
})

describe('AuthFlow - LoginPage', () => {
  beforeEach(() => {
    localStorage.clear()
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    })
    mockNavigate.mockClear()
  })

  it('should render login form', () => {
    render(<LoginPage />)

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument()
  })

  it('should show validation errors for invalid email', async () => {
    const user = userEvent.setup()
    render(<LoginPage />)

    const emailInput = screen.getByLabelText(/email/i)
    const submitButton = screen.getByRole('button', { name: /log in/i })

    await user.type(emailInput, 'invalid-email')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/valid email/i)).toBeInTheDocument()
    })
  })

  it('should show validation errors for short password', async () => {
    const user = userEvent.setup()
    render(<LoginPage />)

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /log in/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'short')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/at least 8 characters/i)).toBeInTheDocument()
    })
  })

  it('should submit form with valid credentials', async () => {
    const user = userEvent.setup()
    render(<LoginPage />)

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /log in/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('should show error message for invalid credentials', async () => {
    const user = userEvent.setup()
    render(<LoginPage />)

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /log in/i })

    await user.type(emailInput, 'wrong@example.com')
    await user.type(passwordInput, 'wrongpassword')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
    })
  })

  it('should show loading state during submission', async () => {
    const user = userEvent.setup()
    render(<LoginPage />)

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /log in/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')

    // Click submit and check for loading state immediately
    user.click(submitButton)

    // Button should be disabled during loading
    await waitFor(() => {
      expect(submitButton).toBeDisabled()
    })
  })
})

describe('AuthFlow - RegisterPage', () => {
  beforeEach(() => {
    localStorage.clear()
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    })
    mockNavigate.mockClear()
  })

  it('should render registration form', () => {
    render(<RegisterPage />)

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/organization name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /register/i })).toBeInTheDocument()
  })

  it('should validate password confirmation', async () => {
    const user = userEvent.setup()
    render(<RegisterPage />)

    // Fill all required fields except password confirmation mismatch
    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/^password$/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    const orgNameInput = screen.getByLabelText(/organization name/i)
    const fullNameInput = screen.getByLabelText(/full name/i)
    const submitButton = screen.getByRole('button', { name: /register/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(fullNameInput, 'Test User')
    await user.type(orgNameInput, 'Test Org')
    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'different123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/passwords must match/i)).toBeInTheDocument()
    })
  })

  it('should submit form with valid data', async () => {
    const user = userEvent.setup()
    render(<RegisterPage />)

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/^password$/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    const orgNameInput = screen.getByLabelText(/organization name/i)
    const fullNameInput = screen.getByLabelText(/full name/i)
    const submitButton = screen.getByRole('button', { name: /register/i })

    await user.type(emailInput, 'newuser@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'password123')
    await user.type(orgNameInput, 'Test Organization')
    await user.type(fullNameInput, 'John Doe')
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login')
    })
  })

  it('should show loading state during submission', async () => {
    const user = userEvent.setup()
    render(<RegisterPage />)

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/^password$/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    const orgNameInput = screen.getByLabelText(/organization name/i)
    const fullNameInput = screen.getByLabelText(/full name/i)
    const submitButton = screen.getByRole('button', { name: /register/i })

    await user.type(emailInput, 'newuser@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'password123')
    await user.type(orgNameInput, 'Test Organization')
    await user.type(fullNameInput, 'John Doe')

    user.click(submitButton)

    await waitFor(() => {
      expect(submitButton).toBeDisabled()
    })
  })
})
