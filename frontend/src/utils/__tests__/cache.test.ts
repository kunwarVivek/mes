import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  getCacheFirst,
  getNetworkFirst,
  cacheAssets,
  invalidateCache
} from '../cache';

// Mock Cache API
class MockCache {
  private store = new Map<string, Response>();

  async put(request: Request | string, response: Response): Promise<void> {
    const key = typeof request === 'string' ? request : request.url;
    this.store.set(key, response.clone());
  }

  async match(request: Request | string): Promise<Response | undefined> {
    const key = typeof request === 'string' ? request : request.url;
    const response = this.store.get(key);
    return response ? response.clone() : undefined;
  }

  async delete(request: Request | string): Promise<boolean> {
    const key = typeof request === 'string' ? request : request.url;
    return this.store.delete(key);
  }

  async keys(): Promise<Request[]> {
    return Array.from(this.store.keys()).map(url => new Request(url));
  }
}

class MockCacheStorage {
  private caches = new Map<string, MockCache>();

  async open(cacheName: string): Promise<Cache> {
    if (!this.caches.has(cacheName)) {
      this.caches.set(cacheName, new MockCache());
    }
    return this.caches.get(cacheName) as unknown as Cache;
  }

  async delete(cacheName: string): Promise<boolean> {
    return this.caches.delete(cacheName);
  }

  async has(cacheName: string): Promise<boolean> {
    return this.caches.has(cacheName);
  }

  async keys(): Promise<string[]> {
    return Array.from(this.caches.keys());
  }
}

describe('Cache Strategy Utilities', () => {
  let mockCacheStorage: MockCacheStorage;

  beforeEach(() => {
    mockCacheStorage = new MockCacheStorage();
    global.caches = mockCacheStorage as unknown as CacheStorage;
    global.fetch = vi.fn();
  });

  describe('getCacheFirst', () => {
    it('should return cached response if available', async () => {
      const request = new Request('https://example.com/style.css');
      const cachedResponse = new Response('cached content', { status: 200 });

      const cache = await caches.open('static-v1');
      await cache.put(request, cachedResponse);

      const result = await getCacheFirst(request, 'static-v1');
      const text = await result.text();

      expect(result.status).toBe(200);
      expect(text).toBe('cached content');
    });

    it('should fetch from network if cache miss', async () => {
      const request = new Request('https://example.com/new-style.css');
      const networkResponse = new Response('network content', { status: 200 });

      (global.fetch as any).mockResolvedValueOnce(networkResponse.clone());

      const result = await getCacheFirst(request, 'static-v1');
      const text = await result.text();

      expect(global.fetch).toHaveBeenCalledWith(request);
      expect(text).toBe('network content');
    });

    it('should cache network response for future use', async () => {
      const request = new Request('https://example.com/image.png');
      const networkResponse = new Response('image data', { status: 200 });

      (global.fetch as any).mockResolvedValueOnce(networkResponse.clone());

      await getCacheFirst(request, 'static-v1');

      // Second call should return from cache without network call
      (global.fetch as any).mockClear();
      const cachedResult = await getCacheFirst(request, 'static-v1');
      const text = await cachedResult.text();

      expect(global.fetch).not.toHaveBeenCalled();
      expect(text).toBe('image data');
    });

    it('should handle network errors gracefully', async () => {
      const request = new Request('https://example.com/offline.css');

      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      await expect(getCacheFirst(request, 'static-v1')).rejects.toThrow('Network error');
    });
  });

  describe('getNetworkFirst', () => {
    it('should return network response when available', async () => {
      const request = new Request('https://api.example.com/data');
      const networkResponse = new Response(JSON.stringify({ data: 'fresh' }), { status: 200 });

      (global.fetch as any).mockResolvedValueOnce(networkResponse.clone());

      const result = await getNetworkFirst(request, 'api-v1');
      const json = await result.json();

      expect(global.fetch).toHaveBeenCalledWith(request);
      expect(json).toEqual({ data: 'fresh' });
    });

    it('should cache network response for future use', async () => {
      const request = new Request('https://api.example.com/data');
      const networkResponse = new Response(JSON.stringify({ data: 'fresh' }), { status: 200 });

      (global.fetch as any).mockResolvedValueOnce(networkResponse.clone());

      await getNetworkFirst(request, 'api-v1');

      const cache = await caches.open('api-v1');
      const cached = await cache.match(request);

      expect(cached).toBeDefined();
      const json = await cached!.json();
      expect(json).toEqual({ data: 'fresh' });
    });

    it('should fallback to cache when network fails', async () => {
      const request = new Request('https://api.example.com/data');
      const cachedResponse = new Response(JSON.stringify({ data: 'stale' }), { status: 200 });

      const cache = await caches.open('api-v1');
      await cache.put(request, cachedResponse);

      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      const result = await getNetworkFirst(request, 'api-v1');
      const json = await result.json();

      expect(json).toEqual({ data: 'stale' });
    });

    it('should throw error when both network and cache fail', async () => {
      const request = new Request('https://api.example.com/not-cached');

      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      await expect(getNetworkFirst(request, 'api-v1')).rejects.toThrow('Network error');
    });
  });

  describe('cacheAssets', () => {
    it('should cache all provided URLs', async () => {
      const urls = [
        'https://example.com/app.js',
        'https://example.com/styles.css',
        'https://example.com/logo.png'
      ];

      (global.fetch as any).mockImplementation((url: string) =>
        Promise.resolve(new Response(`content of ${url}`, { status: 200 }))
      );

      await cacheAssets(urls, 'static-v1');

      const cache = await caches.open('static-v1');
      for (const url of urls) {
        const cached = await cache.match(url);
        expect(cached).toBeDefined();
        const text = await cached!.text();
        expect(text).toBe(`content of ${url}`);
      }
    });

    it('should handle individual fetch failures gracefully', async () => {
      const urls = [
        'https://example.com/success.js',
        'https://example.com/fail.js',
        'https://example.com/success2.js'
      ];

      (global.fetch as any).mockImplementation((url: string) => {
        if (url.includes('fail')) {
          return Promise.reject(new Error('Fetch failed'));
        }
        return Promise.resolve(new Response(`content of ${url}`, { status: 200 }));
      });

      await cacheAssets(urls, 'static-v1');

      const cache = await caches.open('static-v1');

      // Successful URLs should be cached
      const success1 = await cache.match('https://example.com/success.js');
      expect(success1).toBeDefined();

      const success2 = await cache.match('https://example.com/success2.js');
      expect(success2).toBeDefined();

      // Failed URL should not be cached
      const failed = await cache.match('https://example.com/fail.js');
      expect(failed).toBeUndefined();
    });

    it('should handle cache quota exceeded errors', async () => {
      const urls = ['https://example.com/huge-file.bin'];

      (global.fetch as any).mockResolvedValueOnce(
        new Response('x'.repeat(1000000), { status: 200 })
      );

      // Mock cache.put to throw quota error
      const cache = await caches.open('static-v1');
      const originalPut = cache.put.bind(cache);
      cache.put = vi.fn().mockRejectedValueOnce(
        new DOMException('Quota exceeded', 'QuotaExceededError')
      );

      await cacheAssets(urls, 'static-v1');

      // Should not throw, just log warning
      expect(cache.put).toHaveBeenCalled();
    });
  });

  describe('invalidateCache', () => {
    it('should delete specified cache', async () => {
      const cache = await caches.open('old-cache-v1');
      await cache.put('https://example.com/old.js', new Response('old'));

      const deleted = await invalidateCache('old-cache-v1');

      expect(deleted).toBe(true);
      const exists = await caches.has('old-cache-v1');
      expect(exists).toBe(false);
    });

    it('should return false if cache does not exist', async () => {
      const deleted = await invalidateCache('non-existent-cache');

      expect(deleted).toBe(false);
    });

    it('should handle multiple cache names with pattern matching', async () => {
      await caches.open('static-v1');
      await caches.open('static-v2');
      await caches.open('api-v1');

      const allCaches = await caches.keys();
      expect(allCaches).toContain('static-v1');
      expect(allCaches).toContain('static-v2');
      expect(allCaches).toContain('api-v1');

      await invalidateCache('static-v1');
      await invalidateCache('static-v2');

      const remaining = await caches.keys();
      expect(remaining).not.toContain('static-v1');
      expect(remaining).not.toContain('static-v2');
      expect(remaining).toContain('api-v1');
    });
  });

  describe('Security validations', () => {
    it('should reject invalid cache names', async () => {
      const request = new Request('https://example.com/test.js');

      await expect(getCacheFirst(request, '')).rejects.toThrow('Invalid cache name');
      await expect(getNetworkFirst(request, '')).rejects.toThrow('Invalid cache name');
      await expect(cacheAssets(['https://example.com/test.js'], '')).rejects.toThrow('Invalid cache name');
    });

    it('should reject cache names with special characters', async () => {
      const request = new Request('https://example.com/test.js');
      const invalidNames = [
        '../sensitive-data',
        'cache/../../etc',
        'cache name with spaces',
        'cache@special!chars'
      ];

      for (const name of invalidNames) {
        await expect(getCacheFirst(request, name)).rejects.toThrow('Invalid cache name');
        await expect(getNetworkFirst(request, name)).rejects.toThrow('Invalid cache name');
      }
    });

    it('should validate URLs before caching', async () => {
      const invalidUrls = [
        'javascript:alert(1)',
        'data:text/html,<script>alert(1)</script>',
        'blob:https://example.com/12345',
        ''
      ];

      await expect(cacheAssets(invalidUrls, 'static-v1')).rejects.toThrow('Invalid URL');
    });

    it('should only allow http/https protocols', async () => {
      const invalidProtocols = [
        'ftp://example.com/file.txt',
        'file:///etc/passwd',
        'ws://example.com/socket'
      ];

      for (const url of invalidProtocols) {
        await expect(cacheAssets([url], 'static-v1')).rejects.toThrow('Invalid URL');
      }
    });

    it('should not cache responses with Authorization header (getNetworkFirst)', async () => {
      const request = new Request('https://api.example.com/auth');
      const sensitiveResponse = new Response('token123', {
        status: 200,
        headers: { 'Authorization': 'Bearer secret' }
      });

      (global.fetch as any).mockResolvedValueOnce(sensitiveResponse.clone());

      await getNetworkFirst(request, 'api-v1');

      const cache = await caches.open('api-v1');
      const cached = await cache.match(request);

      // Should not cache responses with Authorization header
      expect(cached).toBeUndefined();
    });

    it('should not cache responses with Authorization header (getCacheFirst)', async () => {
      const request = new Request('https://api.example.com/auth');
      const sensitiveResponse = new Response('token123', {
        status: 200,
        headers: { 'Authorization': 'Bearer secret' }
      });

      (global.fetch as any).mockResolvedValueOnce(sensitiveResponse.clone());

      await getCacheFirst(request, 'api-v1');

      const cache = await caches.open('api-v1');
      const cached = await cache.match(request);

      // Should not cache responses with Authorization header
      expect(cached).toBeUndefined();
    });

    it('should not cache responses with Cookie/Set-Cookie headers', async () => {
      const request1 = new Request('https://example.com/with-cookie');
      const request2 = new Request('https://example.com/set-cookie');

      const cookieResponse = new Response('has cookies', {
        status: 200,
        headers: { 'Cookie': 'session=abc123' }
      });

      const setCookieResponse = new Response('sets cookies', {
        status: 200,
        headers: { 'Set-Cookie': 'session=abc123; HttpOnly' }
      });

      (global.fetch as any).mockResolvedValueOnce(cookieResponse.clone());
      (global.fetch as any).mockResolvedValueOnce(setCookieResponse.clone());

      await getCacheFirst(request1, 'test-v1');
      await getNetworkFirst(request2, 'test-v1');

      const cache = await caches.open('test-v1');
      const cached1 = await cache.match(request1);
      const cached2 = await cache.match(request2);

      // Should not cache responses with Cookie or Set-Cookie headers
      expect(cached1).toBeUndefined();
      expect(cached2).toBeUndefined();
    });
  });
});
