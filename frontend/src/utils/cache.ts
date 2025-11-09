/**
 * Cache Strategy Utilities for Service Worker
 * Provides cache-first and network-first strategies with security validations
 */

/**
 * Cache error types for better error handling
 */
export class CacheError extends Error {
  constructor(message: string, public readonly cause?: unknown) {
    super(message);
    this.name = 'CacheError';
  }
}

/**
 * Sensitive headers that should not be cached
 */
const SENSITIVE_HEADERS = ['Authorization', 'Set-Cookie', 'Cookie'] as const;

/**
 * Malicious URL schemes to block
 * Includes blob: for defense-in-depth against malicious blob URLs
 */
const BLOCKED_URL_SCHEMES = ['javascript:', 'data:', 'blob:'] as const;

/**
 * Options for cache strategies
 */
export interface CacheOptions {
  /**
   * Whether to cache the response even on non-200 status codes
   * @default false
   */
  cacheNonOkResponses?: boolean;

  /**
   * Maximum number of retry attempts for network requests
   * @default 0
   */
  maxRetries?: number;
}

/**
 * Validates cache name to prevent injection attacks
 * Only allows alphanumeric characters, hyphens, and underscores
 * @throws {CacheError} If cache name is invalid
 */
function validateCacheName(cacheName: string): void {
  if (!cacheName || typeof cacheName !== 'string' || cacheName.trim().length === 0) {
    throw new CacheError('Invalid cache name');
  }

  // Whitelist safe characters to prevent cache pollution attacks
  if (!/^[a-zA-Z0-9_-]+$/.test(cacheName.trim())) {
    throw new CacheError('Invalid cache name: only alphanumeric, hyphen, and underscore allowed');
  }
}

/**
 * Validates URL to prevent malicious schemes
 * @throws {CacheError} If URL is invalid or uses blocked scheme
 */
function validateUrl(url: string): void {
  if (!url || typeof url !== 'string') {
    throw new CacheError('Invalid URL');
  }

  const lowerUrl = url.toLowerCase();
  for (const scheme of BLOCKED_URL_SCHEMES) {
    if (lowerUrl.startsWith(scheme)) {
      throw new CacheError('Invalid URL');
    }
  }

  try {
    const parsedUrl = new URL(url);
    // Only allow http: and https: protocols
    if (!['http:', 'https:'].includes(parsedUrl.protocol)) {
      throw new CacheError('Invalid URL: only http/https protocols allowed');
    }
  } catch (error) {
    throw new CacheError('Invalid URL', error);
  }
}

/**
 * Checks if response contains sensitive headers that should not be cached
 * @param response - Response object to check
 * @returns True if response has sensitive headers
 */
function hasSensitiveHeaders(response: Response): boolean {
  return SENSITIVE_HEADERS.some(header => response.headers.has(header));
}

/**
 * Cache-first strategy: Try cache, fallback to network
 * Best for static assets (JS, CSS, images)
 *
 * @param request - Request object to fetch
 * @param cacheName - Name of the cache to use
 * @returns Response from cache or network
 * @throws {CacheError} If cache name is invalid
 * @throws {Error} If network request fails and no cached response exists
 *
 * @example
 * ```ts
 * const request = new Request('/static/app.js');
 * const response = await getCacheFirst(request, 'static-v1');
 * ```
 */
export async function getCacheFirst(
  request: Request,
  cacheName: string
): Promise<Response> {
  validateCacheName(cacheName);

  const cache = await caches.open(cacheName);
  const cachedResponse = await cache.match(request);

  if (cachedResponse) {
    return cachedResponse;
  }

  // Cache miss - fetch from network
  const networkResponse = await fetch(request);

  // Cache the response for future use (clone because response can only be read once)
  // Skip caching if response contains sensitive headers (Authorization, Cookie, etc.)
  if (networkResponse.ok && !hasSensitiveHeaders(networkResponse)) {
    try {
      await cache.put(request, networkResponse.clone());
    } catch (error) {
      // Ignore cache storage errors (quota exceeded, etc.)
      // Response is still returned to the caller
      if (error instanceof DOMException && error.name === 'QuotaExceededError') {
        console.warn(`Cache quota exceeded for ${request.url}`);
      }
    }
  }

  return networkResponse;
}

/**
 * Network-first strategy: Try network, fallback to cache
 * Best for API calls where fresh data is preferred but offline support is needed
 *
 * @param request - Request object to fetch
 * @param cacheName - Name of the cache to use
 * @returns Response from network or cache fallback
 * @throws {CacheError} If cache name is invalid
 * @throws {Error} If both network and cache fail
 *
 * @example
 * ```ts
 * const request = new Request('/api/data');
 * const response = await getNetworkFirst(request, 'api-v1');
 * ```
 */
export async function getNetworkFirst(
  request: Request,
  cacheName: string
): Promise<Response> {
  validateCacheName(cacheName);

  const cache = await caches.open(cacheName);

  try {
    // Try network first
    const networkResponse = await fetch(request);

    // Cache the response for future offline use (if no sensitive headers)
    if (networkResponse.ok && !hasSensitiveHeaders(networkResponse)) {
      try {
        await cache.put(request, networkResponse.clone());
      } catch (error) {
        // Ignore cache storage errors but log them
        if (error instanceof DOMException && error.name === 'QuotaExceededError') {
          console.warn(`Cache quota exceeded for ${request.url}`);
        }
      }
    }

    return networkResponse;
  } catch (error) {
    // Network failed - try cache
    const cachedResponse = await cache.match(request);

    if (cachedResponse) {
      return cachedResponse;
    }

    // Both network and cache failed
    throw error;
  }
}

/**
 * Pre-cache static assets during service worker installation
 * Continues caching even if individual URLs fail
 *
 * @param urls - Array of URLs to cache
 * @param cacheName - Name of the cache to use
 * @returns Promise that resolves when all caching attempts complete
 * @throws {CacheError} If cache name or any URL is invalid
 *
 * @example
 * ```ts
 * await cacheAssets([
 *   '/static/app.js',
 *   '/static/styles.css',
 *   '/static/logo.png'
 * ], 'static-v1');
 * ```
 */
export async function cacheAssets(
  urls: string[],
  cacheName: string
): Promise<void> {
  validateCacheName(cacheName);

  // Validate all URLs first (fail fast on invalid URLs)
  for (const url of urls) {
    validateUrl(url);
  }

  const cache = await caches.open(cacheName);

  // Cache each URL, handling failures gracefully
  const results = await Promise.allSettled(
    urls.map(async (url) => {
      try {
        const response = await fetch(url);
        if (response.ok) {
          await cache.put(url, response);
        } else {
          console.warn(`Failed to fetch ${url}: ${response.status} ${response.statusText}`);
        }
      } catch (error) {
        // Log error but don't throw - continue caching other assets
        if (error instanceof DOMException && error.name === 'QuotaExceededError') {
          console.warn(`Cache quota exceeded for ${url}`);
        } else {
          console.warn(`Failed to cache ${url}:`, error);
        }
      }
    })
  );

  // Optional: Log summary of caching results
  const succeeded = results.filter(r => r.status === 'fulfilled').length;
  const failed = results.length - succeeded;
  if (failed > 0) {
    console.info(`Cached ${succeeded}/${urls.length} assets (${failed} failed)`);
  }
}

/**
 * Invalidate cache by deleting it
 * Used when app version changes or cache needs to be cleared
 *
 * @param cacheName - Name of the cache to delete
 * @returns True if cache was deleted, false if it didn't exist
 *
 * @example
 * ```ts
 * // Delete old cache version
 * await invalidateCache('static-v1');
 *
 * // Delete all caches matching pattern
 * const cacheNames = await caches.keys();
 * for (const name of cacheNames) {
 *   if (name.startsWith('static-')) {
 *     await invalidateCache(name);
 *   }
 * }
 * ```
 */
export async function invalidateCache(cacheName: string): Promise<boolean> {
  return await caches.delete(cacheName);
}

/**
 * Cache name constants for consistent usage across the application
 */
export const CACHE_NAMES = {
  STATIC: 'static-v1',
  API: 'api-v1',
  IMAGES: 'images-v1',
  FONTS: 'fonts-v1',
} as const;

/**
 * Type for cache name keys
 */
export type CacheName = typeof CACHE_NAMES[keyof typeof CACHE_NAMES];
