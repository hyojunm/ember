// Initialize the map at a default location (or user's GPS)
const map = L.map('map', {
    center: [40.4406, -79.9959], // Starting coordinates
    zoom: 15,                    // Starting zoom level (Neighborhood view)
    minZoom: 12,                 // Maximum zoom out (City view)
    maxZoom: 18,                 // Maximum zoom in (Street view)
    // maxBounds: [                 // Optional: Lock the map to a specific area
    //     [40.60, -74.20],         // Southwest coordinates
    //     [40.85, -73.80]          // Northeast coordinates
    // ],
    maxBoundsViscosity: 1.0      // Prevents the user from dragging outside the bounds
});

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap'
}).addTo(map);

const userIcon = L.divIcon({
    className: 'user-location-marker',
    html: '<div class="user-location-pulse" aria-hidden="true"></div>',
    iconSize: [18, 18],
    iconAnchor: [9, 9]
});

let userMarker = null;

function setUserLocation(lat, lng) {
    const coords = [lat, lng];
    map.setView(coords, Math.max(map.getZoom(), 15));

    if (!userMarker) {
        userMarker = L.marker(coords, { icon: userIcon, zIndexOffset: 1000 }).addTo(map);
    } else {
        userMarker.setLatLng(coords);
    }
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

// Fetch items from your Flask API
async function loadMapItems() {
    try {
        const response = await fetch('/api/items');
        const items = await response.json();

        // Group items by location coordinates
        const locations = {};
        items.forEach(item => {
            if (item.latitude && item.longitude) {
                const key = `${item.latitude},${item.longitude}`;
                if (!locations[key]) {
                    locations[key] = { lat: item.latitude, lng: item.longitude, location_name: item.location_name, items: [] };
                }
                locations[key].items.push(item);
            }
        });

        // Create one marker per location with all items in the popup
        Object.values(locations).forEach(loc => {
            const marker = L.marker([loc.lat, loc.lng]).addTo(map);
            const itemsHtml = loc.items.map(item => `
                <strong>${item.name}</strong><br>
                ${item.description}<br>
                <button onclick="contactOwner(${item.id})">Request</button>
            `).join('<hr>');
            marker.bindPopup(`<h3>${loc.location_name}</h3>${itemsHtml}`);
        });
    } catch (err) {
        console.log("Map loading offline mode - showing cached data");
    }
}

loadMapItems();

requestUserLocation();

map.on('dblclick', (event) => {
    const coords = event.latlng;
    L.marker(coords).addTo(map);
});
