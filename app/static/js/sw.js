importScripts('https://storage.googleapis.com/workbox-cdn/releases/6.4.1/workbox-sw.js');
workbox.loadModule('workbox-range-requests');

// 1. Force the SW to become active immediately
self.addEventListener('install', (event) => {
    self.skipWaiting(); 
});

// 2. Force the SW to start intercepting requests for all open tabs immediately
self.addEventListener('activate', (event) => {
    event.waitUntil(clients.claim());
    console.log("🚀 Service Worker active and claiming clients!");
});

if (workbox) {
    console.log("Workbox is loaded");

    // 1. Pre-cache the App Shell (static assets only — NOT pages with auth-dependent HTML)
    workbox.precaching.precacheAndRoute([
        { url: '/static/css/main.css', revision: '3' },
        { url: '/static/js/map.js', revision: '3' }
    ]);

    // Homepage contains Jinja-rendered auth state, so always fetch from server first
    workbox.routing.registerRoute(
        ({url}) => url.pathname === '/',
        new workbox.strategies.NetworkFirst({
            cacheName: 'pages-cache-v1',
            plugins: [
                new workbox.cacheableResponse.CacheableResponsePlugin({
                    statuses: [0, 200]
                })
            ]
        })
    );

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

    workbox.routing.registerRoute(
        new RegExp('/api/locations'),
        new workbox.strategies.NetworkFirst({
            cacheName: 'locations-cache-v3',
            plugins: [
                new workbox.cacheableResponse.CacheableResponsePlugin({
                    statuses: [0, 200]
                })
            ]
        })
    );

    // 3. Strategy B: Map Tiles (OpenStreetMap)
    // Cache-first: Maps don't change often, so prioritize speed/offline.
    // workbox.routing.registerRoute(
    //     ({url}) => url.host.includes('tile.openstreetmap.org') || 
    //                url.host.includes('stadiamaps.com') || 
    //                url.host.includes('cartocdn.com'),
    //     new workbox.strategies.CacheFirst({
    //         cacheName: 'map-cache-v3',
    //         plugins: [
    //             new workbox.cacheableResponse.CacheableResponsePlugin({
    //                 statuses: [0, 200]
    //             }),
    //             new workbox.expiration.ExpirationPlugin({
    //                 maxEntries: 50, // Limit cache size so we don't clog the phone
    //                 maxAgeSeconds: 24 * 60 * 60, // 30 Days
    //                 purgeOnQuotaError: true,
    //             }),
    //         ],
    //     })
    // );

    // workbox.routing.registerRoute(
    //   ({url}) => url.pathname.endsWith('.pmtiles'),
    //   new workbox.strategies.CacheFirst({
    //     cacheName: 'map-cache',
    //     plugins: [
    //       // This is the magic: it allows the cache to handle 206 Partial Content
    //       new workbox.rangeRequests.RangeRequestsPlugin(),
    //       new workbox.cacheableResponse.CacheableResponsePlugin({
    //         statuses: [0, 200, 206], // Cache successful and partial responses
    //       }),
    //       new workbox.expiration.ExpirationPlugin({
    //         maxEntries: 1, // You only need the one Pittsburgh file
    //         maxAgeSeconds: 30 * 24 * 60 * 60, // 30 Days
    //       }),
    //     ],
    //   })
    // );

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

self.addEventListener('fetch', (event) => {
    if (event.request.url.includes('pittsburgh-pa.pmtiles')) {
        event.respondWith(
            caches.match(event.request.url).then(cachedResponse => {
                if (cachedResponse) {
                    // The workbox plugin handles the 416/206 logic automatically
                    return workbox.rangeRequests.createPartialResponse(event.request, cachedResponse);
                }
                return fetch(event.request);
            })
        );
    }
    // if (event.request.url.includes('pittsburgh-pa.pmtiles')) {
    //     event.respondWith(
    //         (async () => {
    //             // const cache = await caches.open('pittsburgh-map-v2');
    //             const cachedResponse = await cache.match(event.request.url);

    //             if (cachedResponse) {
    //                 // Use the Workbox Range Handler to slice the cached 200 response 
    //                 // into the 206 Partial Content the map is asking for.
    //                 return await workbox.rangeRequests.createPartialResponse(
    //                     event.request, 
    //                     cachedResponse
    //                 );
    //             }

    //             // Fallback to network if not in cache
    //             return fetch(event.request);
    //         })()
    //     );
    // }
});