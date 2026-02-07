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

// Fetch items from your Flask API
async function loadMapItems() {
    try {
        const response = await fetch('/api/items');
        const items = await response.json();

        items.forEach(item => {
            console.log(item);
            if (item.latitude && item.longitude) {
                const marker = L.marker([item.latitude, item.longitude]).addTo(map);
                marker.bindPopup(`
                    <strong>${item.item_name}</strong><br>
                    ${item.item_desc}<br>
                    <button onclick="contactOwner(${item.user_id})">Request</button>
                `);
            }
        });
    } catch (err) {
        console.log("Map loading offline mode - showing cached data");
    }
}

loadMapItems();