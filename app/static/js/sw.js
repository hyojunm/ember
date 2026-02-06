importScripts('https://storage.googleapis.com/workbox-cdn/releases/6.4.1/workbox-sw.js');

if (workbox) {
  console.log("Workbox is loaded!");

  // Pre-cache the basic UI
  workbox.precaching.precacheAndRoute([
    { url: '/', revision: '1' },
    { url: '/static/styles.css', revision: '1' }
  ]);

  // Strategy: Network First (for emergency item listings)
  workbox.routing.registerRoute(
    ({request}) => request.destination === 'document' || request.url.includes('/api/items'),
    new workbox.strategies.NetworkFirst()
  );

  // Strategy: Cache First (for icons and fonts)
  workbox.routing.registerRoute(
    ({request}) => request.destination === 'image' || request.destination === 'font',
    new workbox.strategies.CacheFirst()
  );
}

// Cache map tiles as the user browses
workbox.routing.registerRoute(
  new RegExp('https://.*.tile.openstreetmap.org/.*'),
  new workbox.strategies.CacheFirst({
    cacheName: 'map-tiles',
    plugins: [
      new workbox.expiration.ExpirationPlugin({
        maxEntries: 50, // Keep 50 tiles
        maxAgeSeconds: 7 * 24 * 60 * 60, // 1 week
      }),
    ],
  })
);