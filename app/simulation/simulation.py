import random
import pandas as pd
import sys
import time

import psycopg2
from faker import Faker
import os

# Dynamisch pad naar velo.csv (2 niveaus omhoog vanaf script)
script_dir = os.path.dirname(__file__)
csv_path = os.path.join(script_dir, "velo.csv")
stations_df = pd.read_csv(csv_path)

fake = Faker()

# Verwerk stationsgegevens
stations_df.dropna(subset=["Naam"], inplace=True)

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

# Genereer gebruikers
def genereer_gebruikers(aantal):
    gebruikers = []
    for i in range(aantal):
        gebruikers.append({
            "id": i + 1,
            "voornaam": fake.first_name(),
            "achternaam": fake.last_name(),
        })
    return gebruikers

# Genereer fietsen en wijs ze toe aan stations
def genereer_fietsen(aantal, stations):
    fietsen = []
    fiets_id = 1
    station_slots = {station["id"]: station["capaciteit"] for station in stations}
    station_ids = list(station_slots.keys())
    random.shuffle(station_ids)

    totaal = len(station_ids)
    n_vol = round(totaal * 0.2)
    n_leeg = max(1, round(totaal * 0.01))
    n_partial = totaal - n_vol - n_leeg

    stations_vol = station_ids[:n_vol]
    stations_leeg = station_ids[n_vol:n_vol + n_leeg]
    stations_partial = station_ids[n_vol + n_leeg:]

    extra_vol_kans = 0.10

    max_per_station = {}
    for sid in stations_vol:
        max_per_station[sid] = station_slots[sid]
    for sid in stations_leeg:
        max_per_station[sid] = 0
    for sid in stations_partial:
        cap = station_slots[sid]
        if cap > 1:
            if random.random() < extra_vol_kans:
                max_per_station[sid] = cap
            else:
                max_per_station[sid] = random.randint(1, cap - 1)
        else:
            max_per_station[sid] = 0

    station_lookup = {s["id"]: s for s in stations}
    for s in stations:
        s["free_bikes"] = 0
        s["free_slots"] = s["capaciteit"]

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
            station_lookup[sid]["free_slots"] = max(station_lookup[sid]["free_slots"] - 1, 0)
            fiets_id += 1

        if len(fietsen) >= aantal:
            break

    while len(fietsen) < aantal:
        fietsen.append({
            "id": fiets_id,
            "station_id": None,
            "status": "onderweg"
        })
        fiets_id += 1

    return fietsen

gebruikers = genereer_gebruikers(58000)
fietsen = genereer_fietsen(10000, stations)

def genereer_geschiedenis(aantal_ritten, gebruikers, fietsen, stations):
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



# Simuleer ritten over tijd
def simulatie(stations, gebruikers, fietsen, versnelling=60, interval=1, duur=10):
    geschiedenis = []
    station_lookup = {s["id"]: s for s in stations}
    beschikbare_fietsen = [f for f in fietsen if f["status"] == "beschikbaar" and f["station_id"] is not None]

    for simulatie_stap in range(duur):
        print(f"Simulatiestap {simulatie_stap + 1} / {duur}")
        tijd_start = time.time()

        for _ in range(random.randint(5, 20)):
            if not beschikbare_fietsen:
                print("Geen beschikbare fietsen op dit moment.")
                break

            fiets = random.choice(beschikbare_fietsen)
            gebruiker = random.choice(gebruikers)
            begin_station = station_lookup.get(fiets["station_id"])
            eind_station = random.choice([s for s in stations if s["id"] != begin_station["id"]])

            geschiedenis.append({
                "gebruiker_id": gebruiker["id"],
                "fiets_id": fiets["id"],
                "begin_station_id": begin_station["id"],
                "eind_station_id": eind_station["id"],
                "duur_minuten": random.randint(2, 30)
            })

            fiets["station_id"] = eind_station["id"]
            begin_station["free_bikes"] = max(0, begin_station["free_bikes"] - 1)
            begin_station["free_slots"] += 1
            eind_station["free_bikes"] += 1
            eind_station["free_slots"] = max(0, eind_station["free_slots"] - 1)
            print(f"- Fiets {fiets['id']} verplaatst van {begin_station['name']} naar {eind_station['name']}")

        tijd_einde = time.time()
        wachttijd = max(0, interval - (tijd_einde - tijd_start))
        time.sleep(wachttijd)

    print(f"\nSimulatie voltooid met {len(geschiedenis)} ritten.")
    return geschiedenis



simulatie(stations,gebruikers,fietsen, 60,1,30)

# Alleen uitvoeren als script direct wordt gestart
#if __name__ == "__main__":
 #   gebruikers = genereer_gebruikers(58000)
 #   fietsen = genereer_fietsen(10000, stations)

#    if "-s" in sys.argv:
#        simulatie(stations, gebruikers, fietsen, versnelling=60, interval=1, duur=30)
#    else:
#        print("Gebruik '-s' om de simulatie te starten.")


conn = psycopg2.connect(
    dbname="velo_community",
    user="admin",
    password="Velo123",
    host="localhost",
    port="5433"
)
cur = conn.cursor()

for gebruiker in gebruikers:
    cur.execute("""
        INSERT INTO users (id, voornaam, achternaam, email, abonnementstype, registratie_datum, postcode, stad)
        VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s)
    """, (
        gebruiker["id"],
        gebruiker["voornaam"],
        gebruiker["achternaam"],
        f"{gebruiker['voornaam']}.{gebruiker['achternaam']}@example.com".lower(),
        random.choice(["Basis", "Premium", "Flex"]),
        fake.postcode(),
        fake.city()
    ))

for fiets in fietsen:
    cur.execute("""
        INSERT INTO bikes (id, type, status) VALUES (%s, %s, %s)
    """, (
        fiets["id"],
        random.choice(["stadsfiets", "elektrisch"]),
        fiets["status"]
    ))

for station in stations:
    cur.execute("""
        INSERT INTO stations (id, naam, adres, latitude, longitude, capaciteit, free_slots, parked_bikes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        station["id"],
        station["name"],
        station["straat"],
        fake.latitude(),
        fake.longitude(),
        station["capaciteit"],
        station["free_slots"],
        station["free_bikes"]
    ))

from datetime import datetime, timedelta

for rit in genereer_geschiedenis(10000, gebruikers, fietsen, stations):
    starttijd = datetime.now() - timedelta(minutes=rit["duur_minuten"])
    eindtijd = datetime.now()

    cur.execute("""
        INSERT INTO rentals (user_id, bike_id, start_station_id, eind_station_id, starttijd, eindtijd, prijs)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        rit["gebruiker_id"],
        rit["fiets_id"],
        rit["begin_station_id"],
        rit["eind_station_id"],
        starttijd,
        eindtijd,
        round(rit["duur_minuten"] * 0.15, 2)  # voorbeeldprijs
    ))

conn.commit()
cur.close()
conn.close()