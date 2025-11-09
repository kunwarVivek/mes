import { useState, useEffect, useCallback } from 'react'

interface ServiceWorkerHook {
  isRegistered: boolean
  isUpdateAvailable: boolean
  error: string | null
  activateUpdate: () => void
}

/**
 * Service Worker registration hook for PWA functionality
 *
 * Features:
 * - Only registers in production mode (not dev/test)
 * - Enforces HTTPS security (except localhost)
 * - Detects and manages service worker updates
 * - Provides error handling and status tracking
 *
 * @returns Service worker state and control functions
 */
export function useServiceWorker(): ServiceWorkerHook {
  const [isRegistered, setIsRegistered] = useState(false)
  const [isUpdateAvailable, setIsUpdateAvailable] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [registration, setRegistration] = useState<ServiceWorkerRegistration | null>(null)

  useEffect(() => {
    // Early exit conditions
    if (!shouldRegisterServiceWorker()) {
      return
    }

    const registerServiceWorker = async () => {
      try {
        // Register service worker with root scope for full app coverage
        // Root scope (/) allows SW to intercept all requests in the app
        // This is intentional for offline-first PWA functionality
        const reg = await navigator.serviceWorker.register('/service-worker.js', {
          scope: '/',
        })

        setRegistration(reg)
        setIsRegistered(true)

        // Check for existing waiting worker
        if (reg.waiting) {
          setIsUpdateAvailable(true)
        }

        // Listen for new service worker updates
        setupUpdateListener(reg)
      } catch (err) {
        handleRegistrationError(err, setError, setIsRegistered)
      }
    }

    registerServiceWorker()
  }, [])

  const activateUpdate = useCallback(() => {
    if (!registration?.waiting) {
      return
    }

    // Tell service worker to skip waiting
    registration.waiting.postMessage({ type: 'SKIP_WAITING' })

    // Reload page when new service worker takes control
    // Using once:true flag provides automatic cleanup after first invocation
    navigator.serviceWorker.addEventListener(
      'controllerchange',
      () => {
        window.location.reload()
      },
      { once: true }
    )
  }, [registration])

  return {
    isRegistered,
    isUpdateAvailable,
    error,
    activateUpdate,
  }
}

/**
 * Determines if service worker should be registered
 * Checks environment mode, browser support, and security context
 */
function shouldRegisterServiceWorker(): boolean {
  // Only register in production
  if (import.meta.env.MODE !== 'production') {
    return false
  }

  // Check browser support
  if (!('serviceWorker' in navigator)) {
    return false
  }

  // Security: only HTTPS or localhost
  return isSecureContext()
}

/**
 * Validates secure context (HTTPS or localhost)
 */
function isSecureContext(): boolean {
  return (
    window.location.protocol === 'https:' ||
    window.location.hostname === 'localhost' ||
    window.location.hostname === '127.0.0.1'
  )
}

/**
 * Sets up listener for service worker updates
 */
function setupUpdateListener(registration: ServiceWorkerRegistration): void {
  registration.addEventListener('updatefound', () => {
    const newWorker = registration.installing

    if (!newWorker) {
      return
    }

    newWorker.addEventListener('statechange', () => {
      // Update available when new worker is installed and there's an active controller
      if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
        // Notify user that update is available
        // Component can show reload prompt to user
        window.dispatchEvent(new Event('swUpdateAvailable'))
      }
    })
  })
}

/**
 * Handles service worker registration errors with error type classification
 */
function handleRegistrationError(
  err: unknown,
  setError: (msg: string) => void,
  setIsRegistered: (registered: boolean) => void
): void {
  let errorMessage = 'Service worker registration failed'

  if (err instanceof Error) {
    // Classify error types for better UI feedback
    if (err.name === 'SecurityError') {
      errorMessage = 'Service worker registration blocked: HTTPS required'
    } else if (err.name === 'QuotaExceededError') {
      errorMessage = 'Service worker registration failed: Storage quota exceeded'
    } else if (err.message.includes('network')) {
      errorMessage = 'Service worker registration failed: Network error'
    } else {
      errorMessage = err.message
    }
  }

  setError(errorMessage)
  setIsRegistered(false)
  console.error('Service worker registration failed:', err)
}
