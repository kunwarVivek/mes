# Cache Strategy Utilities

Production-ready cache management utilities for Service Workers with security validations and error handling.

## Features

- **Cache-First Strategy**: Optimal for static assets (JS, CSS, images)
- **Network-First Strategy**: Best for API calls with offline fallback
- **Pre-caching**: Bulk asset caching during service worker installation
- **Cache Invalidation**: Clean up old caches on version changes
- **Security Validations**: Prevents caching of sensitive data and malicious URLs
- **Error Handling**: Graceful handling of quota exceeded and network failures
- **TypeScript Support**: Full type definitions and inference

## Installation

The utilities are located in `src/utils/cache.ts` and are ready to use in your service worker.

## API Reference

### `getCacheFirst(request: Request, cacheName: string): Promise<Response>`

Cache-first strategy: Try cache, fallback to network. Best for static assets.

**Parameters:**
- `request` - Request object to fetch
- `cacheName` - Name of the cache to use

**Returns:** Response from cache or network

**Throws:**
- `CacheError` - If cache name is invalid
- `Error` - If network request fails and no cached response exists

**Example:**
```typescript
const request = new Request('/static/app.js');
const response = await getCacheFirst(request, CACHE_NAMES.STATIC);
```

### `getNetworkFirst(request: Request, cacheName: string): Promise<Response>`

Network-first strategy: Try network, fallback to cache. Best for API calls.

**Parameters:**
- `request` - Request object to fetch
- `cacheName` - Name of the cache to use

**Returns:** Response from network or cache fallback

**Throws:**
- `CacheError` - If cache name is invalid
- `Error` - If both network and cache fail

**Example:**
```typescript
const request = new Request('/api/data');
const response = await getNetworkFirst(request, CACHE_NAMES.API);
```

### `cacheAssets(urls: string[], cacheName: string): Promise<void>`

Pre-cache static assets during service worker installation. Continues caching even if individual URLs fail.

**Parameters:**
- `urls` - Array of URLs to cache
- `cacheName` - Name of the cache to use

**Returns:** Promise that resolves when all caching attempts complete

**Throws:**
- `CacheError` - If cache name or any URL is invalid

**Example:**
```typescript
await cacheAssets([
  '/static/app.js',
  '/static/styles.css',
  '/static/logo.png'
], CACHE_NAMES.STATIC);
```

### `invalidateCache(cacheName: string): Promise<boolean>`

Invalidate cache by deleting it. Used when app version changes.

**Parameters:**
- `cacheName` - Name of the cache to delete

**Returns:** `true` if cache was deleted, `false` if it didn't exist

**Example:**
```typescript
// Delete old cache version
await invalidateCache('static-v1');

// Delete all caches matching pattern
const cacheNames = await caches.keys();
for (const name of cacheNames) {
  if (name.startsWith('static-')) {
    await invalidateCache(name);
  }
}
```

## Constants

### `CACHE_NAMES`

Predefined cache names for consistent usage:

```typescript
const CACHE_NAMES = {
  STATIC: 'static-v1',  // JS, CSS, HTML
  API: 'api-v1',        // API responses
  IMAGES: 'images-v1',  // Image assets
  FONTS: 'fonts-v1',    // Font files
} as const;
```

## Security Features

### URL Validation
- Blocks `javascript:` and `data:` URL schemes
- Validates URL format before caching
- Prevents injection attacks through cache names

### Sensitive Header Detection
Automatically prevents caching of responses with:
- `Authorization` header
- `Set-Cookie` header
- `Cookie` header

### Quota Management
- Gracefully handles `QuotaExceededError`
- Logs warnings without breaking the application
- Continues caching other assets when one fails

## Service Worker Integration

See `src/utils/service-worker-example.ts` for a complete implementation example.

### Basic Setup

```typescript
import {
  getCacheFirst,
  getNetworkFirst,
  cacheAssets,
  invalidateCache,
  CACHE_NAMES,
} from './cache';

// Install: Pre-cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    cacheAssets([
      '/',
      '/index.html',
      '/assets/app.js',
    ], CACHE_NAMES.STATIC)
  );
});

// Activate: Clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(
        names
          .filter(name => !Object.values(CACHE_NAMES).includes(name))
          .map(name => invalidateCache(name))
      )
    )
  );
});

// Fetch: Route to appropriate strategy
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  if (url.pathname.startsWith('/api/')) {
    event.respondWith(getNetworkFirst(request, CACHE_NAMES.API));
  } else {
    event.respondWith(getCacheFirst(request, CACHE_NAMES.STATIC));
  }
});
```

## Error Handling

All functions handle errors gracefully:

```typescript
try {
  const response = await getCacheFirst(request, 'my-cache');
  // Use response
} catch (error) {
  if (error instanceof CacheError) {
    console.error('Cache validation failed:', error.message);
  } else {
    console.error('Network request failed:', error);
  }
}
```

## Testing

Run tests with:
```bash
npm test -- src/utils/__tests__/cache.test.ts
```

Test coverage includes:
- Cache-first strategy (hit/miss scenarios)
- Network-first strategy (online/offline scenarios)
- Pre-caching with partial failures
- Security validations
- Error handling (quota exceeded, network failures)

## Performance Considerations

- **Response Cloning**: Responses are cloned before caching to allow reading
- **Parallel Caching**: `cacheAssets` uses `Promise.allSettled` for parallel operations
- **Graceful Degradation**: Individual failures don't block other operations
- **Minimal Overhead**: Validation checks are fast and occur before network requests

## Migration from Workbox

If migrating from Workbox, here's the equivalent mapping:

| Workbox Strategy | Cache Utils Function |
|------------------|---------------------|
| `CacheFirst()` | `getCacheFirst()` |
| `NetworkFirst()` | `getNetworkFirst()` |
| `precacheAndRoute()` | `cacheAssets()` in install event |
| Cache cleanup | `invalidateCache()` in activate event |

## Version Management

Update cache versions when deploying:

```typescript
// Before deployment: static-v1
const CACHE_NAMES = {
  STATIC: 'static-v1',
  API: 'api-v1',
};

// After deployment: static-v2
const CACHE_NAMES = {
  STATIC: 'static-v2',  // Incremented
  API: 'api-v1',        // Unchanged
};

// Old cache (static-v1) will be cleaned up automatically
```

## Troubleshooting

### Cache not updating
- Ensure cache version is incremented
- Check that old caches are being deleted in activate event
- Verify service worker is properly activated

### Quota exceeded errors
- Reduce number of cached assets
- Implement cache size limits
- Clear old caches more aggressively

### Network errors not falling back to cache
- Ensure assets are pre-cached in install event
- Check that correct cache strategy is used
- Verify cache name matches between caching and retrieval

## License

MIT
