/**
 * Example Service Worker Implementation using Cache Strategy Utilities
 *
 * This file demonstrates how to use the cache utilities in a service worker.
 * To use in your actual service worker:
 * 1. Copy the relevant sections to your service worker file
 * 2. Update the CACHE_VERSION when deploying new versions
 * 3. Update STATIC_ASSETS with your actual asset URLs
 */

import {
  getCacheFirst,
  getNetworkFirst,
  cacheAssets,
  invalidateCache,
  CACHE_NAMES,
} from './cache';

// Update this version when deploying new code
const CACHE_VERSION = 'v1';

// Static assets to pre-cache during installation
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/assets/app.js',
  '/assets/styles.css',
  '/assets/logo.png',
];

/**
 * Service Worker Install Event
 * Pre-cache static assets
 */
self.addEventListener('install', (event: ExtendableEvent) => {
  event.waitUntil(
    cacheAssets(STATIC_ASSETS, CACHE_NAMES.STATIC)
      .then(() => {
        console.log('Static assets cached successfully');
        // Skip waiting to activate immediately
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('Failed to cache static assets:', error);
      })
  );
});

/**
 * Service Worker Activate Event
 * Clean up old caches
 */
self.addEventListener('activate', (event: ExtendableEvent) => {
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        // Delete all caches that don't match current version
        const deletePromises = cacheNames
          .filter((name) => !Object.values(CACHE_NAMES).includes(name as any))
          .map((name) => invalidateCache(name));

        return Promise.all(deletePromises);
      })
      .then(() => {
        console.log('Old caches cleaned up');
        // Take control of all clients immediately
        return self.clients.claim();
      })
  );
});

/**
 * Service Worker Fetch Event
 * Route requests to appropriate cache strategy
 */
self.addEventListener('fetch', (event: FetchEvent) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip cross-origin requests
  if (url.origin !== self.location.origin) {
    return;
  }

  // Route based on request type
  if (url.pathname.startsWith('/api/')) {
    // API requests: Network-first with cache fallback
    event.respondWith(getNetworkFirst(request, CACHE_NAMES.API));
  } else if (url.pathname.match(/\.(png|jpg|jpeg|svg|gif|webp)$/)) {
    // Images: Cache-first
    event.respondWith(getCacheFirst(request, CACHE_NAMES.IMAGES));
  } else if (url.pathname.match(/\.(woff|woff2|ttf|eot)$/)) {
    // Fonts: Cache-first
    event.respondWith(getCacheFirst(request, CACHE_NAMES.FONTS));
  } else {
    // Static assets (JS, CSS, HTML): Cache-first
    event.respondWith(getCacheFirst(request, CACHE_NAMES.STATIC));
  }
});

/**
 * Service Worker Message Event
 * Handle messages from the application
 */
self.addEventListener('message', (event: ExtendableMessageEvent) => {
  const { data } = event;

  if (data && data.type === 'SKIP_WAITING') {
    // Force immediate activation of new service worker
    self.skipWaiting();
  }

  if (data && data.type === 'CACHE_URLS') {
    // Cache specific URLs on demand
    event.waitUntil(
      cacheAssets(data.urls, data.cacheName || CACHE_NAMES.STATIC)
    );
  }

  if (data && data.type === 'CLEAR_CACHE') {
    // Clear specific cache
    event.waitUntil(
      invalidateCache(data.cacheName)
    );
  }
});

export {};
