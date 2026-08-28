const CACHE = 'nura-shell-v1'
const SHELL = ['/', '/index.html', '/manifest.json', '/offline.html', '/icons/icon-192.png']

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting()),
  )
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))),
    ).then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (event) => {
  const { request } = event
  if (request.method !== 'GET') return

  const url = new URL(request.url)
  if (url.pathname.startsWith('/api') || url.pathname === '/health') {
    event.respondWith(
      fetch(request).catch(
        () =>
          new Response(
            JSON.stringify({
              success: false,
              error:
                'Nura is offline. Previously saved content remains available, but visual analysis requires a connection.',
            }),
            { status: 503, headers: { 'Content-Type': 'application/json' } },
          ),
      ),
    )
    return
  }

  event.respondWith(
    fetch(request)
      .then((response) => {
        const copy = response.clone()
        caches.open(CACHE).then((cache) => cache.put(request, copy))
        return response
      })
      .catch(async () => {
        const cached = await caches.match(request)
        if (cached) return cached
        if (request.mode === 'navigate') {
          const offline = await caches.match('/offline.html')
          if (offline) return offline
        }
        return new Response('Nura is offline.', { status: 503, headers: { 'Content-Type': 'text/plain' } })
      }),
  )
})
