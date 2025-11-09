import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import type { AxiosError, InternalAxiosRequestConfig } from 'axios'

/**
 * API Client Interceptor Tests
 *
 * Following TDD principles:
 * RED -> GREEN -> REFACTOR
 *
 * Tests cover:
 * 1. Request interceptor adds Authorization header
 * 2. Request interceptor adds X-Organization-ID header
 * 3. Request interceptor adds X-Plant-ID header
 * 4. Response interceptor handles 401 with token refresh
 * 5. Response interceptor logs out on refresh failure
 */

// Mock Zustand store state
let mockState: any = {}
const mockGetState = vi.fn(() => mockState)

// Mock Zustand store
vi.mock('../stores/auth.store', () => ({
  useAuthStore: Object.assign(
    () => mockState,
    {
      getState: mockGetState,
      setState: vi.fn(),
      subscribe: vi.fn(),
      destroy: vi.fn(),
    }
  ),
}))

// We'll need to re-import apiClient after mocks are set up
let apiClient: any

describe('API Client Interceptors', () => {
  beforeEach(async () => {
    vi.clearAllMocks()

    // Re-import to apply interceptors with fresh mocks
    const module = await import('../lib/api-client')
    apiClient = module.default
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Request Interceptor - JWT Token', () => {
    it('should add Authorization header when token exists', async () => {
      // Arrange
      mockState = {
        accessToken: 'test-jwt-token',
        refreshToken: 'test-refresh-token',
        user: null,
        isAuthenticated: true,
        currentOrg: null,
        currentPlant: null,
      }

      // Create a mock request
      const config: InternalAxiosRequestConfig = {
        headers: {} as any,
        method: 'GET',
        url: '/test',
      } as InternalAxiosRequestConfig

      // Act
      const requestInterceptor = apiClient.interceptors.request.handlers[0]
      const result = await requestInterceptor.fulfilled(config)

      // Assert
      expect(result.headers.Authorization).toBe('Bearer test-jwt-token')
    })

    it('should NOT add Authorization header when token is null', async () => {
      // Arrange
      mockState = {
        accessToken: null,
        refreshToken: null,
        user: null,
        isAuthenticated: false,
        currentOrg: null,
        currentPlant: null,
      }

      const config: InternalAxiosRequestConfig = {
        headers: {} as any,
        method: 'GET',
        url: '/test',
      } as InternalAxiosRequestConfig

      // Act
      const requestInterceptor = apiClient.interceptors.request.handlers[0]
      const result = await requestInterceptor.fulfilled(config)

      // Assert
      expect(result.headers.Authorization).toBeUndefined()
    })
  })

  describe('Request Interceptor - Tenant Context', () => {
    it('should add X-Organization-ID header when currentOrg exists', async () => {
      // Arrange
      mockState = {
        accessToken: 'token',
        refreshToken: 'refresh',
        user: null,
        isAuthenticated: true,
        currentOrg: { id: 123, org_code: 'ORG001', org_name: 'Test Org' },
        currentPlant: null,
      }

      const config: InternalAxiosRequestConfig = {
        headers: {} as any,
        method: 'GET',
        url: '/test',
      } as InternalAxiosRequestConfig

      // Act
      const requestInterceptor = apiClient.interceptors.request.handlers[0]
      const result = await requestInterceptor.fulfilled(config)

      // Assert
      expect(result.headers['X-Organization-ID']).toBe('123')
    })

    it('should add X-Plant-ID header when currentPlant exists', async () => {
      // Arrange
      mockState = {
        accessToken: 'token',
        refreshToken: 'refresh',
        user: null,
        isAuthenticated: true,
        currentOrg: null,
        currentPlant: { id: 456, plant_code: 'PLT001', plant_name: 'Test Plant' },
      }

      const config: InternalAxiosRequestConfig = {
        headers: {} as any,
        method: 'GET',
        url: '/test',
      } as InternalAxiosRequestConfig

      // Act
      const requestInterceptor = apiClient.interceptors.request.handlers[0]
      const result = await requestInterceptor.fulfilled(config)

      // Assert
      expect(result.headers['X-Plant-ID']).toBe('456')
    })

    it('should add both tenant headers when both exist', async () => {
      // Arrange
      mockState = {
        accessToken: 'token',
        refreshToken: 'refresh',
        user: null,
        isAuthenticated: true,
        currentOrg: { id: 123, org_code: 'ORG001', org_name: 'Test Org' },
        currentPlant: { id: 456, plant_code: 'PLT001', plant_name: 'Test Plant' },
      }

      const config: InternalAxiosRequestConfig = {
        headers: {} as any,
        method: 'GET',
        url: '/test',
      } as InternalAxiosRequestConfig

      // Act
      const requestInterceptor = apiClient.interceptors.request.handlers[0]
      const result = await requestInterceptor.fulfilled(config)

      // Assert
      expect(result.headers['X-Organization-ID']).toBe('123')
      expect(result.headers['X-Plant-ID']).toBe('456')
      expect(result.headers.Authorization).toBe('Bearer token')
    })
  })

  describe('Response Interceptor - 401 Handling', () => {
    it('should attempt token refresh on 401 error', async () => {
      // Arrange
      const mockPost = vi.spyOn(axios, 'post').mockResolvedValue({
        data: { access_token: 'new-token' },
      })

      const mockSetTokens = vi.fn()
      mockState = {
        accessToken: 'old-token',
        refreshToken: 'refresh-token',
        user: null,
        isAuthenticated: true,
        setTokens: mockSetTokens,
      }

      const error: Partial<AxiosError> = {
        config: {
          headers: {} as any,
          _retry: false,
        } as InternalAxiosRequestConfig,
        response: {
          status: 401,
          data: {},
          statusText: 'Unauthorized',
          headers: {},
          config: {} as InternalAxiosRequestConfig,
        },
      }

      // Act
      const responseInterceptor = apiClient.interceptors.response.handlers[0]

      try {
        await responseInterceptor.rejected(error)
      } catch (e) {
        // Expected to catch if retry fails
      }

      // Assert
      expect(mockPost).toHaveBeenCalledWith(
        expect.stringContaining('/auth/refresh'),
        { refresh_token: 'refresh-token' }
      )
    })

    it('should logout user when token refresh fails', async () => {
      // Arrange
      const mockLogout = vi.fn()

      vi.spyOn(axios, 'post').mockRejectedValue(new Error('Refresh failed'))

      mockState = {
        accessToken: 'old-token',
        refreshToken: 'refresh-token',
        user: null,
        isAuthenticated: true,
        logout: mockLogout,
      }

      // Mock window.location
      delete (window as any).location
      window.location = { href: '' } as any

      const error: Partial<AxiosError> = {
        config: {
          headers: {} as any,
          _retry: false,
        } as InternalAxiosRequestConfig,
        response: {
          status: 401,
          data: {},
          statusText: 'Unauthorized',
          headers: {},
          config: {} as InternalAxiosRequestConfig,
        },
      }

      // Act
      const responseInterceptor = apiClient.interceptors.response.handlers[0]

      try {
        await responseInterceptor.rejected(error)
      } catch (e) {
        // Expected to reject
      }

      // Assert
      expect(mockLogout).toHaveBeenCalled()
      expect(window.location.href).toBe('/login')
    })

    it('should not retry if request already has _retry flag', async () => {
      // Arrange
      const mockPost = vi.spyOn(axios, 'post')

      const error: Partial<AxiosError> = {
        config: {
          headers: {} as any,
          _retry: true, // Already retried
        } as InternalAxiosRequestConfig,
        response: {
          status: 401,
          data: {},
          statusText: 'Unauthorized',
          headers: {},
          config: {} as InternalAxiosRequestConfig,
        },
      }

      // Act
      const responseInterceptor = apiClient.interceptors.response.handlers[0]

      try {
        await responseInterceptor.rejected(error)
      } catch (e) {
        // Expected to reject
      }

      // Assert - should NOT call refresh endpoint
      expect(mockPost).not.toHaveBeenCalled()
    })

    it('should pass through non-401 errors', async () => {
      // Arrange
      const error: Partial<AxiosError> = {
        config: {
          headers: {} as any,
        } as InternalAxiosRequestConfig,
        response: {
          status: 500,
          data: { error: 'Server error' },
          statusText: 'Internal Server Error',
          headers: {},
          config: {} as InternalAxiosRequestConfig,
        },
      }

      // Act
      const responseInterceptor = apiClient.interceptors.response.handlers[0]

      // Assert
      await expect(responseInterceptor.rejected(error)).rejects.toEqual(error)
    })
  })
})
