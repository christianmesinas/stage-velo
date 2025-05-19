from datetime import datetime
import pytz



from flask import Blueprint, send_file, session, redirect, url_for, request, render_template
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv, find_dotenv
from urllib.parse import quote_plus, urlencode
from os import environ as env
import requests
import csv
import uuid
import os
import copy

from app.api import api as api
from app.api.api import get_alle_stations, get_info
from app.database.models import Usertable
from app.database import SessionLocal
from app.simulation import simulation
from collections import Counter
from functools import wraps


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get("user")
        if not user:
            return redirect(url_for("routes.login"))  # of index als je geen aparte loginpagina hebt
        if user.get("email") != os.getenv("ADMIN_EMAIL"):
            return "❌ Geen toegang: je bent geen administrator", 403
        return f(*args, **kwargs)
    return decorated_function






routes = Blueprint("routes", __name__)

# ======================
# .env en Auth0 configuratie
# ======================

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

oauth = OAuth()
oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
        "audience": f"https://{env.get('AUTH0_DOMAIN')}/api/v2/"
    },
    server_metadata_url=f"https://{env.get('AUTH0_DOMAIN')}/.well-known/openid-configuration"
)

# ======================
# AUTH ROUTES
# ======================

@routes.route("/auth/process", methods=["POST"])
def process_auth():
    token = request.json.get("access_token")
    if not token:
        return {"error": "Access token ontbreekt"}, 400

    headers = {'Authorization': f'Bearer {token}'}
    try:
        user_info = requests.get(
            f'https://{env.get("AUTH0_DOMAIN")}/userinfo',
            headers=headers
        ).json()
    except Exception as e:
        return {"error": f"Fout bij ophalen userinfo: {str(e)}"}, 500

    user_id = user_info.get("sub")
    email = user_info.get("email")
    name = user_info.get("name", "")
    profile_picture = user_info.get("picture", "img/default.png")

    session["user"] = {
        "id": user_id,
        "email": email,
        "name": name
    }

    db = SessionLocal()
    Usertable.get_or_create(
        db=db,
        user_id=user_id,
        email=email,
        name=name,
        profile_picture=profile_picture
    )
    db.close()

    return "", 200

@routes.route("/logout")
def logout():
    session.clear()
    return redirect(
        f'https://{env.get("AUTH0_DOMAIN")}/v2/logout?' + urlencode({
            "returnTo": url_for("routes.index", _external=True),
            "client_id": env.get("AUTH0_CLIENT_ID"),
        }, quote_plus)
    )

# ======================
# ALGEMENE ROUTES
# ======================

@routes.route("/")
def index():
    return render_template("index.html",
                           auth0_client_id=env.get("AUTH0_CLIENT_ID"),
                           auth0_domain=env.get("AUTH0_DOMAIN"))

@routes.route("/login")
def login():
    return render_template("login.html",
                           auth0_client_id=env.get("AUTH0_CLIENT_ID"),
                           auth0_domain=env.get("AUTH0_DOMAIN"))

@routes.route("/profile")
def profile():
    if 'user' not in session:
        return redirect(url_for("routes.login"))
    return render_template("profile.html")

@routes.route("/help")
def help():
    return render_template("help.html")



@routes.route("/maps")
def markers():
    markers = []
    for location in api.get_alle_stations():
        markers.append({
            'lat': location[4],
            'lon': location[5],
            'name': location[1],
            'free-bikes': location[6],
            'empty-slots': location[7],
            'status': location[3],
        })
    return render_template("maps.html", markers=markers)

@routes.route("/tarieven")
def tarieven():
    return render_template("tarieven.html")

@routes.route("/tarieven/dagpas", methods=["GET", "POST"])
def dagpass():
    if request.method == "POST":
        pincode = request.form.get("pincode")
        bevestig_pincode = request.form.get("bevestig_pincode")

        if pincode != bevestig_pincode:
            foutmelding = "De pincodes komen niet overeen!"
            return render_template(
                "tarieven/dagpas.html",
                foutmelding=foutmelding,
                formdata=request.form
            )

        data = {
            "voornaam": request.form.get("voornaam"),
            "achternaam": request.form.get("achternaam"),
            "email": request.form.get("email"),
            "telefoon": request.form.get("telefoon"),
            "geboortedatum": request.form.get("geboortedatum"),
            "pincode": pincode
        }
        return render_template("tarieven/bedankt.html", data=data)

    return render_template("tarieven/dagpas.html", formdata={})

@routes.route("/tarieven/weekpas", methods=["GET", "POST"])
def weekpass():
    if request.method == "POST":
        pincode = request.form.get("pincode")
        bevestig_pincode = request.form.get("bevestig_pincode")

        if pincode != bevestig_pincode:
            foutmelding = "De pincodes komen niet overeen!"
            return render_template(
                "tarieven/weekpas.html",
                foutmelding=foutmelding,
                formdata=request.form
            )

        data = {
            "voornaam": request.form.get("voornaam"),
            "achternaam": request.form.get("achternaam"),
            "email": request.form.get("email"),
            "telefoon": request.form.get("telefoon"),
            "geboortedatum": request.form.get("geboortedatum"),
            "pincode": pincode
        }
        return render_template("tarieven/bedankt.html", data=data)

    return render_template("tarieven/weekpas.html", formdata={})

@routes.route("/tarieven/jaarkaart", methods=["GET", "POST"])
def jaarkaart():
    if request.method == "POST":
        pincode = request.form.get("pincode")
        bevestig_pincode = request.form.get("bevestig_pincode")

        if pincode != bevestig_pincode:
            foutmelding = "De pincodes komen niet overeen!"
            return render_template(
                "tarieven/jaarkaart.html",
                foutmelding=foutmelding,
                formdata=request.form
            )

        data = {
            "voornaam": request.form.get("voornaam"),
            "achternaam": request.form.get("achternaam"),
            "email": request.form.get("email"),
            "telefoon": request.form.get("telefoon"),
            "geboortedatum": request.form.get("geboortedatum"),
            "pincode": pincode
        }
        return render_template("tarieven/bedankt.html", data=data)

    return render_template("tarieven/jaarkaart.html", formdata={})

@routes.route("/defect")
def defect():
    if 'user' not in session:
        return redirect(url_for("routes.login"))
    return render_template("defect.html")

@routes.app_errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@routes.app_errorhandler(500)
def internal_server_error(error):
    return render_template('500.html'), 500



# ======================
# ADMIN ROUTE
# ======================



@routes.route("/admin")
@admin_required
def admin():
    laatste_simulatie = session.get("laatste_simulatie")
    return render_template("admin.html", laatste_simulatie=laatste_simulatie)









@routes.route("/admin/simulatie", methods=["GET", "POST"])
@admin_required
def admin_simulatie():
    boodschap = None
    ritten = []
    csv_bestand = None

    aantal_ritten = 0
    gemiddelde_duur = 0
    langste_rit = 0
    meest_gebruikte_fiets = 0
    populairst_station = 0
    drukste_per_station = []

    stations_copy = None

    if request.method == "POST":
        try:
            gebruikers_aantal = int(request.form.get("gebruikers"))
            fietsen_aantal = int(request.form.get("fietsen"))
            dagen = int(request.form.get("dagen"))

            gebruikers = simulation.genereer_gebruikers(gebruikers_aantal)
            stations_copy = copy.deepcopy(simulation.stations)
            fietsen = simulation.genereer_fietsen(fietsen_aantal, stations_copy)
            ritten = simulation.simulatie(stations_copy, gebruikers, fietsen, dagen)

            # 📊 Inzichten
            aantal_ritten = len(ritten)
            gemiddelde_duur = round(sum(r["duur_minuten"] for r in ritten) / aantal_ritten, 2) if aantal_ritten > 0 else 0
            langste_rit = max((r["duur_minuten"] for r in ritten), default=0)

            fiets_teller = Counter(r["fiets_id"] for r in ritten)
            meest_gebruikte_fiets = fiets_teller.most_common(1)[0][0] if fiets_teller else None

            station_teller = Counter(r["begin_station_id"] for r in ritten)
            populairst_station = station_teller.most_common(1)[0][0] if station_teller else None

            # ⏰ Drukste momenten per station
            station_uren_counter = {}
            for rit in ritten:
                station_id = rit["begin_station_id"]
                starttijd = rit["starttijd"]
                if isinstance(starttijd, str):
                    startuur = datetime.strptime(starttijd, "%Y-%m-%d %H:%M:%S").hour
                else:
                    startuur = starttijd.hour
                station_uren_counter.setdefault(station_id, Counter())[startuur] += 1

            for station in stations_copy:
                sid = station["id"]
                naam = station["name"]
                if sid in station_uren_counter:
                    meest_uur, aantal = station_uren_counter[sid].most_common(1)[0]
                    tijdvak = f"{meest_uur:02d}:00 - {meest_uur:02d}:59"
                    drukste_per_station.append({
                        "naam": naam,
                        "tijdvak": tijdvak,
                        "aantal": aantal
                    })

            drukste_per_station.sort(key=lambda x: x["aantal"], reverse=True)

            # 📥 CSV export
            csv_bestand = f"/tmp/ritten_{uuid.uuid4().hex}.csv"
            with open(csv_bestand, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["gebruiker_id", "fiets_id", "begin_station_id", "eind_station_id", "duur_minuten"])
                for rit in ritten:
                    writer.writerow([
                        rit["gebruiker_id"],
                        rit["fiets_id"],
                        rit["begin_station_id"],
                        rit["eind_station_id"],
                        rit["duur_minuten"]
                    ])

            # ✅ Tijd in Belgische tijdzone
            brussel_tijd = datetime.now(pytz.timezone("Europe/Brussels"))
            session["laatste_simulatie"] = brussel_tijd.strftime("%d-%m-%Y om %H:%M")
            session.modified = True

            boodschap = f"✅ Simulatie is gestart met {len(ritten)} ritten."

        except Exception as e:
            boodschap = f"❌ Fout bij simulatie: {str(e)}"

    # 📍 Stationstatus
    stations_overzicht = []
    bron_stations = stations_copy if request.method == "POST" else simulation.stations
    for s in bron_stations:
        stations_overzicht.append({
            "naam": s["name"],
            "fietsen": s["free_bikes"],
            "vrij": s["free_slots"]
        })

    return render_template(
        "admin_simulatie.html",
        boodschap=boodschap,
        ritten=ritten,
        csv_bestand=csv_bestand,
        stations_overzicht=stations_overzicht,
        aantal_ritten=aantal_ritten,
        gemiddelde_duur=gemiddelde_duur,
        langste_rit=langste_rit,
        meest_gebruikte_fiets=meest_gebruikte_fiets,
        populairst_station=populairst_station,
        drukste_per_station=drukste_per_station,
    )





@routes.route("/admin/data")
@admin_required


def admin_data():
    stations = get_alle_stations()
    info = get_info()

    # voorbeeld: update tijd registreren
    session["live_data_update"] = datetime.now().strftime("%H:%M:%S")

    populairste_station = {
        "naam": "Station Zuid",
        "ritten": 23
    }

    return render_template("live_data.html", stations=stations, populairste_station=populairste_station)




@routes.route("/admin/gebruikers")
@admin_required


def admin_gebruikers():
    gebruikers = simulation.gebruikers_lijst()  # voorbeeld
    return render_template("admin/gebruikers.html", gebruikers=gebruikers)
