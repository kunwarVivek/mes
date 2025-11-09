# PWA Components - Tech Debt

**Created**: 2025-11-09
**Status**: Non-blocking improvements for future sprints
**Priority**: Low (all components production-ready)

---

## Service Worker (useServiceWorker)

### 1. POST-activation Test Coverage
**Priority**: Low
**Effort**: 1 hour
**File**: `src/hooks/__tests__/useServiceWorker.test.tsx`

**Description**: Add test to verify page reload behavior when new service worker takes control after activation.

**Current Gap**: Tests verify `activateUpdate()` sends `SKIP_WAITING` message but don't verify the subsequent page reload on `controllerchange` event.

**Suggested Test**:
```typescript
it('should reload page when new service worker takes control', async () => {
  // Setup with waiting worker
  const waitingWorker = { postMessage: vi.fn() }
  mockRegistration.waiting = waitingWorker

  const { result } = renderHook(() => useServiceWorker())

  // Call activateUpdate
  act(() => result.current.activateUpdate())

  // Manually trigger controllerchange event
  const controllerChangeEvent = new Event('controllerchange')
  navigator.serviceWorker.dispatchEvent(controllerChangeEvent)

  // Assert window.location.reload was called
  expect(window.location.reload).toHaveBeenCalled()
})
```

---

### 2. Cache Strategy Content-Type Filtering
**Priority**: Low
**Effort**: 2 hours
**File**: `public/service-worker.js`

**Description**: Optimize cache storage by filtering content types. Currently caches all successful responses, which may include large assets unnecessarily.

**Current Behavior**: Network-first strategy caches all 200 OK responses regardless of size or content type.

**Suggested Enhancement**:
```javascript
// In fetch event handler
const contentType = response.headers.get('content-type')
const shouldCache = [
  'text/html',
  'text/css',
  'application/javascript',
  'image/', // prefix match
  'font/'
].some(type => contentType?.includes(type))

if (response.ok && shouldCache) {
  cache.put(request, response.clone())
}
```

**Benefit**: Reduces storage quota usage, prevents caching large downloads/videos.

---

## Camera Hook (useCamera)

### 3. User-Friendly Error Messages
**Priority**: Medium
**Effort**: 2 hours
**File**: `src/hooks/useCamera.tsx:88-96`

**Description**: Normalize browser-specific error names to user-friendly messages for better UX.

**Current Behavior**: Exposes raw browser error names (`NotAllowedError`, `NotFoundError`, `NotSupportedError`).

**Suggested Mapping**:
```typescript
const ERROR_MESSAGES = {
  NotAllowedError: 'Camera permission denied. Please allow camera access in browser settings.',
  NotFoundError: 'No camera device found. Please connect a camera.',
  NotSupportedError: 'Camera not supported on this device.',
  OverconstrainedError: 'Camera constraints not supported. Trying default settings...',
} as const

// In catch block:
const userMessage = ERROR_MESSAGES[error.name] || 'Camera error occurred'
```

**Benefit**: Better user experience with actionable error messages.

---

### 4. Edge Case Test Coverage
**Priority**: Low
**Effort**: 1.5 hours
**File**: `src/hooks/__tests__/useCamera.test.tsx`

**Missing Test Scenarios**:
1. **Invalid video element**: Test with null, undefined, or detached video element
2. **Canvas context failure**: Mock `getContext('2d')` returning null
3. **Non-permission errors**: Test `NotFoundError`, `NotSupportedError`, `OverconstrainedError`
4. **Constraint validation**: Test invalid dimensions (negative, Infinity, NaN)

**Suggested Tests**:
```typescript
it('should handle invalid video element gracefully', async () => {
  const invalidElements = [null, undefined, document.createElement('div')]
  for (const element of invalidElements) {
    await expect(capturePhoto(element)).rejects.toThrow('Invalid video element')
  }
})

it('should handle canvas context creation failure', async () => {
  vi.spyOn(document.createElement('canvas'), 'getContext').mockReturnValue(null)
  await expect(capturePhoto(validVideoElement)).rejects.toThrow('Failed to get canvas context')
})
```

---

## Cache Utils (cache.ts)

### 5. Request Method Validation
**Priority**: Low
**Effort**: 1 hour
**File**: `src/utils/cache.ts:162-171`

**Description**: Only cache GET/HEAD requests to prevent stale write operations (POST/PUT/DELETE) in cache.

**Current Behavior**: Caches all successful responses regardless of HTTP method.

**Suggested Enhancement**:
```typescript
// In getNetworkFirst and getCacheFirst
const CACHEABLE_METHODS = ['GET', 'HEAD']

if (networkResponse.ok &&
    !hasSensitiveHeaders(networkResponse) &&
    CACHEABLE_METHODS.includes(request.method.toUpperCase())) {
  await cache.put(request, networkResponse.clone())
}
```

**Benefit**: Prevents caching stale POST/PUT/DELETE responses, aligns with HTTP semantics.

---

## Offline Hook (useOffline)

### 6. Race Condition Test Coverage
**Priority**: Low
**Effort**: 1.5 hours
**File**: `src/hooks/__tests__/useOffline.test.tsx`

**Description**: Test rapid online/offline transitions during active sync operation.

**Missing Scenario**: User goes offline mid-sync, ensuring graceful handling without data loss.

**Suggested Test**:
```typescript
it('should handle online/offline transition during active sync', async () => {
  const slowSync = vi.fn(() => new Promise(resolve => setTimeout(resolve, 100)))
  const { result } = renderHook(() => useOffline({ onSync: slowSync }))

  // Queue action while offline
  act(() => {
    offlineListeners.forEach(l => l())
    result.current.queueAction('ACTION_1', { data: 'test' })
  })

  // Go online and start sync
  act(() => onlineListeners.forEach(l => l()))

  // Wait 50ms (mid-sync) then go offline again
  await act(async () => {
    await new Promise(resolve => setTimeout(resolve, 50))
    offlineListeners.forEach(l => l())
  })

  // Verify: isOffline=true, action still queued for retry
  expect(result.current.isOffline).toBe(true)
  expect(result.current.queuedActions).toHaveLength(1)
})
```

**Benefit**: Ensures robustness in poor network conditions with frequent connectivity changes.

---

## Summary

**Total Items**: 6
**Estimated Effort**: 9 hours
**Priority Breakdown**:
- Low: 4 items (7.5 hours)
- Medium: 1 item (2 hours)
- High: 0 items

**Status**: All items are non-blocking. PWA components are production-ready without these improvements.

**Recommendation**: Address in dedicated tech debt sprint, prioritize Medium item (#3 - error messages) for better UX.
