import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor, cleanup } from '@testing-library/react'
import { useOffline } from '../useOffline'

describe('useOffline', () => {
  const originalNavigator = global.navigator
  let onlineListeners: Array<() => void> = []
  let offlineListeners: Array<() => void> = []
  let localStorageMock: Record<string, string> = {}

  beforeEach(() => {
    // Clear actual browser localStorage (jsdom)
    localStorage.clear()

    // Clear all mocks first to remove previous spy implementations
    vi.restoreAllMocks()
    vi.clearAllMocks()

    onlineListeners = []
    offlineListeners = []
    localStorageMock = {} // Clear localStorage between tests

    // Mock navigator.onLine
    Object.defineProperty(global.navigator, 'onLine', {
      writable: true,
      value: true,
      configurable: true,
    })

    // Mock window event listeners
    vi.spyOn(window, 'addEventListener').mockImplementation((event, handler) => {
      if (event === 'online' && typeof handler === 'function') {
        onlineListeners.push(handler)
      }
      if (event === 'offline' && typeof handler === 'function') {
        offlineListeners.push(handler)
      }
    })

    vi.spyOn(window, 'removeEventListener').mockImplementation((event, handler) => {
      if (event === 'online' && typeof handler === 'function') {
        onlineListeners = onlineListeners.filter((h) => h !== handler)
      }
      if (event === 'offline' && typeof handler === 'function') {
        offlineListeners = offlineListeners.filter((h) => h !== handler)
      }
    })

    // Mock localStorage - recreate spies to use fresh localStorageMock reference
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => {
      return localStorageMock[key] || null
    })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation((key, value) => {
      localStorageMock[key] = value
    })
    vi.spyOn(Storage.prototype, 'removeItem').mockImplementation((key) => {
      delete localStorageMock[key]
    })
  })

  afterEach(() => {
    cleanup() // Clean up React components
    Object.defineProperty(global, 'navigator', {
      value: originalNavigator,
      configurable: true,
    })
    vi.restoreAllMocks()
  })

  describe('Offline Detection', () => {
    it('should detect initial online status', () => {
      Object.defineProperty(navigator, 'onLine', { value: true, writable: true })

      const { result } = renderHook(() => useOffline())

      expect(result.current.isOffline).toBe(false)
    })

    it('should detect initial offline status', () => {
      Object.defineProperty(navigator, 'onLine', { value: false, writable: true })

      const { result } = renderHook(() => useOffline())

      expect(result.current.isOffline).toBe(true)
    })

    it('should update status when going offline', () => {
      Object.defineProperty(navigator, 'onLine', { value: true, writable: true })

      const { result } = renderHook(() => useOffline())

      expect(result.current.isOffline).toBe(false)

      act(() => {
        Object.defineProperty(navigator, 'onLine', { value: false, writable: true })
        offlineListeners.forEach((listener) => listener())
      })

      expect(result.current.isOffline).toBe(true)
    })

    it('should update status when going online', () => {
      Object.defineProperty(navigator, 'onLine', { value: false, writable: true })

      const { result } = renderHook(() => useOffline())

      expect(result.current.isOffline).toBe(true)

      act(() => {
        Object.defineProperty(navigator, 'onLine', { value: true, writable: true })
        onlineListeners.forEach((listener) => listener())
      })

      expect(result.current.isOffline).toBe(false)
    })

    it('should cleanup event listeners on unmount', () => {
      const { unmount } = renderHook(() => useOffline())

      const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener')

      unmount()

      expect(removeEventListenerSpy).toHaveBeenCalledWith('online', expect.any(Function))
      expect(removeEventListenerSpy).toHaveBeenCalledWith('offline', expect.any(Function))
    })
  })

  describe('Action Queue Management', () => {
    it('should initialize with empty queue', () => {
      const { result } = renderHook(() => useOffline())

      expect(result.current.queuedActions).toEqual([])
    })

    it('should queue action when offline', () => {
      Object.defineProperty(navigator, 'onLine', { value: false, writable: true })

      const { result } = renderHook(() => useOffline())

      act(() => {
        result.current.queueAction('CREATE_USER', { name: 'John' })
      })

      expect(result.current.queuedActions).toHaveLength(1)
      expect(result.current.queuedActions[0]).toMatchObject({
        type: 'CREATE_USER',
        payload: { name: 'John' },
      })
      expect(result.current.queuedActions[0].id).toBeDefined()
      expect(result.current.queuedActions[0].timestamp).toBeDefined()
    })

    it('should allow queuing actions when online', () => {
      Object.defineProperty(navigator, 'onLine', { value: true, writable: true })

      const { result } = renderHook(() => useOffline())

      act(() => {
        result.current.queueAction('UPDATE_USER', { id: 1 })
      })

      expect(result.current.queuedActions).toHaveLength(1)
    })

    it('should persist queue to localStorage', () => {
      Object.defineProperty(navigator, 'onLine', { value: false, writable: true })

      const { result } = renderHook(() => useOffline())

      act(() => {
        result.current.queueAction('CREATE_USER', { name: 'Jane' })
      })

      const storedQueue = localStorage.getItem('offline-queue')
      expect(storedQueue).toBeDefined()

      const parsedQueue = JSON.parse(storedQueue!)
      expect(parsedQueue).toHaveLength(1)
      expect(parsedQueue[0].type).toBe('CREATE_USER')
    })

    it('should restore queue from localStorage on init', () => {
      const existingQueue = [
        {
          id: '123',
          type: 'DELETE_USER',
          payload: { id: 1 },
          timestamp: Date.now(),
        },
      ]

      localStorage.setItem('offline-queue', JSON.stringify(existingQueue))

      const { result } = renderHook(() => useOffline())

      expect(result.current.queuedActions).toHaveLength(1)
      expect(result.current.queuedActions[0].type).toBe('DELETE_USER')
    })

    it('should use custom storage key when provided', () => {
      const { result } = renderHook(() =>
        useOffline({ storageKey: 'custom-offline-queue' })
      )

      act(() => {
        result.current.queueAction('TEST_ACTION', { data: 'test' })
      })

      const storedQueue = localStorage.getItem('custom-offline-queue')
      expect(storedQueue).toBeDefined()
    })
  })

  describe('Queue Synchronization', () => {
    it('should auto-sync queue when going online', async () => {
      Object.defineProperty(navigator, 'onLine', { value: false, writable: true })

      const onSyncMock = vi.fn().mockResolvedValue(undefined)
      const { result } = renderHook(() => useOffline({ onSync: onSyncMock }))

      act(() => {
        result.current.queueAction('CREATE_USER', { name: 'Alice' })
        result.current.queueAction('UPDATE_USER', { id: 1 })
      })

      expect(result.current.queuedActions).toHaveLength(2)

      act(() => {
        Object.defineProperty(navigator, 'onLine', { value: true, writable: true })
        onlineListeners.forEach((listener) => listener())
      })

      await waitFor(() => {
        expect(onSyncMock).toHaveBeenCalledTimes(2)
        expect(result.current.queuedActions).toHaveLength(0)
      })
    })

    it('should call onSync callback for each action during sync', async () => {
      Object.defineProperty(navigator, 'onLine', { value: false, writable: true })

      const onSyncMock = vi.fn().mockResolvedValue(undefined)
      const { result } = renderHook(() => useOffline({ onSync: onSyncMock }))

      const action1 = { type: 'ACTION_1', payload: { data: 1 } }
      const action2 = { type: 'ACTION_2', payload: { data: 2 } }

      act(() => {
        result.current.queueAction(action1.type, action1.payload)
        result.current.queueAction(action2.type, action2.payload)
      })

      act(() => {
        result.current.syncQueue()
      })

      await waitFor(() => {
        expect(onSyncMock).toHaveBeenCalledWith(
          expect.objectContaining({ type: 'ACTION_1', payload: { data: 1 } })
        )
        expect(onSyncMock).toHaveBeenCalledWith(
          expect.objectContaining({ type: 'ACTION_2', payload: { data: 2 } })
        )
      })
    })

    it('should remove successfully synced actions from queue', async () => {
      Object.defineProperty(navigator, 'onLine', { value: true, writable: true })

      const onSyncMock = vi.fn().mockResolvedValue(undefined)
      const { result } = renderHook(() => useOffline({ onSync: onSyncMock }))

      act(() => {
        result.current.queueAction('CREATE_USER', { name: 'Bob' })
      })

      expect(result.current.queuedActions).toHaveLength(1)

      act(() => {
        result.current.syncQueue()
      })

      await waitFor(() => {
        expect(result.current.queuedActions).toHaveLength(0)
      })
    })

    it('should keep failed actions in queue on sync failure', async () => {
      Object.defineProperty(navigator, 'onLine', { value: true, writable: true })

      const onSyncMock = vi.fn().mockRejectedValue(new Error('Sync failed'))
      const { result } = renderHook(() => useOffline({ onSync: onSyncMock }))

      act(() => {
        result.current.queueAction('CREATE_USER', { name: 'Charlie' })
      })

      expect(result.current.queuedActions).toHaveLength(1)

      act(() => {
        result.current.syncQueue()
      })

      await waitFor(() => {
        expect(onSyncMock).toHaveBeenCalled()
      })

      // Action should remain in queue after sync failure
      expect(result.current.queuedActions).toHaveLength(1)
    })

    it('should handle mixed success/failure during sync', async () => {
      Object.defineProperty(navigator, 'onLine', { value: true, writable: true })

      const onSyncMock = vi
        .fn()
        .mockResolvedValueOnce(undefined) // First action succeeds
        .mockRejectedValueOnce(new Error('Failed')) // Second action fails
        .mockResolvedValueOnce(undefined) // Third action succeeds

      const { result } = renderHook(() => useOffline({ onSync: onSyncMock }))

      act(() => {
        result.current.queueAction('ACTION_1', { data: 1 })
        result.current.queueAction('ACTION_2', { data: 2 })
        result.current.queueAction('ACTION_3', { data: 3 })
      })

      expect(result.current.queuedActions).toHaveLength(3)

      act(() => {
        result.current.syncQueue()
      })

      await waitFor(() => {
        expect(onSyncMock).toHaveBeenCalledTimes(3)
      })

      // Only the failed action should remain in queue
      expect(result.current.queuedActions).toHaveLength(1)
      expect(result.current.queuedActions[0].type).toBe('ACTION_2')
    })
  })

  describe('Queue Clear', () => {
    it('should clear all queued actions', () => {
      Object.defineProperty(navigator, 'onLine', { value: false, writable: true })

      const { result } = renderHook(() => useOffline())

      act(() => {
        result.current.queueAction('ACTION_1', { data: 1 })
        result.current.queueAction('ACTION_2', { data: 2 })
      })

      expect(result.current.queuedActions).toHaveLength(2)

      act(() => {
        result.current.clearQueue()
      })

      expect(result.current.queuedActions).toHaveLength(0)
    })

    it('should clear localStorage when clearing queue', () => {
      Object.defineProperty(navigator, 'onLine', { value: false, writable: true })

      const { result } = renderHook(() => useOffline())

      act(() => {
        result.current.queueAction('ACTION_1', { data: 1 })
      })

      expect(localStorage.getItem('offline-queue')).toBeDefined()

      act(() => {
        result.current.clearQueue()
      })

      expect(localStorage.getItem('offline-queue')).toBeNull()
    })
  })

  describe('Edge Cases', () => {
    it('should handle empty onSync callback gracefully', async () => {
      Object.defineProperty(navigator, 'onLine', { value: true, writable: true })

      const { result } = renderHook(() => useOffline())

      act(() => {
        result.current.queueAction('ACTION_1', { data: 1 })
      })

      act(() => {
        result.current.syncQueue()
      })

      await waitFor(() => {
        // Queue should remain unchanged without onSync callback
        expect(result.current.queuedActions).toHaveLength(0)
      })
    })

    it('should handle corrupted localStorage data gracefully', () => {
      localStorage.setItem('offline-queue', 'invalid json')

      const { result } = renderHook(() => useOffline())

      expect(result.current.queuedActions).toEqual([])
    })

    it('should handle localStorage quota exceeded', () => {
      const setItemSpy = vi
        .spyOn(Storage.prototype, 'setItem')
        .mockImplementationOnce(() => {
          throw new Error('QuotaExceededError')
        })

      const { result } = renderHook(() => useOffline())

      act(() => {
        result.current.queueAction('ACTION_1', { data: 1 })
      })

      // Should not throw, action still queued in memory
      expect(result.current.queuedActions).toHaveLength(1)

      setItemSpy.mockRestore()
    })

    it('should generate unique IDs for queued actions', () => {
      const { result } = renderHook(() => useOffline())

      act(() => {
        result.current.queueAction('ACTION_1', { data: 1 })
        result.current.queueAction('ACTION_1', { data: 1 })
      })

      const ids = result.current.queuedActions.map((a) => a.id)
      expect(new Set(ids).size).toBe(2) // All IDs unique
    })
  })
})
