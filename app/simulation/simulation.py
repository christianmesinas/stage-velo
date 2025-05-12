import random
import pandas as pd
import sys
import time
from faker import Faker

fake = Faker()

# CSV inlezen voor een reële simulatie
stations_df = pd.read_csv("velo.csv")
stations_df.dropna(subset=["Naam"], inplace=True)

# Filteren relevante velden
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

# Random gebruikers genereren
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
    n_vol = round(totaal * 0.2)  # 20% van de stations volledig vol
    n_leeg = max(1, round(totaal * 0.01))  # 1% van de stations leeg
    n_partial = totaal - n_vol - n_leeg  # Resterende stations gedeeltelijk bezet

    stations_vol = station_ids[:n_vol]
    stations_leeg = station_ids[n_vol:n_vol + n_leeg]
    stations_partial = station_ids[n_vol + n_leeg:]

    extra_vol_kans = 0.10  # 10% kans dat een partial station vol is

    max_per_station = {}
    for sid in stations_vol:
        max_per_station[sid] = station_slots[sid]  # Volledig vol
    for sid in stations_leeg:
        max_per_station[sid] = 0  # Leeg
    for sid in stations_partial:
        cap = station_slots[sid]
        if cap > 1:
            if random.random() < extra_vol_kans:
                max_per_station[sid] = cap  # Maak toch vol
            else:
                max_per_station[sid] = random.randint(1, cap - 1)  # Gedeeltelijk bezet
        else:
            max_per_station[sid] = 0  # Te kleine capaciteit

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
            # Verminder free_slots voor elke toegewezen fiets, ongeacht status
            station_lookup[sid]["free_slots"] = max(station_lookup[sid]["free_slots"] - 1, 0)
            fiets_id += 1

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

# Geschiedenis ritten simuleren
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

#functies callen zodat we geschiedenis kunnen genereren
gebruikers = genereer_gebruikers(58000)
fietsen = genereer_fietsen(10000, stations)
# Genereer geschiedenis
#geschiedenis = genereer_geschiedenis(10000, gebruikers, fietsen, stations)

def simulatie(stations, gebruikers, fietsen, versnelling=60, interval=1, duur=10):
    ###
    # simulatie met tijdsversnelling, versnelling op 1 = realtime en versnelling op 60 = 1 minuut per seconde
    # interval : tijd tussen stappen van de simulatie, duur: aantal simulatiestappen.
    # duur : aantal minuten dat de simulatie zal draaien. dus met een versnelling van 60 interval van 1 en duur van 10 minuten.
    # zal de simulatie 10 seconden duren.
    ###
    geschiedenis = []
    station_lookup = {s["id"]: s for s in stations}
    beschikbare_fietsen = [f for f in fietsen if f["status"] == "beschikbaar" and f["station_id"] is not None]

    for simulatie_stap in range(duur):
        print(f"Simulatiestap {simulatie_stap + 1 / duur}")
        tijd_start = time.time()

        #ritten simuleren
        for _ in range(random.randint(5,20)):
            if not beschikbare_fietsen:
                print("Geen beschikbare fietsen op dit moment.")
                break

            fiets = random.choice(beschikbare_fietsen)
            gebruiker = random.choice(gebruikers)
            begin_station = station_lookup.get(fiets["station_id"])
            eind_station = random.choice([s for s in stations if s["id"] != begin_station["id"]])

            #rit toevoegen
            geschiedenis.append({
                "gebruiker_id": gebruiker["id"],
                "fiets_id": fiets["id"],
                "begin_station_id": begin_station["id"],
                "eind_station_id": eind_station["id"],
                "duur_minuten": random.randint(2, 30)
            })
            #we moeten ook de fietsstatus updaten
            fiets["station_id"] = eind_station["id"]
            begin_station["free_bikes"] = max(0, begin_station["free_bikes"] - 1)
            begin_station["free_slots"] += 1
            eind_station["free_bikes"] += 1
            eind_station["free_slots"] = max(0, eind_station["free_slots"] - 1)
            print(f"- Fiets {fiets['id']} verplaatst van {begin_station['name']} naar {eind_station['name']}")

        tijd_einde = time.time()
        wachttijd = max(0, interval - (tijd_einde - tijd_start))
        time.sleep(wachttijd)
    print(f"\n Simulatie voltooid met {len(geschiedenis)} ritten.")
    return geschiedenis

simulatie(stations,gebruikers,fietsen, 60,1,30)
