const CACHE = "sightra-shell-v10";
const PRECACHE = [
  "/offline/",
  "/manifest.webmanifest",
  "/static/css/sightra.css",
  "/static/js/sightra.js",
  "/static/icons/app-icon-192.png",
  "/static/icons/app-icon-512.png",
];

/** Never cache-first brand images (avoids stale white JPG / old icons). */
function isBrandAsset(pathname) {
  return (
    pathname.startsWith("/static/img/sightra-logo") ||
    pathname.startsWith("/static/icons/") ||
    pathname.includes("app-icon-") ||
    pathname.endsWith("sightra-logo.jpg")
  );
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then(async (cache) => {
      await Promise.all(
        PRECACHE.map(async (url) => {
          try {
            await cache.add(url);
          } catch {
            /* one missing asset must not block SW install */
          }
        })
      );
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.pathname.startsWith("/api/")) return;

  if (isBrandAsset(url.pathname)) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response && response.ok) {
            const clone = response.clone();
            caches.open(CACHE).then((cache) => cache.put(request, clone));
          }
          return response;
        })
        .catch(() => caches.match(request))
    );
    return;
  }

  if (url.pathname.startsWith("/static/") || url.pathname === "/manifest.webmanifest") {
    event.respondWith(
      fetch(request)
        .then((response) => response)
        .catch(() => caches.match(request))
    );
    return;
  }

  event.respondWith(
    fetch(request)
      .then((response) => response)
      .catch(() =>
        caches.match(request).then((hit) => hit || caches.match("/offline/"))
      )
  );
});
