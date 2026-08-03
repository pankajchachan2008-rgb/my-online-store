const CACHE_NAME = 'cgsmart-v1';
const urlsToCache = [
    '/'
];

// Install Service Worker
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                return cache.addAll(urlsToCache);
            })
    );
});

// Fetch logic
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Agar cache mein hai toh wahan se return karein, warna internet se fetch karein
                return response || fetch(event.request);
            })
    );
});