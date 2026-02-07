const PGH_MAP_URL = "/static/maps/pittsburgh-pa.pmtiles";

// Restore saved map position or use defaults
const savedMap = JSON.parse(localStorage.getItem('emberMapView'));
const mapCenter = savedMap ? [savedMap.lat, savedMap.lng] : [40.4406, -79.9959];
const mapZoom = savedMap ? savedMap.zoom : 15;

const map = L.map('map', {
    center: mapCenter,
    zoom: mapZoom,
    minZoom: 12,                 // Maximum zoom out (City view)
    maxZoom: 18,                 // Maximum zoom in (Street view)
    maxBounds: [                 // Optional: Lock the map to a specific area
        [40.340, -80.150],         // Southwest coordinates
        [40.570, -79.750]          // Northeast coordinates
    ],
    maxBoundsViscosity: 1.0,     // Prevents the user from dragging outside the bounds
    zoomControl: false           // Disable default zoom control
});

// Add zoom control to bottom right
L.control.zoom({
    position: 'bottomright'
}).addTo(map);

// Save map position on every move/zoom
map.on('moveend', function() {
    const c = map.getCenter();
    localStorage.setItem('emberMapView', JSON.stringify({ lat: c.lat, lng: c.lng, zoom: map.getZoom() }));
});

const layer = protomapsL.leafletLayer({
    url: PGH_MAP_URL,
    paint_rules: [
        {
            dataLayer: 'water',
            symbolizer: new protomapsL.PolygonSymbolizer({
                fill: '#a2daf2'
            })
        },
        {
            dataLayer: 'park',
            symbolizer: new protomapsL.PolygonSymbolizer({
                fill: '#d8e8c8'
            })
        },
        {
            dataLayer: 'landuse',
            symbolizer: new protomapsL.PolygonSymbolizer({
                fill: '#e0ebd4'
            })
        },
        {
            dataLayer: 'building',
            symbolizer: new protomapsL.PolygonSymbolizer({
                fill: '#d9d9d9',
                stroke: '#c0c0c0',
                width: 0.5
            })
        },
        {
            dataLayer: 'transportation',
            symbolizer: new protomapsL.LineSymbolizer({
                color: '#ffffff',
                width: (z) => (z < 13 ? 1 : z < 15 ? 3 : 6)
            })
        }
    ],
    label_rules: [
        {
            dataLayer: 'place',
            symbolizer: new protomapsL.CenteredTextSymbolizer({
                labelProps: ['name'],
                fill: '#333333',
                font: '600 16px sans-serif'
            })
        },
        {
            dataLayer: 'transportation_name',
            symbolizer: new protomapsL.LineLabelSymbolizer({
                labelProps: ['name'],
                fill: '#444444',
                font: '12px sans-serif'
            })
        },
        {
            dataLayer: 'poi',
            symbolizer: new protomapsL.CenteredTextSymbolizer({
                labelProps: ['name'],
                fill: '#666666',
                font: '11px sans-serif'
            })
        },
        {
            dataLayer: 'housenumber',
            symbolizer: new protomapsL.CenteredTextSymbolizer({
                labelProps: ['housenumber'],
                fill: '#888888',
                font: '9px sans-serif'
            })
        }
    ]
});

layer.addTo(map);

const userIcon = L.divIcon({
    className: 'user-location-marker',
    html: '<div class="user-location-pulse" aria-hidden="true"></div>',
    iconSize: [80, 80],
    iconAnchor: [40, 40]
});

// Campfire SVG icons for location markers
const campfireSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 44 44" width="44" height="44">
  <path d="M22 4c-2 4-8 9-8 16a8 8 0 0 0 16 0c0-7-6-12-8-16z" fill="#F97316" stroke="#C2410C" stroke-width="1.5"/>
  <path d="M22 10c-1.2 2.5-4 5.5-4 9a4 4 0 0 0 8 0c0-3.5-2.8-6.5-4-9z" fill="#FCD34D"/>
  <line x1="10" y1="34" x2="34" y2="40" stroke="#92400E" stroke-width="3" stroke-linecap="round"/>
  <line x1="34" y1="34" x2="10" y2="40" stroke="#92400E" stroke-width="3" stroke-linecap="round"/>
</svg>`;

const campfireEmptySvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 44 44" width="44" height="44">
  <path d="M22 4c-2 4-8 9-8 16a8 8 0 0 0 16 0c0-7-6-12-8-16z" fill="#D1D5DB" stroke="#9CA3AF" stroke-width="1.5"/>
  <path d="M22 10c-1.2 2.5-4 5.5-4 9a4 4 0 0 0 8 0c0-3.5-2.8-6.5-4-9z" fill="#E5E7EB"/>
  <line x1="10" y1="34" x2="34" y2="40" stroke="#9CA3AF" stroke-width="3" stroke-linecap="round"/>
  <line x1="34" y1="34" x2="10" y2="40" stroke="#9CA3AF" stroke-width="3" stroke-linecap="round"/>
</svg>`;

const campfireIcon = L.divIcon({
    className: 'ember-marker',
    html: campfireSvg,
    iconSize: [44, 44],
    iconAnchor: [22, 40],
    popupAnchor: [0, -40],
    tooltipAnchor: [0, -34]
});

const campfireEmptyIcon = L.divIcon({
    className: 'ember-marker',
    html: campfireEmptySvg,
    iconSize: [44, 44],
    iconAnchor: [22, 40],
    popupAnchor: [0, -40],
    tooltipAnchor: [0, -34]
});

let userMarker = null;
let userLat = null;
let userLng = null;
let allItems = [];
let markersByKey = {}; // lookup markers by "lat,lng" key
let _highlightedMarkerKey = null; // track currently highlighted marker

function setUserLocation(lat, lng) {
    userLat = lat;
    userLng = lng;
    const coords = [lat, lng];
    map.setView(coords, Math.max(map.getZoom(), 15));

    if (!userMarker) {
        userMarker = L.marker(coords, { icon: userIcon, zIndexOffset: 1000 }).addTo(map);
    } else {
        userMarker.setLatLng(coords);
    }

    // Refresh nearby items sidebar if not viewing a specific location
    if (typeof _viewingLocation !== 'undefined' && !_viewingLocation && typeof showNearbyItems === 'function') showNearbyItems();
}

function requestUserLocation() {
    if (!navigator.geolocation) {
        console.log('Geolocation not supported.');
        return;
    }

    navigator.geolocation.getCurrentPosition(
        (pos) => {
            setUserLocation(pos.coords.latitude, pos.coords.longitude);
        },
        (err) => {
            console.log('Location request failed:', err.message);
        },
        {
            enableHighAccuracy: true,
            timeout: 8000,
            maximumAge: 60000
        }
    );
}

// Highlight a marker by scaling it up; unhighlight the previous one
function highlightMarker(lat, lng) {
    // Unhighlight previous
    if (_highlightedMarkerKey && markersByKey[_highlightedMarkerKey]) {
        var prevEl = markersByKey[_highlightedMarkerKey].getElement();
        if (prevEl) prevEl.classList.remove('ember-marker-highlight');
    }
    // Highlight new
    var key = lat + ',' + lng;
    _highlightedMarkerKey = key;
    if (markersByKey[key]) {
        var el = markersByKey[key].getElement();
        if (el) el.classList.add('ember-marker-highlight');
    }
}

// Fetch items and locations from your Flask API
async function loadMapItems() {
    try {
        const response = await fetch('/api/items');
        const items = await response.json();
        allItems = items;

        // Group items by location coordinates
        const locations = {};
        items.forEach(item => {
            if (item.latitude && item.longitude) {
                const key = `${item.latitude},${item.longitude}`;
                if (!locations[key]) {
                    locations[key] = { lat: item.latitude, lng: item.longitude, location_name: item.location_name, address: item.address, items: [] };
                }
                locations[key].items.push(item);
            }
        });

        // Create one marker per location with tooltip and click handler
        Object.values(locations).forEach(loc => {
            const marker = L.marker([loc.lat, loc.lng], { icon: campfireIcon }).addTo(map);
            const key = `${loc.lat},${loc.lng}`;
            markersByKey[key] = marker;
            const previewNames = loc.items.slice(0, 3).map(i => i.name).join(', ');
            const extra = loc.items.length > 3 ? ` +${loc.items.length - 3} more` : '';
            const tooltipHtml = `<strong>${loc.location_name}</strong><br>${loc.address || ''}<br><em>${previewNames}${extra}</em>`;
            marker.bindTooltip(tooltipHtml);
            marker.on('click', () => {
                if (typeof showLocationItems === 'function') showLocationItems(loc);
            });
        });

        // Also load standalone locations (no items yet)
        const locResponse = await fetch('/api/locations');
        const allLocations = await locResponse.json();
        allLocations.forEach(loc => {
            const key = `${loc.latitude},${loc.longitude}`;
            if (!locations[key]) {
                const standaloneMarker = L.marker([loc.latitude, loc.longitude], { icon: campfireEmptyIcon }).addTo(map);
                markersByKey[key] = standaloneMarker;
                standaloneMarker.bindTooltip(`<strong>${loc.name || loc.address}</strong><br>${loc.address || ''}`);
                standaloneMarker.on('click', () => {
                    if (typeof showLocationItems === 'function') {
                        showLocationItems({ location_name: loc.name || loc.address, address: loc.address, items: [] });
                    }
                });
            }
        });
        // Populate sidebar with nearby items (only if not viewing a specific location)
        if (typeof _viewingLocation !== 'undefined' && !_viewingLocation && typeof showNearbyItems === 'function') showNearbyItems();
    } catch (err) {
        console.log("Map loading offline mode - showing cached data");
    }
}

let offlineMapAvailable = false;

async function precacheMapData() {
    const cache = await caches.open('pittsburgh-map-v2');

    // Check if it's already cached
    const cachedResponse = await cache.match(PGH_MAP_URL);
    if (cachedResponse) {
        console.log("📍 Offline map data found in cache.");
        return;
    }

    offlineMapAvailable = confirm("Would you like to download map data for offline access?");

    if (offlineMapAvailable) {
        console.log("📥 Starting 60MB background download of Pittsburgh map...");
        
        try {
            const response = await fetch(PGH_MAP_URL);
            if (!response.ok) throw new Error('Network error');
            
            // This puts the full 60MB into the Workbox-managed cache
            await cache.put(PGH_MAP_URL, response);
            console.log("✅ Map cached! You can now go fully offline.");
        } catch (err) {
            console.error("❌ Precache failed:", err);
        }
    }
}

// Call this as soon as the page loads
precacheMapData();
loadMapItems();
requestUserLocation();

function toggleMapInteractions() {
    const mapElement = document.getElementById('map');

    if (navigator.onLine) {
        map.zoomControl?.enable();
        map.doubleClickZoom.enable();
        map.scrollWheelZoom.enable();
        map.touchZoom.enable();

        console.log("Map zoom enabled (Online)");
        mapElement.classList.remove('map-offline-locked');
    } else {
        map.zoomControl?.disable();
        map.doubleClickZoom.disable();
        map.scrollWheelZoom.disable();
        map.touchZoom.disable();
        
        console.log("Map zoom disabled (Offline)");
        mapElement.classList.add('map-offline-locked');
    }
}

// // 2. Listen for connection changes
// window.addEventListener('online', toggleMapInteractions);
// window.addEventListener('offline', toggleMapInteractions);

// // 3. Run once on load to set the correct state
// toggleMapInteractions();

function updateStatusUI() {
    const badge = document.getElementById('status-badge');
    const indicator = document.getElementById('status-indicator');
    const pulse = document.getElementById('status-pulse');
    const text = document.getElementById('status-text');

    if (navigator.onLine) {
        // Online State
        indicator.classList.remove('bg-red-500');
        indicator.classList.add('bg-green-500');
        pulse.classList.add('hidden');
        text.innerText = "Online";
        text.classList.remove('text-red-600');
        text.classList.add('text-gray-700');
    } else {
        // Offline State
        indicator.classList.remove('bg-green-500');
        indicator.classList.add('bg-red-500');
        pulse.classList.remove('hidden'); // Shows the ping animation
        text.innerText = "Offline Mode";
        text.classList.remove('text-gray-700');
        text.classList.add('text-red-600');
    }
}

window.addEventListener('online', updateStatusUI);
window.addEventListener('offline', updateStatusUI);

updateStatusUI();