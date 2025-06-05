// static/js/maps.js

// Translation function to use window.translations
function _(str) {
    return window.translations && window.translations[str] ? window.translations[str] : str;
}

// Initialize a Leaflet map centered on Antwerp (51.2194, 4.4025)
var map = L.map('map').setView([51.2194, 4.4025], 13);

// Add OpenStreetMap tiles as the map layer
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// Add a legend at the bottom right
var legend = L.control({ position: 'bottomright' });

legend.onAdd = function (map) {
    var div = L.DomUtil.create('div', 'info legend');
    var categories = [
        { label: _("Stations met fietsen"), img: "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR04a9rmYuwrdOY-wd9R196xmBzJPWY6ERP6w&s" },
        { label: _("Volle stations"), img: "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTBAkFqlBX2bAivJuALy_bzTSN7ysB3GI634w&s" },
        { label: _("Lege stations"), img: "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR9SYMZI045Ex5qTuM1F2jFG0KBq1mWhG4YKw&s" },
        { label: _("Gesloten stations"), img: "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTwjZizx-6SkSoVR9tvHtDQGXPcxU-fQTyUHg&s" }
    ];

    // Add each category to the legend HTML
    categories.forEach(function (cat) {
        div.innerHTML +=
            '<img src="' + cat.img + '" style="width: 20px; height: 20px; vertical-align: middle; margin-right: 8px; margin-bottom: 2px">' +
            cat.label + '<br>';
    });

    return div;
};

// Add the legend to the map
legend.addTo(map);