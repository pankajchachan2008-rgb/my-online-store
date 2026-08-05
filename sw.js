const CACHE_NAME = 'cgsmart-cache-v1';
const urlsToCache = [
    '/',
    '/static/images/cgs_copy_ppnqnx.jpg' // Aapki main brand image ya static files
];

// Install Event
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                return cache.addAll(urlsToCache);
            })
    );
});

// Fetch Event
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                if (response) {
                    return response;
                }
                return fetch(event.request);
            })
    );
});