import random
import pandas as pd
import sys
from datetime import datetime, timedelta
import time
import io
from app.database.session import SessionLocal
from app.database.models import Fiets

import psycopg2
from faker import Faker
import os

# Dynamisch pad naar velo.csv (2 niveaus omhoog vanaf script)
script_dir = os.path.dirname(__file__)
csv_path = os.path.join(script_dir, "velo.csv")
stations_df = pd.read_csv(csv_path)

fake = Faker()
antwerpen_postcodes = ['2000','2018','2020','2030','2040','2050','2060','2100','2130','2140','2150','2170','2180','2600','2610','2610','2660'] #alle postcodes antwerpen in een lijst

# Verwerk stationsgegevens
stations_df.dropna(subset=["Naam"], inplace=True)

stations = []
for _, row in stations_df.iterrows(): #de data in de stations.csv (van velo antwerpen) in een lijst stations steken.
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
    gebruikers = [] #lege lijst gebruikers aangemaakt
    for i in range(aantal): #loop met als i het aantal gebruikers dat we willen genereren
        gebruikers.append({
            "id": i + 1,
            "voornaam": fake.first_name(),
            "achternaam": fake.last_name(),
            "email": f"{fake.last_name()}.{fake.first_name()}@example.com".lower(),
            "postcode": random.choice(antwerpen_postcodes),
            "abonnementstype": random.choice(['Basis','Premium','Flex']),
        })
    return gebruikers


# Genereer fietsen en wijs ze toe aan stations
def genereer_fietsen(aantal, stations):
    fietsen = []
    fiets_id = 1
    station_slots = {station["id"]: station["capaciteit"] for station in stations}
    station_ids = list(station_slots.keys())
    random.shuffle(station_ids) #random toewijzing van stations

    totaal = len(station_ids)
    #een gecontroleerde random choice waar 20 procent van de stations vol zijn, 1 procent volledig leeg zijn.
    #de resterdende 71 procent heeft dan een willekeurig aantal fietsen en vrije slots.
    n_vol = round(totaal * 0.2)
    n_leeg = max(1, round(totaal * 0.01))
    n_partial = totaal - n_vol - n_leeg
    #een onderscheid tussen volle stations , lege stations en stations die niet leeg alsook niet vol zijn.
    stations_vol = station_ids[:n_vol]
    stations_leeg = station_ids[n_vol:n_vol + n_leeg]
    stations_partial = station_ids[n_vol + n_leeg:]

    extra_vol_kans = 0.10

    max_per_station = {}
    for sid in stations_vol: #
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
            status = random.choices(["beschikbaar", "onderhoud"], weights=[0.8, 0.2])[0]
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


def gewogen_starttijd(datum):
    #we moeten a.d.h. van de uur van de dag beslissen hoe groot de kans is dat op die moment een fiets gepakt wordt.
    gewichten = []
    for uur in range(24):
        if 8 <= uur < 18: #spitsuur, piekuren
            gewichten += [uur] * 5 #hoogste activiteit
        elif 6 <= uur < 8 or 18 <= uur < 20: #mensen die vroeger naar en later van werk vertrekken.
            gewichten += [uur] * 2
        else:
            gewichten += [uur] #daluren
    gekozen_uur = random.choice(gewichten)
    gekozen_minuten = random.randint(0,59)
    return datetime.combine(datum, datetime.min.time()) + timedelta(hours=gekozen_uur,minutes=gekozen_minuten)


def genereer_geschiedenis(gebruikers, fietsen, stations, dagen=28, ritten_per_fiets_per_dag=4): #velo gemiddelde is 4 ritten/fiets/dag
    geschiedenis = []
    vandaag = datetime.today().date() #simulatie telt terug van de dag van vandaag, als default de voorbije 28dagen (1maand)
    beschikbare_fietsen = [f for f in fietsen if f["status"] == "beschikbaar" and f["station_id"] is not None]

    for dag_offset in range(dagen):
        datum = vandaag - timedelta(days=(dagen - dag_offset - 1)) #dagen tellen van het aantal dagen tot dag van vandaag
        for fiets in beschikbare_fietsen:
            for _ in range(ritten_per_fiets_per_dag):
                gebruiker = random.choice(gebruikers)
                begin_station = next((s for s in stations if s["id"] == fiets["station_id"]), None)
                eind_station = random.choice([s for s in stations if s["id"] != fiets["station_id"]])

                if not begin_station or not eind_station:
                    continue

                duur = random.randint(2,30) #random duur in minuten voor een fietsrit
                starttijd = gewogen_starttijd(datum)
                eindtijd = starttijd + timedelta(minutes=duur)

                geschiedenis.append({
                    "gebruiker_id": gebruiker["id"],
                    "fiets_id": fiets["id"],
                    "begin_station_id": begin_station["id"],
                    "eind_station_id": eind_station["id"],
                    "starttijd": starttijd.strftime("%Y-%m-%d %H:%M:%S"),
                    "eindtijd": eindtijd.strftime("%Y-%m-%d %H:%M:%S"),
                    "duur_minuten": duur
                })

                fiets["station_id"] = eind_station["id"] #de fiets wordt teogekend aan zijn nieuwe station.
    return geschiedenis


def geschiedenis_to_csv_buffer(geschiedenis): #we gaan geschiedenis eerst in een csv steken zodat we het met COPY kunnen doorpushen naar de db
    buffer = io.StringIO()
    for rit in geschiedenis:
        buffer.write(
            f"{rit['gebruiker_id']},{rit['fiets_id']},{rit['begin_station_id']},"
            f"{rit['eind_station_id']},{rit['starttijd']},{rit['eindtijd']},{rit['duur_minuten']}\n"
        )
    buffer.seek(0)
    return buffer


# Simuleer ritten over tijd
def simulatie(stations, gebruikers, fietsen,  dagen=1, ritten_per_fiets_per_dag=4):
    geschiedenis = []
    station_lookup = {s["id"]: s for s in stations}
    beschikbare_fietsen = [f for f in fietsen if f["status"] == "beschikbaar" and f["station_id"] is not None]
    vandaag = datetime.today().date()

    for dag_offset in range(dagen):#de simulatie telt de voorbije aantal dagen.
        datum = vandaag - timedelta(days=dag_offset)
        print(f"\bSimulatie voor {datum}...")

        for _ in range(random.randint(5, 20)):
            if not beschikbare_fietsen:
                print("Geen beschikbare fietsen op dit moment.")
                break

        for fiets in beschikbare_fietsen:
            for _ in range(ritten_per_fiets_per_dag):
                gebruiker = random.choice(gebruikers)
                begin_station = station_lookup.get(fiets["station_id"])
                bepaling_eind_station = [s for s in stations if s["id"] != begin_station["id"]] #de eindstation mag niet hetzelfde zijn als waar de fiets wordt genomen.
                if not begin_station or not bepaling_eind_station:
                    continue

                eind_station = random.choice(bepaling_eind_station) #de eind_station (eindpunt van rit) moet random bepaalt worden.
                duur = random.randint(2,30)
                starttijd = gewogen_starttijd(datum)
                eindtijd = starttijd + timedelta(minutes=duur)

                geschiedenis.append({
                    "gebruiker_id": gebruiker["id"],
                    "fiets_id": fiets["id"],
                    "begin_station_id": begin_station["id"],
                    "eind_station_id": eind_station["id"],
                    "starttijd": starttijd.strftime("%Y-%m-%d %H:%M:%S"),
                    "eindtijd": eindtijd.strftime("%Y-%m-%d %H:%M:%S"),
                    "duur_minuten": duur
                })

                fiets["station_id"] = eind_station["id"] #de fiets moet gelinkt worden aan de eindstation.
                begin_station["free_bikes"] = max(0, begin_station["free_bikes"] - 1)
                begin_station["free_slots"] += 1 #er komt een slot vrij bij de station waar de fiets wordt gepakt.
                eind_station["free_bikes"] += 1 #er komt een fiets erbij bij de station waar de fiets wordt achter gelaten.
                eind_station["free_slots"] = max(0, eind_station["free_slots"] - 1)
                print(f"- {starttijd.strftime('%H:%M')} Fiets {fiets['id']} van {begin_station['name']} naar {eind_station['name']} ({duur} min)")

    print(f"Simulatie voltooid met {len(geschiedenis)} ritten over {dagen}")
    return geschiedenis


#simulatie(stations,gebruikers,fietsen, 60)


def sla_stations_op_in_db(stations):
    session = SessionLocal()
    try:
        for s in stations:
            bestaand_station = session.get(Station, s["id"])
            if bestaand_station:
                # Update bestaande waarden
                bestaand_station.naam = s["name"]
                bestaand_station.straat = s["straat"]
                bestaand_station.postcode = s["postcode"]
                bestaand_station.latitude = None
                bestaand_station.longitude = None
                bestaand_station.capaciteit = s["capaciteit"]
                bestaand_station.status = s["status"]
                bestaand_station.free_slots = s["free_slots"]
                bestaand_station.parked_bikes = s["free_bikes"]
            else:
                nieuw_station = Station(
                    id=s["id"],
                    naam=s["name"],
                    straat=s["straat"],
                    postcode=s["postcode"],
                    latitude=None,
                    longitude=None,
                    capaciteit=s["capaciteit"],
                    status=s["status"],
                    free_slots=s["free_slots"],
                    parked_bikes=s["free_bikes"]
                )
                session.add(nieuw_station)
        session.commit()
        print(f"{len(stations)} stations opgeslagen of bijgewerkt in de database.")
    except Exception as e:
        session.rollback()
        print("❌ Fout bij opslaan van stations:", e)
    finally:
        session.close()

sla_stations_op_in_db(stations)


def sla_fietsen_op_in_db(fietsen):
    session = SessionLocal()
    try:
        for f in fietsen:
            fiets = Fiets(
                id=f["id"],
                # station_id=f["station_id"],
                status=f["status"]
            )
            session.merge(fiets)  # merge voorkomt fouten bij dubbele ID’s
        session.commit()
        print(f"{len(fietsen)} fietsen opgeslagen in de database.")
    except Exception as e:
        session.rollback()
        print("❌ Fout bij opslaan fietsen:", e)
    finally:
        session.close()



if __name__ == "__main__": #zorgt ervoor dat de functies enkel runnen wanneer ze worden opgeroepen, en niet tijdens import.
    gebruikers = genereer_gebruikers(30000)
    fietsen = genereer_fietsen(2000, stations)
    geschiedenis = genereer_geschiedenis(gebruikers, fietsen, stations)
    sla_fietsen_op_in_db(fietsen)

    buffer = geschiedenis_to_csv_buffer(geschiedenis)
    with open("simulatie_output_csv", "w") as f:
        f.write(buffer.getvalue())
