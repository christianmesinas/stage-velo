import os
import json
import random
import pandas as pd
from faker import Faker

fake = Faker()

#bestandsnamen
USERS_FILE = "gebruikers.json"
BIKES_FILE = "fietsen.json"
STATIONS_FILE = "stations.json"

#CSV moet ingelezen worden voor een reële simulatie
stations_df = pd.read_csv("velo.csv")
stations_df.dropna(subset=["Naam"], inplace=True)

#filteren relevante velden
stations = []
for _, row in stations_df.iterrows():
    stations.append({
        "id": row["OBJECTID"],
        "name": row["Naam"],
        "straat": row.get("Straatnaam", ""),
        "postcode": row.get("Postcode", ""),
        "capaciteit": row.get("Aantal_plaatsen", 0),
        "status": row.get("Gebruik", "ONBEKEND")
    })

#random gebruikers genereren
def genereer_gebruikers(aantal):
    gebruikers = []
    for i in range(aantal):
        gebruikers.append({
            "id": i + 1,
            "voornaam": fake.first_name(),
            "achternaam": fake.last_name(),
        })
    return gebruikers

def genereer_fietsen(aantal, stations):
    fietsen = []
    fiets_id = 1
    station_slots = {station["id"]: station["capaciteit"] for station in stations}
    station_ids = list(station_slots.keys())

    # Verdeel stations in 3 groepen:
    # - Vol (geen vrije slots)
    # - Leeg (0 fietsen)
    # - Gedeeltelijk gevuld (1 tot capaciteit - 1)
    random.shuffle(station_ids)
    totaal = len(station_ids)
    n_vol = max(1, totaal // 3)
    n_leeg = max(1, totaal // 3)
    n_partial = totaal - n_vol - n_leeg

    stations_vol = station_ids[:n_vol]
    stations_leeg = station_ids[n_vol:n_vol + n_leeg]
    stations_partial = station_ids[n_vol + n_leeg:]

    # Bepaal hoeveel fietsen er per station mogen komen
    max_per_station = {}
    for sid in stations_vol:
        max_per_station[sid] = station_slots[sid]  # Vol
    for sid in stations_leeg:
        max_per_station[sid] = 0  # Leeg
    for sid in stations_partial:
        max_per_station[sid] = random.randint(1, station_slots[sid] - 1)  # Tussen 1 en capaciteit - 1

    # Toewijzing van fietsen
    for sid in station_ids:
        toewijsbaar = min(max_per_station[sid], aantal - len(fietsen))
        for _ in range(toewijsbaar):
            fietsen.append({
                "id": fiets_id,
                "station_id": sid,
                "status": random.choice(["beschikbaar", "onderhoud"])
            })
            fiets_id += 1
        if len(fietsen) >= aantal:
            break

    # Voeg resterende fietsen toe als "onderweg"
    while len(fietsen) < aantal:
        fietsen.append({
            "id": fiets_id,
            "station_id": None,
            "status": "onderweg"
        })
        fiets_id += 1

    return fietsen

#testen van de code en steken in json files
if os.path.exists(USERS_FILE) and os.path.exists(BIKES_FILE) and os.path.exists(STATIONS_FILE):
    keuze = input("Gegevens gevonden. Opnieuw genereren (j/n): ").strip().lower()
else:
    keuze = "j"

if keuze == "j":
    gebruikers = genereer_gebruikers(58000)
    fietsen = genereer_fietsen(10000, stations)

    #schrijven naar json formaat
    with open(USERS_FILE, "w") as f:
        json.dump(gebruikers, f, indent=2)
    with open(BIKES_FILE, "w") as f:
        json.dump(fietsen, f, indent=2)
    with open(STATIONS_FILE, "w") as f:
        json.dump(stations, f, indent=2)
    print("simulatie aangemaakt en opgeslagen.")

else:
    print("Bestaande gegevens worden gebruikt.")
    with open(USERS_FILE) as f:
        gebruikers = json.load(f)
    with open(BIKES_FILE) as f:
        fietsen = json.load(f)
    with open(STATIONS_FILE) as f:
        stations = json.load(f)

#genereer free-bikes en free-slots per station
from collections import defaultdict

# tellen van beschikbare fietsen én bezette slots
beschikbare_fietsen = defaultdict(int)
bezettingsgraad = defaultdict(int)

for fiets in fietsen:
    sid = fiets["station_id"]
    if sid is None:
        continue
    bezettingsgraad[sid] += 1
    if fiets["status"] == "beschikbaar":
        beschikbare_fietsen[sid] += 1

for station in stations:
    sid = station["id"]
    free_bikes = beschikbare_fietsen.get(sid, 0)
    bezet = bezettingsgraad.get(sid, 0)
    station["free_bikes"] = free_bikes
    station["free_slots"] = max(station["capaciteit"] - bezet, 0)

#stations data in json steken
with open(STATIONS_FILE, "w") as f:
    json.dump(stations, f, indent=2)

print("beschikbare fietsen en vrije sloten data toegevoegd aan stationsdata")


#geschiedenis ritten simuleren
def genereer_geschiedenis(aantal_ritten, gebruikers,fietsen, stations):
    geschiedenis = []
    for i in range(aantal_ritten):
        gebruiker = random.choice(gebruikers)
        fiets = random.choice([f for f in fietsen if f["status"] == "beschikbaar"])
        begin_station = next((s for s in stations if s["id"] == fiets["station_id"]), None)
        eind_station = random.choice(stations)

        if begin_station and eind_station and begin_station["id"] != eind_station["id"]:
            geschiedenis.append({
                "gebruiker_id": gebruiker["id"],
                "fiets_id": fiets["id"],
                "begin_station_id": begin_station["id"],
                "eind_station_id": eind_station["id"],
                "duur_minuten": random.randint(2, 30)
            })
    return geschiedenis

geschiedenis = genereer_geschiedenis(10000, gebruikers,fietsen,stations)

#json file inladen
with open("geschiedenis.json", "w") as f:
    json.dump(geschiedenis, f, indent=2)

print("geschiedenis gesimuleerd!")