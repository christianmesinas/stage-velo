from flask import Blueprint, send_file, session, redirect, url_for, request, render_template
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv, find_dotenv
from urllib.parse import quote_plus, urlencode
from os import environ as env
import requests
import csv
import uuid
import os

from app.api import api as api
from app.database.models import Usertable
from app.database import SessionLocal
from app.simulation import simulation


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




@routes.route("/admin", methods=["GET", "POST"])
def admin():
    boodschap = None
    ritten = []
    csv_bestand = None

    if request.method == "POST":
        try:
            gebruikers_aantal = int(request.form.get("gebruikers"))
            fietsen_aantal = int(request.form.get("fietsen"))
            dagen = int(request.form.get("dagen"))
            gebruikers = simulation.genereer_gebruikers(gebruikers_aantal)
            fietsen = simulation.genereer_fietsen(fietsen_aantal, simulation.stations)
            ritten = simulation.simulatie(simulation.stations, gebruikers, fietsen, dagen)

            # Maak een unieke bestandsnaam
            csv_bestand = f"/tmp/ritten_{uuid.uuid4().hex}.csv"
            with open(csv_bestand, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["gebruiker_id", "fiets_id", "begin_station_id", "eind_station_id", "duur_minuten"])
                for rit in ritten:
                    writer.writerow([
                        rit.gebruiker_id,
                        rit.fiets_id,
                        rit.begin_station_id,
                        rit.eind_station_id,
                        rit.duur_minuten
                    ])

            boodschap = f"✅ Simulatie is gestart met {len(ritten)} ritten."

        except Exception as e:
            boodschap = f"❌ Fout bij simulatie: {str(e)}"

    return render_template("admin.html", boodschap=boodschap, ritten=ritten, csv_bestand=csv_bestand)


