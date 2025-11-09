import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useServiceWorker } from '../useServiceWorker'

describe('useServiceWorker', () => {
  const originalNavigator = global.navigator
  const originalLocation = global.window.location

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks()

    // Mock HTTPS location by default
    delete (window as any).location
    window.location = {
      protocol: 'https:',
      hostname: 'example.com',
    } as any
  })

  afterEach(() => {
    // Restore navigator
    Object.defineProperty(global, 'navigator', {
      value: originalNavigator,
      configurable: true,
    })

    // Restore location
    Object.defineProperty(global.window, 'location', {
      value: originalLocation,
      configurable: true,
    })

    // Restore import.meta.env
    vi.unstubAllEnvs()
  })

  describe('Registration', () => {
    it('should register service worker in production mode', async () => {
      vi.stubEnv('MODE', 'production')

      const registerMock = vi.fn().mockResolvedValue({
        installing: null,
        waiting: null,
        active: { state: 'activated' },
        addEventListener: vi.fn(),
      })

      Object.defineProperty(global, 'navigator', {
        value: {
          serviceWorker: {
            register: registerMock,
          },
        },
        configurable: true,
      })

      const { result } = renderHook(() => useServiceWorker())

      await waitFor(() => {
        expect(registerMock).toHaveBeenCalledWith('/service-worker.js', {
          scope: '/',
        })
      })

      expect(result.current.isRegistered).toBe(true)
      expect(result.current.error).toBeNull()
    })

    it('should not register service worker in development mode', async () => {
      vi.stubEnv('MODE', 'development')

      const registerMock = vi.fn()
      Object.defineProperty(global, 'navigator', {
        value: {
          serviceWorker: {
            register: registerMock,
          },
        },
        configurable: true,
      })

      const { result } = renderHook(() => useServiceWorker())

      expect(registerMock).not.toHaveBeenCalled()
      expect(result.current.isRegistered).toBe(false)
    })

    it('should not register if service worker not supported', () => {
      vi.stubEnv('MODE', 'production')

      Object.defineProperty(global, 'navigator', {
        value: {},
        configurable: true,
      })

      const { result } = renderHook(() => useServiceWorker())

      expect(result.current.isRegistered).toBe(false)
      expect(result.current.error).toBeNull()
    })

    it('should handle registration errors gracefully', async () => {
      vi.stubEnv('MODE', 'production')

      const errorMessage = 'Registration failed'
      const registerMock = vi.fn().mockRejectedValue(new Error(errorMessage))

      Object.defineProperty(global, 'navigator', {
        value: {
          serviceWorker: {
            register: registerMock,
          },
        },
        configurable: true,
      })

      const { result } = renderHook(() => useServiceWorker())

      await waitFor(() => {
        expect(result.current.error).toBe(errorMessage)
      })

      expect(result.current.isRegistered).toBe(false)
    })
  })

  describe('Update Handling', () => {
    it('should detect when new service worker is waiting', async () => {
      vi.stubEnv('MODE', 'production')

      const registration = {
        installing: null,
        waiting: {
          state: 'installed',
          postMessage: vi.fn(),
        },
        active: { state: 'activated' },
        addEventListener: vi.fn(),
      }

      const registerMock = vi.fn().mockResolvedValue(registration)

      Object.defineProperty(global, 'navigator', {
        value: {
          serviceWorker: {
            register: registerMock,
          },
        },
        configurable: true,
      })

      const { result } = renderHook(() => useServiceWorker())

      await waitFor(() => {
        expect(result.current.isUpdateAvailable).toBe(true)
      })
    })

    it('should activate waiting service worker on update', async () => {
      vi.stubEnv('MODE', 'production')

      const postMessageMock = vi.fn()
      const addEventListenerMock = vi.fn()
      const registration = {
        installing: null,
        waiting: {
          state: 'installed',
          postMessage: postMessageMock,
        },
        active: { state: 'activated' },
        addEventListener: vi.fn(),
      }

      const registerMock = vi.fn().mockResolvedValue(registration)

      Object.defineProperty(global, 'navigator', {
        value: {
          serviceWorker: {
            register: registerMock,
            addEventListener: addEventListenerMock,
          },
        },
        configurable: true,
      })

      const { result } = renderHook(() => useServiceWorker())

      await waitFor(() => {
        expect(result.current.isUpdateAvailable).toBe(true)
      })

      result.current.activateUpdate()

      expect(postMessageMock).toHaveBeenCalledWith({ type: 'SKIP_WAITING' })
    })
  })

  describe('Security', () => {
    it('should only register with HTTPS in production', async () => {
      vi.stubEnv('MODE', 'production')

      delete (window as any).location
      window.location = {
        protocol: 'http:',
        hostname: 'example.com',
      } as any

      const registerMock = vi.fn()
      Object.defineProperty(global, 'navigator', {
        value: {
          serviceWorker: {
            register: registerMock,
          },
        },
        configurable: true,
      })

      renderHook(() => useServiceWorker())

      expect(registerMock).not.toHaveBeenCalled()
    })

    it('should allow localhost with HTTP', async () => {
      vi.stubEnv('MODE', 'production')

      delete (window as any).location
      window.location = {
        protocol: 'http:',
        hostname: 'localhost',
      } as any

      const registerMock = vi.fn().mockResolvedValue({
        installing: null,
        waiting: null,
        active: { state: 'activated' },
        addEventListener: vi.fn(),
      })

      Object.defineProperty(global, 'navigator', {
        value: {
          serviceWorker: {
            register: registerMock,
          },
        },
        configurable: true,
      })

      const { result } = renderHook(() => useServiceWorker())

      await waitFor(() => {
        expect(registerMock).toHaveBeenCalled()
      })

      expect(result.current.isRegistered).toBe(true)
    })
  })
})
