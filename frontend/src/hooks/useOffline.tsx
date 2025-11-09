import { useState, useEffect, useCallback, useRef } from 'react'

export interface Action {
  id: string
  type: string
  payload: unknown
  timestamp: number
}

export interface UseOfflineOptions {
  onSync?: (action: Action) => Promise<void>
  storageKey?: string
  parallelSync?: boolean
}

export interface UseOfflineReturn {
  isOffline: boolean
  queueAction: (type: string, payload: unknown) => void
  syncQueue: () => Promise<void>
  queuedActions: Action[]
  clearQueue: () => void
}

const DEFAULT_STORAGE_KEY = 'offline-queue'

/**
 * Sanitize storage key to prevent injection attacks
 */
function sanitizeStorageKey(key: string): string {
  if (!key || typeof key !== 'string') return DEFAULT_STORAGE_KEY
  if (key.startsWith('__') || key.includes('proto')) return DEFAULT_STORAGE_KEY
  return key.trim()
}

/**
 * Sanitize payload for safe localStorage storage
 */
function sanitizePayload(payload: unknown): unknown {
  try {
    const serialized = JSON.stringify(payload)
    const parsed = JSON.parse(serialized)

    if (parsed && typeof parsed === 'object') {
      delete parsed.__proto__
      delete parsed.constructor
      delete parsed.prototype
    }
    return parsed
  } catch {
    console.warn('Invalid payload detected, using null')
    return null
  }
}

/**
 * Production-safe error logging
 */
function logError(message: string, error?: unknown) {
  if (process.env.NODE_ENV === 'development') {
    console.error(message, error)
  } else {
    console.error(message)
  }
}

/**
 * Offline detection and sync queue management hook for PWA
 *
 * Features:
 * - Detects online/offline status via navigator.onLine
 * - Queues actions when offline with localStorage persistence
 * - Auto-syncs queued actions when connection restored
 * - Handles sync failures gracefully with retry support
 *
 * @param options - Configuration options
 * @returns Offline state and queue management functions
 */
export function useOffline(options: UseOfflineOptions = {}): UseOfflineReturn {
  const { onSync, storageKey = DEFAULT_STORAGE_KEY, parallelSync = false } = options
  const safeStorageKey = sanitizeStorageKey(storageKey)

  const [isOffline, setIsOffline] = useState(!navigator.onLine)
  const [queuedActions, setQueuedActions] = useState<Action[]>(() => {
    return loadQueueFromStorage(safeStorageKey)
  })

  // Use ref to always have latest onSync callback without causing re-renders
  const onSyncRef = useRef(onSync)
  useEffect(() => {
    onSyncRef.current = onSync
  }, [onSync])

  // Persist queue to localStorage whenever it changes
  useEffect(() => {
    saveQueueToStorage(safeStorageKey, queuedActions)
  }, [queuedActions, safeStorageKey])

  /**
   * Sync all queued actions
   */
  const syncQueue = useCallback(async () => {
    // Get current queue state
    const currentQueue = await new Promise<Action[]>((resolve) => {
      setQueuedActions((queue) => {
        resolve(queue)
        return queue
      })
    })

    if (currentQueue.length === 0) {
      return
    }

    // If no onSync callback provided, just clear the queue
    if (!onSyncRef.current) {
      setQueuedActions([])
      return
    }

    const failedActions: Action[] = []

    // Process actions (parallel or sequential based on option)
    if (parallelSync) {
      const results = await Promise.allSettled(
        currentQueue.map(action => onSyncRef.current!(action))
      )
      results.forEach((result, index) => {
        if (result.status === 'rejected') {
          failedActions.push(currentQueue[index])
          logError('Failed to sync action', result.reason)
        }
      })
    } else {
      // Sequential processing for order-dependent actions
      for (const action of currentQueue) {
        try {
          await onSyncRef.current(action)
        } catch (error) {
          failedActions.push(action)
          logError('Failed to sync action', error)
        }
      }
    }

    // Update queue with only failed actions
    setQueuedActions(failedActions)
  }, [])

  /**
   * Queue an action for later sync
   */
  const queueAction = useCallback((type: string, payload: unknown) => {
    const action: Action = {
      id: generateActionId(),
      type,
      payload: sanitizePayload(payload),
      timestamp: Date.now(),
    }

    setQueuedActions((prev) => [...prev, action])
  }, [])

  // Use ref for syncQueue to avoid effect dependency issues
  const syncQueueRef = useRef(syncQueue)
  useEffect(() => {
    syncQueueRef.current = syncQueue
  }, [syncQueue])

  // Set up online/offline event listeners
  useEffect(() => {
    const handleOnline = () => {
      setIsOffline(false)
      // Auto-sync queue when going online
      syncQueueRef.current()
    }

    const handleOffline = () => {
      setIsOffline(true)
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  /**
   * Clear all queued actions
   */
  const clearQueue = useCallback(() => {
    setQueuedActions([])
    removeQueueFromStorage(safeStorageKey)
  }, [safeStorageKey])

  return {
    isOffline,
    queueAction,
    syncQueue,
    queuedActions,
    clearQueue,
  }
}

/**
 * Load queue from localStorage
 */
function loadQueueFromStorage(storageKey: string): Action[] {
  try {
    const stored = localStorage.getItem(storageKey)
    if (!stored) {
      return []
    }

    const parsed = JSON.parse(stored)
    return Array.isArray(parsed) ? parsed : []
  } catch (error) {
    // Handle corrupted data gracefully
    logError('Failed to load offline queue from localStorage', error)
    return []
  }
}

/**
 * Save queue to localStorage
 */
function saveQueueToStorage(storageKey: string, queue: Action[]): void {
  try {
    if (queue.length === 0) {
      localStorage.removeItem(storageKey)
    } else {
      localStorage.setItem(storageKey, JSON.stringify(queue))
    }
  } catch (error) {
    // Handle quota exceeded gracefully
    logError('Failed to save offline queue to localStorage', error)
  }
}

/**
 * Remove queue from localStorage
 */
function removeQueueFromStorage(storageKey: string): void {
  try {
    localStorage.removeItem(storageKey)
  } catch (error) {
    logError('Failed to remove offline queue from localStorage', error)
  }
}

/**
 * Generate unique action ID using crypto.randomUUID for collision resistance
 */
function generateActionId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  // Fallback for environments without crypto.randomUUID
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
}
