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
        "status": row.get("Gebruik", "ONBEKEND"),
        "free_bikes": 0,
        "free_slots": row.get("Aantal_plaatsen", 0)
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
    random.shuffle(station_ids)

    totaal = len(station_ids)
    n_vol = round(totaal * 0.30)
    n_leeg = max(1, round(totaal * 0.02))
    n_partial = totaal - n_vol - n_leeg

    stations_vol = station_ids[:n_vol]
    stations_leeg = station_ids[n_vol:n_vol + n_leeg]
    stations_partial = station_ids[n_vol + n_leeg:]

    # Extra kans dat een gedeeltelijk station toch vol is
    extra_vol_kans = 0.10  # 10% van de partial stations

    max_per_station = {}
    for sid in stations_vol:
        max_per_station[sid] = station_slots[sid]
    for sid in stations_leeg:
        max_per_station[sid] = 0
    for sid in stations_partial:
        cap = station_slots[sid]
        if cap > 1:
            if random.random() < extra_vol_kans:
                max_per_station[sid] = cap  # maak toch vol
            else:
                max_per_station[sid] = random.randint(1, cap - 1)
        else:
            max_per_station[sid] = 0  # capaciteit te klein voor partial

    # Reset free_bikes en free_slots
    station_lookup = {s["id"]: s for s in stations}
    for s in stations:
        s["free_bikes"] = 0
        s["free_slots"] = s["capaciteit"]

    # Fietsen toewijzen
    for sid in station_ids:
        toewijsbaar = min(max_per_station[sid], aantal - len(fietsen))
        for _ in range(toewijsbaar):
            status = random.choice(["beschikbaar", "onderhoud"])
            fietsen.append({
                "id": fiets_id,
                "station_id": sid,
                "status": status
            })
            if status == "beschikbaar":
                station_lookup[sid]["free_bikes"] += 1
            fiets_id += 1

        # Update vrije slots
        station = station_lookup[sid]
        station["free_slots"] = max(station["capaciteit"] - station["free_bikes"], 0)

        if len(fietsen) >= aantal:
            break

    # Resterende fietsen zijn "onderweg"
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