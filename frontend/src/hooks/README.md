# PWA Hooks Documentation

Custom React hooks for Progressive Web App functionality.

## useServiceWorker

A React hook for managing service worker registration and updates in PWA applications.

### Features

- Only registers in production mode (skips dev/test)
- Enforces HTTPS security (except localhost)
- Detects and manages service worker updates
- Graceful error handling
- TypeScript support

### Usage

```tsx
import { useServiceWorker } from '@/hooks/useServiceWorker'

function App() {
  const { isRegistered, isUpdateAvailable, error, activateUpdate } = useServiceWorker()

  if (error) {
    console.error('Service worker error:', error)
  }

  return (
    <div>
      {isUpdateAvailable && (
        <div className="update-banner">
          <p>New version available!</p>
          <button onClick={activateUpdate}>Update Now</button>
        </div>
      )}
      {/* Rest of your app */}
    </div>
  )
}
```

### API

#### Return Value

```typescript
interface ServiceWorkerHook {
  isRegistered: boolean        // Whether service worker is registered
  isUpdateAvailable: boolean   // Whether update is waiting
  error: string | null         // Registration error if any
  activateUpdate: () => void   // Activate waiting service worker
}
```

---

## useOffline

A React hook for offline detection and sync queue management for PWA applications.

### Features

- Detects online/offline status via `navigator.onLine`
- Queues actions when offline with localStorage persistence
- Auto-syncs queued actions when connection restored
- Handles sync failures gracefully (failed actions remain in queue)
- Persistent queue across browser sessions
- Custom storage key support
- Error handling for localStorage quota exceeded

### Usage

```tsx
import { useOffline } from '@/hooks/useOffline'

function App() {
  const {
    isOffline,
    queueAction,
    syncQueue,
    queuedActions,
    clearQueue
  } = useOffline({
    onSync: async (action) => {
      // Sync action to server
      const response = await fetch('/api/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(action)
      })
      if (!response.ok) {
        throw new Error('Sync failed')
      }
    },
    storageKey: 'my-offline-queue' // Optional
  })

  const handleCreateUser = async (userData) => {
    if (isOffline) {
      // Queue for later sync
      queueAction('CREATE_USER', userData)
      toast.success('Queued for sync when online')
    } else {
      // Sync immediately
      await createUser(userData)
    }
  }

  return (
    <div>
      {isOffline && (
        <div className="offline-banner">
          You are offline. Actions will be queued.
          {queuedActions.length > 0 && (
            <span> ({queuedActions.length} pending)</span>
          )}
        </div>
      )}
      <button onClick={handleCreateUser}>Create User</button>
      <button onClick={syncQueue}>Manual Sync</button>
      <button onClick={clearQueue}>Clear Queue</button>
    </div>
  )
}
```

### API

#### Parameters

```typescript
interface UseOfflineOptions {
  onSync?: (action: Action) => Promise<void>  // Callback to sync each action
  storageKey?: string                          // localStorage key (default: 'offline-queue')
}
```

#### Return Value

```typescript
interface UseOfflineReturn {
  isOffline: boolean                          // Current offline status
  queueAction: (type: string, payload: unknown) => void  // Queue an action
  syncQueue: () => Promise<void>              // Manually trigger sync
  queuedActions: Action[]                     // List of pending actions
  clearQueue: () => void                      // Clear all queued actions
}

interface Action {
  id: string           // Unique action ID
  type: string         // Action type (e.g., 'CREATE_USER')
  payload: unknown     // Action data
  timestamp: number    // When action was queued (ms since epoch)
}
```

#### Behavior

**Offline Detection**: Uses `navigator.onLine` and listens to `online`/`offline` events

**Auto-Sync**: When connection is restored (online event), automatically calls `syncQueue()`

**Sync Strategy**:
1. Process each action sequentially
2. Call `onSync(action)` for each action
3. If `onSync` succeeds, remove action from queue
4. If `onSync` fails (throws error), keep action in queue for retry
5. Update localStorage with remaining failed actions

**Persistence**: Queue is automatically saved to localStorage whenever it changes

---

## useCamera

A React hook for accessing device camera with media stream management.

### Features

- Request camera permissions
- Start/stop camera stream
- Preview video stream in real-time
- Capture photo from stream
- Auto-cleanup on unmount
- Error handling for camera access

### Usage

```tsx
import { useCamera } from '@/hooks/useCamera'

function CameraComponent() {
  const {
    stream,
    error,
    isActive,
    videoRef,
    startCamera,
    stopCamera,
    capturePhoto
  } = useCamera()

  const handleCapture = async () => {
    const photo = await capturePhoto()
    if (photo) {
      // Use photo blob
      const formData = new FormData()
      formData.append('photo', photo, 'capture.jpg')
      await uploadPhoto(formData)
    }
  }

  return (
    <div>
      <video ref={videoRef} autoPlay playsInline />
      <button onClick={startCamera} disabled={isActive}>Start Camera</button>
      <button onClick={stopCamera} disabled={!isActive}>Stop Camera</button>
      <button onClick={handleCapture} disabled={!isActive}>Capture Photo</button>
      {error && <div className="error">{error}</div>}
    </div>
  )
}
```

---

## Testing

All hooks have comprehensive test coverage with Vitest and React Testing Library.

```bash
# Run all hook tests
npm test -- src/hooks/__tests__/

# Run specific hook tests
npm test -- src/hooks/__tests__/useServiceWorker.test.tsx
npm test -- src/hooks/__tests__/useOffline.test.tsx
npm test -- src/hooks/__tests__/useCamera.test.tsx
```
