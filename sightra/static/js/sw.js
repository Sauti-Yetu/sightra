const CACHE = "sightra-shell-v1";
const PRECACHE = [
  "/",
  "/dashboard",
  "/offline/",
  "/static/css/sightra.css",
  "/static/js/sightra.js",
  "/manifest.webmanifest",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(PRECACHE)));
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

  if (url.pathname.startsWith("/static/") || url.pathname === "/manifest.webmanifest") {
    event.respondWith(caches.match(request).then((hit) => hit || fetch(request)));
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
