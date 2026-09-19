const CACHE = "ramsey-shell-v3";
const SHELL = [
  "/app/",
  "/app/index.html",
  "/app/css/style.css",
  "/app/js/main.js",
  "/app/js/session-controls.js",
  "/app/js/ui.js",
  "/app/js/state.js",
  "/app/js/api.js",
  "/app/js/voice.js",
  "/app/js/firebase-auth.js",
  "/app/js/pixel-avatars.js",
  "/app/manifest.webmanifest",
];
self.addEventListener("install", (event) => event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting())));
self.addEventListener("activate", (event) => event.waitUntil(
  caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)))).then(() => self.clients.claim())
));
self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  if (!new URL(event.request.url).pathname.startsWith('/app/')) return;
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});
