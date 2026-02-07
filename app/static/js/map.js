// Restore saved map position or use defaults
const savedMap = JSON.parse(localStorage.getItem('emberMapView'));
const mapCenter = savedMap ? [savedMap.lat, savedMap.lng] : [40.4406, -79.9959];
const mapZoom = savedMap ? savedMap.zoom : 15;

const map = L.map('map', {
    center: mapCenter,
    zoom: mapZoom,
    minZoom: 12,                 // Maximum zoom out (City view)
    maxZoom: 18,                 // Maximum zoom in (Street view)
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

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap'
}).addTo(map);

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

loadMapItems();

requestUserLocation();

