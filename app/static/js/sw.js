importScripts('https://storage.googleapis.com/workbox-cdn/releases/6.4.1/workbox-sw.js');

if (workbox) {
    console.log("Workbox is loaded");

    // 1. Pre-cache the App Shell (The basics to make the page load)
    workbox.precaching.precacheAndRoute([
        { url: '/', revision: '3' },
        { url: '/static/css/main.css', revision: '3' },
        { url: '/static/js/map.js', revision: '3' }
    ]);

    workbox.routing.registerRoute(
        ({url}) => url.host === 'unpkg.com',
        new workbox.strategies.CacheFirst({
            cacheName: 'leaflet-cdn-v3',
            plugins: [
                new workbox.cacheableResponse.CacheableResponsePlugin({
                    statuses: [0, 200] // <--- This is the magic line that accepts opaque responses
                })
            ]
        })
    );

    // 2. Strategy A: Supply Items API (/api/items)
    // Network-first: Get fresh pins if possible, fallback to cache if offline.
    workbox.routing.registerRoute(
        new RegExp('/api/items'),
        new workbox.strategies.NetworkFirst({
            cacheName: 'items-cache-v3',
            plugins: [
                new workbox.cacheableResponse.CacheableResponsePlugin({
                    statuses: [0, 200]
                })
            ]
        })
    );

    // 3. Strategy B: Map Tiles (OpenStreetMap)
    // Cache-first: Maps don't change often, so prioritize speed/offline.
    workbox.routing.registerRoute(
        ({url}) => url.host.includes('tile.openstreetmap.org')|| 
                   url.host.includes('stadiamaps.com') || 
                   url.host.includes('cartocdn.com'),
        new workbox.strategies.CacheFirst({
            cacheName: 'map-cache-v3',
            plugins: [
                new workbox.cacheableResponse.CacheableResponsePlugin({
                    statuses: [0, 200]
                }),
                new workbox.expiration.ExpirationPlugin({
                    maxEntries: 50, // Limit cache size so we don't clog the phone
                    maxAgeSeconds: 24 * 60 * 60, // 30 Days
                    purgeOnQuotaError: true,
                }),
            ],
        })
    );

    // 4. Strategy C: Static Images (User uploads)
    workbox.routing.registerRoute(
        ({url}) => url.pathname.startsWith('/static/uploads/'),
            new workbox.strategies.StaleWhileRevalidate({
            cacheName: 'image-cache-v2',
        })
    );
} else {
    console.log("Workbox failed to load");
}