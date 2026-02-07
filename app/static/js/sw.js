importScripts('https://storage.googleapis.com/workbox-cdn/releases/6.4.1/workbox-sw.js');

if (workbox) {
    console.log("Workbox is loaded");

    // 1. Pre-cache the App Shell (The basics to make the page load)
    workbox.precaching.precacheAndRoute([
        { url: '/', revision: '1' },
        { url: '/static/css/main.css', revision: '1' },
        { url: '/static/js/map.js', revision: '1' },
        { url: 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css', revision: '1' },
        { url: 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js', revision: '1' }
    ]);

    // 2. Strategy A: Supply Items API (/api/items)
    // Network-first: Get fresh pins if possible, fallback to cache if offline.
    workbox.routing.registerRoute(
        ({url}) => url.pathname === '/api/items',
        new workbox.strategies.NetworkFirst({
            cacheName: 'items-cache',
        })
    );

    // 3. Strategy B: Map Tiles (OpenStreetMap)
    // Cache-first: Maps don't change often, so prioritize speed/offline.
    workbox.routing.registerRoute(
        ({url}) => url.host.includes('tile.openstreetmap.org'),
        new workbox.strategies.CacheFirst({
            cacheName: 'map-cache',
            plugins: [
                new workbox.cacheableResponse.CacheableResponsePlugin({
                    statuses: [0, 200]
                }),
                new workbox.expiration.ExpirationPlugin({
                    maxEntries: 100, // Limit cache size so we don't clog the phone
                    maxAgeSeconds: 30 * 24 * 60 * 60, // 30 Days
                }),
            ],
        })
    );

    // 4. Strategy C: Static Images (User uploads)
    workbox.routing.registerRoute(
        ({url}) => url.pathname.startsWith('/static/uploads/'),
            new workbox.strategies.StaleWhileRevalidate({
            cacheName: 'image-cache',
        })
    );
} else {
    console.log("Workbox failed to load");
}