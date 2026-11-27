/* Parlez service worker — cache the static shell for offline resume. */
const CACHE = 'parlez-v1';
const SHELL = [
  '/app', '/login', '/signup',
  '/static/styles.css', '/static/app-theme.css', '/static/learn.css',
  '/static/parlez-polish.css', '/static/app.js', '/static/learn.js',
  '/static/viewport.js', '/static/mascot.svg', '/static/manifest.webmanifest'
];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  // Never cache API responses (auth, progress, payments).
  if (url.pathname.startsWith('/api/')) return;
  event.respondWith(
    fetch(request).then((response) => {
      if (response.ok && response.type === 'basic') {
        const copy = response.clone();
        caches.open(CACHE).then(cache => cache.put(request, copy));
      }
      return response;
    }).catch(() => caches.match(request).then(cached => cached || caches.match('/app')))
  );
});
