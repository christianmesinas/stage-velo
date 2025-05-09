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

    # sommige stations moeten lege plaatsen hebben (realisme)
    max_per_station = {
        station["id"]: random.randint(0, cap) for station, cap in zip(stations, station_slots.values())
    }

    # Sorteer stations op willekeurige volgorde
    station_ids = list(station_slots.keys())
    random.shuffle(station_ids)

    for station_id in station_ids:
        toewijsbaar = min(max_per_station[station_id], aantal - len(fietsen))
        for _ in range(toewijsbaar):
            fietsen.append({
                "id": fiets_id,
                "station_id": station_id,
                "status": random.choice(["beschikbaar", "onderhoud"])
            })
            fiets_id += 1
        if len(fietsen) >= aantal:
            break

    # Voeg wat fietsen toe die "onderweg" zijn (dus zonder station)
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
    keuze = input("Gegevens gevonden. Opnieuw genereren (j/n").strip().lower()
else:
    keuze = "j"

if keuze == "j":
    gebruikers = genereer_gebruikers(58000)
    fietsen = genereer_fietsen(4200, stations)

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

