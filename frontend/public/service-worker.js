// Service Worker - Minimal PWA Implementation
// This will be enhanced with Workbox in production build

const CACHE_NAME = 'unison-v1'

// Listen for skip waiting message
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting()
  }
})

// Activate immediately
self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      // Claim all clients immediately
      await self.clients.claim()
    })()
  )
})

// Basic fetch strategy - network first, fall back to cache
self.addEventListener('fetch', (event) => {
  event.respondWith(
    (async () => {
      try {
        const response = await fetch(event.request)

        // Cache successful responses
        if (response.ok) {
          const cache = await caches.open(CACHE_NAME)
          cache.put(event.request, response.clone())
        }

        return response
      } catch (error) {
        // Try to serve from cache if network fails
        const cachedResponse = await caches.match(event.request)
        if (cachedResponse) {
          return cachedResponse
        }

        throw error
      }
    })()
  )
})
