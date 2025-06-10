import random
import pandas as pd
import sys
from datetime import datetime, timedelta
import time
import io
from app.database.session import SessionLocal
from app.database.models import Fiets, Station, Gebruiker, Geschiedenis
import psycopg2
from faker import Faker
import os
import math

# Dynamisch pad naar velo.csv
script_dir = os.path.dirname(__file__)
csv_path = os.path.join(script_dir, "stations.csv")
stations_df = pd.read_csv(csv_path)

fake = Faker()
antwerpen_postcodes = ['2000', '2018', '2020', '2030', '2040', '2050', '2060', '2100', '2130', '2140', '2150', '2170',
                       '2180', '2600', '2610', '2610', '2660']

# Verwerk stationsgegevens
stations_df.dropna(subset=["naam"], inplace=True)

stations = []
for _, row in stations_df.iterrows():
    stations.append({
        "id": row["id"],
        "name": row["naam"],
        "straat": row["adres"],
        "latitude": row["latitude"],
        "longitude": row["longitude"],
        "capaciteit": row["capaciteit"],
        "status": 'OPN',
        "free_bikes": 0,
        "free_slots": 0,
        "postcode": row.get("postcode", random.choice(antwerpen_postcodes))
    })


# Cache afstanden tussen stations
def cache_afstanden(stations):
    afstanden = {}
    for s1 in stations:
        for s2 in stations:
            if s1["name"] != s2["name"]:
                afstand = bereken_afstand(s1["latitude"], s1["longitude"], s2["latitude"], s2["longitude"])
                afstanden[(s1["name"], s2["name"])] = afstand
    return afstanden


# Helperfunctie voor afstandsberekening (Haversine formule)
def bereken_afstand(lat1, lon1, lat2, lon2):
    R = 6371  # Aardradius in km
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c  # Afstand in km


# Vind nabijgelegen station met beschikbare fietsen
def vind_nabijgelegen_station(huidig_station, stations, fietsen, afstanden):
    nabijgelegen = sorted(
        [s for s in stations if s["name"] != huidig_station["name"] and s["free_bikes"] > 0],
        key=lambda s: afstanden.get((huidig_station["name"], s["name"]), float('inf'))
    )
    return nabijgelegen[0] if nabijgelegen else None


# Genereer gebruikers
def genereer_gebruikers(aantal):
    gebruikers = []
    for i in range(aantal):
        gebruikers.append({
            "id": i + 1,
            "voornaam": fake.first_name(),
            "achternaam": fake.last_name(),
            "email": f"{fake.last_name()}.{fake.first_name()}@example.com".lower(),
            "postcode": random.choice(antwerpen_postcodes),
            "abonnementstype": random.choices(['Dagpas', 'Weekpas', 'Jaarkaart'], weights=[60, 10, 30], k=1)[0]
        })
    return gebruikers

#helper functie voor validatei
def valideer_station_capaciteit(station):
    total_bikes = station["free_bikes"]
    total_slots = station["free_slots"]
    capaciteit = station["capaciteit"]

    # Corrigeer als totaal de capaciteit overschrijdt
    if total_bikes + total_slots > capaciteit:
        # Prioriteer fietsen, pas slots aan
        station["free_slots"] = max(0, capaciteit - station["free_bikes"])
    elif total_bikes + total_slots < capaciteit:
        # Vul ontbrekende slots aan
        station["free_slots"] = capaciteit - station["free_bikes"]

    # Zorg dat geen negatieve waarden mogelijk zijn
    station["free_bikes"] = max(0, station["free_bikes"])
    station["free_slots"] = max(0, station["free_slots"])


# Genereer fietsen en wijs ze toe aan stations
def genereer_fietsen(aantal, stations):
    fietsen = []
    fiets_id = 1
    station_slots = {station["id"]: station["capaciteit"] for station in stations}
    station_ids = list(station_slots.keys())
    random.shuffle(station_ids)

    totaal = len(station_ids)
    n_vol = round(totaal * 0.0001)
    n_leeg = max(1, round(totaal * 0.000001))
    n_partial = totaal - n_vol - n_leeg

    stations_vol = station_ids[:n_vol]
    stations_leeg = station_ids[n_vol:n_vol + n_leeg]
    stations_partial = station_ids[n_vol + n_leeg:]

    extra_vol_kans = 0.0001
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
        station = station_lookup[sid]
        toewijsbaar = min(max_per_station[sid], aantal - len(fietsen), station["free_slots"])
        for _ in range(toewijsbaar):
            status = random.choices(["beschikbaar", "onderhoud"], weights=[0.8, 0.2])[0]
            fietsen.append({
                "id": fiets_id,
                "station_naam": station_lookup[sid]["name"],
                "status": status,
                "ritten_vandaag": 0,
                "onderhoud_teller": random.randint(10, 20),
                "in_gebruik_tot": None
            })
            if status == "beschikbaar":
                station_lookup[sid]["free_bikes"] += 1
            station["free_slots"] -= 1
            # Valideer na elke toevoeging
            valideer_station_capaciteit(station)
            fiets_id += 1

        if len(fietsen) >= aantal:
            break

    # Voeg overige fietsen toe als "onderweg"

    while len(fietsen) < aantal:
        fietsen.append({
            "id": fiets_id,
            "station_naam": None,
            "status": "onderweg",
            "ritten_vandaag": 0,
            "onderhoud_teller": random.randint(10, 20),
            "in_gebruik_tot": None
        })
        fiets_id += 1
    return fietsen


# Simuleer herverdeling van fietsen door operator
def herverdeel_fietsen(stations, fietsen):
    if not any(s["free_bikes"] <= s["capaciteit"] * 0.1 or s["free_bikes"] >= s["capaciteit"] * 0.9 for s in stations):
        return

    station_lookup = {s["name"]: s for s in stations}
    volle_stations = [s for s in stations if s["free_bikes"] >= s["capaciteit"] * 0.9]
    lege_stations = [s for s in stations if s["free_bikes"] <= s["capaciteit"] * 0.1 and s["free_slots"] > 0]

    for vol_station in volle_stations:
        te_verplaatsen = int(vol_station["free_bikes"] * 0.3)
        if not lege_stations:
            continue

        doel_station = random.choice(lege_stations)
        beschikbare_fietsen = [f for f in fietsen if
                               f["station_naam"] == vol_station["name"] and
                               f["status"] == "beschikbaar" and
                               f["in_gebruik_tot"] is None]

        verplaatst = 0
        for fiets in beschikbare_fietsen:
            if verplaatst >= te_verplaatsen or doel_station["free_slots"] <= 0:
                break

            # Controleer capaciteit voordat je verplaatst
            if doel_station["free_bikes"] < doel_station["capaciteit"]:
                fiets["station_naam"] = doel_station["name"]
                vol_station["free_bikes"] -= 1
                vol_station["free_slots"] += 1
                doel_station["free_bikes"] += 1
                doel_station["free_slots"] -= 1
                verplaatst += 1

                # Valideer beide stations
                valideer_station_capaciteit(vol_station)
                valideer_station_capaciteit(doel_station)


# Fix voor de rit simulatie in genereer_geschiedenis
def update_station_na_rit(begin_station, eind_station):
    # Update begin station (fiets weggegaan)
    begin_station["free_bikes"] = max(0, begin_station["free_bikes"] - 1)
    begin_station["free_slots"] = min(begin_station["capaciteit"], begin_station["free_slots"] + 1)

    # Update eind station (fiets aangekomen) - alleen als er ruimte is
    if eind_station["free_bikes"] < eind_station["capaciteit"]:
        eind_station["free_bikes"] += 1
        eind_station["free_slots"] = max(0, eind_station["free_slots"] - 1)

    # Valideer beide stations
    valideer_station_capaciteit(begin_station)
    valideer_station_capaciteit(eind_station)

# Batch-update voor onderhoudsfietsen
def update_onderhoud_fietsen(fietsen, stations, beschikbare_fietsen_per_station, stations_met_fietsen):
    beschikbare_stations = [s for s in stations if s["free_slots"] > 0]
    for fiets in [f for f in fietsen if f["status"] == "onderhoud" and random.random() < 0.1]:
        if beschikbare_stations:
            # Filter stations die nog daadwerkelijk ruimte hebben
            echt_beschikbare = [s for s in beschikbare_stations if s["free_bikes"] < s["capaciteit"]]
            if not echt_beschikbare:
                continue

            nieuw_station = random.choice(echt_beschikbare)
            fiets["status"] = "beschikbaar"
            fiets["station_naam"] = nieuw_station["name"]
            nieuw_station["free_bikes"] += 1
            nieuw_station["free_slots"] = max(0, nieuw_station["free_slots"] - 1)
            fiets["in_gebruik_tot"] = None

            # Valideer station capaciteit
            valideer_station_capaciteit(nieuw_station)

            beschikbare_fietsen_per_station[nieuw_station["name"]].append(fiets)
            stations_met_fietsen.add(nieuw_station["name"])

# Gewogen starttijd met weersfactor
def gewogen_starttijd(datum):
    gewichten = []
    weersfactor = 1.0
    if random.random() < 0.3:
        weersfactor = 0.5
    for uur in range(24):
        if 8 <= uur < 18:
            gewichten += [uur] * int(5 * weersfactor)
        elif 6 <= uur < 8 or 18 <= uur < 20:
            gewichten += [uur] * int(2 * weersfactor)
        else:
            gewichten += [uur] * int(1 * weersfactor)
    if not gewichten:
        gewichten = [random.randint(0, 23)]
    gekozen_uur = random.choice(gewichten)
    gekozen_minuten = random.randint(0, 59)
    return datetime.combine(datum, datetime.min.time()) + timedelta(hours=gekozen_uur, minutes=gekozen_minuten)


# Genereer geschiedenis (gebruikersgericht)
def genereer_geschiedenis(gebruikers, fietsen, stations, dagen=28):
    geschiedenis = []
    station_lookup = {s["name"]: s for s in stations}
    vandaag = datetime.today().date()

    # Cache afstanden
    afstanden = cache_afstanden(stations)

    # Ritlimieten per abonnementstype
    rit_limieten = {
        "Dagpas": (1, 3),
        "Weekpas": (2, 4),
        "Jaarkaart": (3, 6)
    }

    # Lijst van populaire stations
    populaire_stations = ["Centraal Station", "Groenplaats", "Antwerpen-Berchem"]
    populaire_gewichten = {s["name"]: 2.0 if s["name"] in populaire_stations else 1.0 for s in stations}

    # Houd ritten per gebruiker bij
    ritten_per_gebruiker = {g["id"]: {} for g in gebruikers}

    for dag_offset in range(dagen):
        datum = vandaag - timedelta(days=(dagen - dag_offset - 1))
        herverdeel_fietsen(stations, fietsen)

        # Selecteer actieve gebruikers (15% kans, gewogen op abonnementstype)
        actieve_gebruikers = []
        for g in gebruikers:
            kans = 0.15 if g["abonnementstype"] == "Jaarkaart" else 0.10 if g["abonnementstype"] == "Weekpas" else 0.05
            if random.random() < kans:
                actieve_gebruikers.append(g)

        # Maak sets en lijsten aan het begin van de dag
        stations_met_fietsen = set(s["name"] for s in stations if s["free_bikes"] > 0)
        beschikbare_fietsen_per_station = {
            s["name"]: [f for f in fietsen if f["status"] == "beschikbaar" and f["station_naam"] == s["name"] and (
                        f["in_gebruik_tot"] is None or f["in_gebruik_tot"] <= gewogen_starttijd(datum))]
            for s in stations
        }

        # Batch-update onderhoudsfietsen
        update_onderhoud_fietsen(fietsen, stations, beschikbare_fietsen_per_station, stations_met_fietsen)

        for gebruiker in actieve_gebruikers:
            # Pre-bereken gewichten voor beginstations
            begin_gewichten = {
                s["name"]: populaire_gewichten[s["name"]] * (3.0 if s["postcode"] == gebruiker["postcode"] else 1.0)
                for s in stations if s["name"] in stations_met_fietsen
            }

            min_ritten, max_ritten = rit_limieten[gebruiker["abonnementstype"]]
            aantal_ritten = random.randint(min_ritten, max_ritten)

            for _ in range(aantal_ritten):
                if random.random() < 0.05:
                    continue

                # Selecteer beginstation
                if not stations_met_fietsen:
                    continue
                begin_station_naam = random.choices(
                    list(stations_met_fietsen),
                    weights=[begin_gewichten.get(s, 1.0) for s in stations_met_fietsen],
                    k=1
                )[0]
                begin_station = station_lookup[begin_station_naam]

                # Controleer fietsbeschikbaarheid
                beschikbare_fietsen = beschikbare_fietsen_per_station[begin_station["name"]]
                if not beschikbare_fietsen:
                    begin_station = vind_nabijgelegen_station(begin_station, stations, fietsen, afstanden)
                    if not begin_station:
                        continue
                    beschikbare_fietsen = beschikbare_fietsen_per_station[begin_station["name"]]
                    if not beschikbare_fietsen:
                        continue

                fiets = random.choice(beschikbare_fietsen)

                # Pre-bereken gewichten voor eindstations
                mogelijke_eindstations = [s for s in stations if
                                          s["name"] != begin_station["name"] and s["free_slots"] > 0]
                if not mogelijke_eindstations:
                    continue
                eind_gewichten = {
                    s["name"]: (1 / (afstanden.get((begin_station["name"], s["name"]), 1.0) + 0.1)) *
                               populaire_gewichten[s["name"]] *
                               (3.0 if s["postcode"] == gebruiker["postcode"] else 1.0)
                    for s in mogelijke_eindstations
                }

                eind_station = random.choices(
                    mogelijke_eindstations,
                    weights=[eind_gewichten[s["name"]] for s in mogelijke_eindstations],
                    k=1
                )[0]

                # Bereken ritduur
                afstand = afstanden.get((begin_station["name"], eind_station["name"]), 1.0)
                gemiddelde_snelheid = 15
                duur = max(2, int((afstand / gemiddelde_snelheid) * 60 + random.uniform(-2, 2)))

                # Voor 1% van Dagpas-gebruikers: kans op langere rit (tot 45 minuten)
                if gebruiker["abonnementstype"] == "Dagpas" and random.random() < 0.01:
                    duur = random.randint(31, 45)

                starttijd = gewogen_starttijd(datum)
                eindtijd = starttijd + timedelta(minutes=duur)

                # Vereenvoudigde overlapcontrole: controleer alleen de laatste rit
                ritten_van_dag = ritten_per_gebruiker[gebruiker["id"]].get(datum, [])
                overlap = False
                if ritten_van_dag:
                    laatste_rit = ritten_van_dag[-1]
                    overlap = laatste_rit["starttijd"] <= eindtijd and laatste_rit["eindtijd"] >= starttijd

                if overlap:
                    continue

                # Registreer de rit
                geschiedenis.append({
                    "gebruiker_id": gebruiker["id"],
                    "fiets_id": fiets["id"],
                    "begin_station_naam": begin_station["name"],
                    "eind_station_naam": eind_station["name"],
                    "starttijd": starttijd.strftime("%Y-%m-%d %H:%M:%S"),
                    "eindtijd": eindtijd.strftime("%Y-%m-%d %H:%M:%S"),
                    "duur_minuten": duur,
                })

                # Update stationstatus
                update_station_na_rit(begin_station, eind_station)

                # Update fietsstatus
                fiets["station_naam"] = eind_station["name"]
                fiets["ritten_vandaag"] += 1
                fiets["onderhoud_teller"] -= 1
                fiets["in_gebruik_tot"] = eindtijd
                if fiets["onderhoud_teller"] <= 0:
                    fiets["status"] = "onderhoud"
                    fiets["station_naam"] = None
                    fiets["onderhoud_teller"] = random.randint(10, 20)

                # Update beschikbare fietsen en stations
                beschikbare_fietsen_per_station[begin_station["name"]] = [
                    f for f in beschikbare_fietsen_per_station[begin_station["name"]]
                    if f["id"] != fiets["id"]
                ]
                beschikbare_fietsen_per_station[eind_station["name"]].append(fiets)
                if begin_station["free_bikes"] == 0:
                    stations_met_fietsen.discard(begin_station["name"])
                if eind_station["free_bikes"] > 0:
                    stations_met_fietsen.add(eind_station["name"])

                # Registreer rit voor overlapcontrole
                if datum not in ritten_per_gebruiker[gebruiker["id"]]:
                    ritten_per_gebruiker[gebruiker["id"]][datum] = []
                ritten_per_gebruiker[gebruiker["id"]][datum].append({
                    "starttijd": starttijd,
                    "eindtijd": eindtijd
                })

    return geschiedenis


def geschiedenis_to_csv_buffer(geschiedenis):
    buffer = io.StringIO()
    for rit in geschiedenis:
        buffer.write(
            f"{rit['gebruiker_id']},{rit['fiets_id']},{rit['begin_station_naam']},"
            f"{rit['eind_station_naam']},{rit['starttijd']},{rit['eindtijd']},{rit['duur_minuten']}\n"
        )
    buffer.seek(0)
    return buffer


def sla_stations_op_in_db(stations):
    session = SessionLocal()
    try:
        for s in stations:
            bestaand_station = session.get(Station, s["id"])
            if bestaand_station:
                bestaand_station.naam = s["name"]
                bestaand_station.straat = s["straat"]
                bestaand_station.latitude = s["latitude"]
                bestaand_station.longitude = s["longitude"]
                bestaand_station.capaciteit = s["capaciteit"]
                bestaand_station.status = s["status"]
                bestaand_station.free_slots = s["free_slots"]
                bestaand_station.parked_bikes = s["free_bikes"]
            else:
                nieuw_station = Station(
                    id=s["id"],
                    naam=s["name"],
                    straat=s["straat"],
                    latitude=s["latitude"],
                    longitude=s["longitude"],
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


def sla_fietsen_op_in_db(fietsen):
    session = SessionLocal()
    try:
        for f in fietsen:
            fiets = Fiets(
                id=f["id"],
                station_naam=f["station_naam"],
                status=f["status"]
            )
            session.merge(fiets)
        session.commit()
        print(f"{len(fietsen)} fietsen opgeslagen in de database.")
    except Exception as e:
        session.rollback()
        print("❌ Fout bij opslaan fietsen:", e)
    finally:
        session.close()


def sla_gebruikers_op_in_db(gebruikers):
    session = SessionLocal()
    try:
        for g in gebruikers:
            gebruiker = Gebruiker(
                id=g["id"],
                voornaam=g["voornaam"],
                achternaam=g["achternaam"],
                email=g["email"],
                postcode=g["postcode"],
                abonnementstype=g["abonnementstype"],
            )
            session.merge(gebruiker)
        session.commit()
        print(f"{len(gebruikers)} gebruikers opgeslagen in de database.")
    except Exception as e:
        session.rollback()
        print("❌ Fout bij opslaan gebruikers:", e)
    finally:
        session.close()


def sla_geschiedenis_op_in_db(geschiedenis):
    session = SessionLocal()
    try:
        for g in geschiedenis:
            geschieden = Geschiedenis(
                gebruiker_id=g["gebruiker_id"],
                fiets_id=g["fiets_id"],
                start_station_naam=g["begin_station_naam"],
                eind_station_naam=g["eind_station_naam"],
                starttijd=g["starttijd"],
                eindtijd=g["eindtijd"],
                duur_minuten=g["duur_minuten"],
            )
            session.merge(geschieden)
        session.commit()
        print(f"{len(geschiedenis)} geschiedenis opgeslagen in de database.")
    except Exception as e:
        session.rollback()
        print("❌ Fout bij opslaan geschiedenis:", e)
    finally:
        session.close()

#
# if __name__ == "__main__":
#     gebruikers = genereer_gebruikers(5000)
#     fietsen = genereer_fietsen(5800, stations)
#     geschiedenis = genereer_geschiedenis(gebruikers, fietsen, stations)
#     sla_stations_op_in_db(stations)
#     sla_fietsen_op_in_db(fietsen)
#     sla_gebruikers_op_in_db(gebruikers)
#     sla_geschiedenis_op_in_db(geschiedenis)
#
#     buffer = geschiedenis_to_csv_buffer(geschiedenis)
#     with open("simulatie_output.csv", "w") as f:
#         f.write(buffer.getvalue())