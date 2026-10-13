/**
 * Sightra Service Worker — app shell + static assets only (never API/user data).
 */
const CACHE_NAME = 'sightra-v2';
const OFFLINE_URL = '/offline/';

const APP_SHELL = [
  OFFLINE_URL,
  '/static/css/sightra.css',
  '/static/js/sightra.js',
  '/manifest.webmanifest',
  '/static/manifest.webmanifest',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
];

const OFFLINE_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Offline — Sightra</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 0; min-height: 100dvh; display: flex; align-items: center; justify-content: center;
      background: #0a1628; color: #f1f5f9; text-align: center; padding: 2rem; }
    h1 { font-size: 1.5rem; }
    p { color: #94a3b8; max-width: 24rem; margin: 1rem auto; }
    a, button { display: inline-block; margin: 0.5rem; padding: 0.875rem 1.5rem; font-weight: 700;
      border-radius: 0.75rem; text-decoration: none; border: none; cursor: pointer; font-size: 1rem; }
    .primary { background: #00e5ff; color: #002024; }
    .secondary { background: transparent; color: #00e5ff; border: 2px solid #00e5ff; }
  </style>
</head>
<body>
  <div>
    <h1>You're currently offline</h1>
    <p>Sightra is still available for features that don't require an internet connection. Reconnect to use camera vision, navigation, and live assistance.</p>
    <button type="button" class="primary" onclick="location.reload()">Try again</button>
    <a href="/dashboard/" class="secondary">Go to Home</a>
  </div>
</body>
</html>`;

function offlineResponse() {
  return new Response(OFFLINE_HTML, {
    headers: { 'Content-Type': 'text/html; charset=utf-8' },
  });
}

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function (cache) {
        return cache.addAll(APP_SHELL).catch(function () { /* partial precache ok */ });
      })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys()
      .then(function (keys) {
        return Promise.all(
          keys.filter(function (k) { return k !== CACHE_NAME; }).map(function (k) { return caches.delete(k); })
        );
      })
      .then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (event) {
  var url = new URL(event.request.url);

  if (url.origin !== self.location.origin) {
    return;
  }

  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/admin/')) {
    return;
  }

  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then(function (response) {
          if (response.ok) {
            var clone = response.clone();
            caches.open(CACHE_NAME).then(function (cache) {
              cache.put(event.request, clone);
            });
          }
          return response;
        })
        .catch(function () {
          return caches.match(event.request)
            .then(function (cached) { return cached || caches.match(OFFLINE_URL); })
            .then(function (cached) { return cached || offlineResponse(); });
        })
    );
    return;
  }

  if (url.pathname === '/sw.js') {
    event.respondWith(fetch(event.request));
    return;
  }

  if (url.pathname.startsWith('/static/') || url.pathname === '/manifest.webmanifest') {
    event.respondWith(
      caches.match(event.request).then(function (cached) {
        if (cached) return cached;
        return fetch(event.request).then(function (response) {
          if (response.ok) {
            var clone = response.clone();
            caches.open(CACHE_NAME).then(function (cache) {
              cache.put(event.request, clone);
            });
          }
          return response;
        });
      })
    );
    return;
  }

  if (event.request.method === 'GET') {
    event.respondWith(
      fetch(event.request).catch(function () {
        return caches.match(event.request);
      })
    );
  }
});
