// SENTINEL service worker — installable + instant reopen.
// Strategy (lesson from the game): NETWORK-FIRST for code (html/js/css) so a new deploy is never
// masked by a stale cache; CACHE-FIRST for icons/fonts/tiles. API calls are never cached.
const CACHE = "sentinel-v1";
const SHELL = ["./", "./index.html", "./style.css", "./app.js", "./manifest.json",
               "./icons/icon-192.png", "./icons/icon-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET") return;
  if (url.pathname.includes("/api/") || url.pathname.endsWith("app-config.js")) return;   // live data only
  const isCode = /\.(html|js|css)$/.test(url.pathname) || url.pathname.endsWith("/");
  if (isCode) {
    e.respondWith(fetch(e.request).then(res => {
      const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); return res;
    }).catch(() => caches.match(e.request)));
  } else if (url.origin === location.origin || url.hostname.endsWith("cartocdn.com") || url.hostname.endsWith("cdnjs.cloudflare.com")) {
    e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).then(res => {
      const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); return res;
    })));
  }
});
