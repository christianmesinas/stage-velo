// Mock _() functie voor pybabel extractie
function _(str) { return str; }

// initialiseren van een leaflet map en centreren op Antwerpen (51.2194, 4.4025)
var map = L.map('map').setView([51.2194,4.4025], 13);

//Openstreetmap-tegels toevoegen als kaartlaag
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

//Een legende toevoegen onderaan de code
var legend = L.control({position: 'bottomright'});
//legende
legend.onAdd = function (map) {
    var div = L.DomUtil.create('div', 'info legend');
    var categories = [
        { label: _("Stations met fietsen"), img: "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR04a9rmYuwrdOY-wd9R196xmBzJPWY6ERP6w&s" },
        { label: _("Volle stations"), img: "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTBAkFqlBX2bAivJuALy_bzTSN7ysB3GI634w&s" },
        { label: _("Lege stations"), img: "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR9SYMZI045Ex5qTuM1F2jFG0KBq1mWhG4YKw&s"},
        { label: _("Gesloten stations"), img: "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTwjZizx-6SkSoVR9tvHtDQGXPcxU-fQTyUHg&s"}
    ];
    //Voeg elke categorie toe aan de HTML van de legende
    categories.forEach(function(cat) {
        div.innerHTML +=
            '<img src="' + cat.img + '" style="width: 20px; height: 20px; vertical-align: middle; margin-right: 8px;margin-bottom: 2px">' +
            cat.label + '<br>';
    });

    return div;
};
//voeg legende toe aan de kaart
legend.addTo(map);
