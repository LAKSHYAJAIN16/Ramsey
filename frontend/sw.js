const CACHE = "ramsey-shell-v2";
const SHELL = [
  "/app/",
  "/app/index.html",
  "/app/css/style.css",
  "/app/js/main.js",
  "/app/js/ui.js",
  "/app/js/state.js",
  "/app/js/api.js",
  "/app/js/voice.js",
  "/app/js/firebase-auth.js",
  "/app/js/pixel-avatars.js",
  "/app/manifest.webmanifest",
];
self.addEventListener("install", (event) => event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(SHELL))));
self.addEventListener("activate", (event) => event.waitUntil(
  caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)))).then(() => self.clients.claim())
));
self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  event.respondWith(caches.match(event.request).then((cached) => cached || fetch(event.request)));
});
