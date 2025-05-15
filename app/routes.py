from flask import Blueprint, render_template, session, redirect, url_for, request
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv, find_dotenv
from api.api import get_info
from urllib.parse import quote_plus, urlencode
from os import environ as env
import requests
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
    stations = get_info()
    markers = []
    for station in stations:
        markers.append({
            'lat': station['location']['latitude'],
            'lon': station['location']['longitude'],
            'name': station['name'],
            'free-bikes': station['free_bikes'],
            'empty-slots': station['empty_slots'],
            'status': station['extra']['status'],
        })
    return render_template("maps.html", markers=markers)

#def simulatie_button():
    #if is_admin = True:
        # geef button for simulatie te genereren in maps

@routes.route("/tarieven")
def tarieven():
    return render_template("tarieven.html")

@routes.route("/tarieven/dagpas", methods=["GET", "POST"])
def dagpas():
    if request.method == "POST":
        pincode = request.form.get("pincode")
        bevestig_pincode = request.form.get("bevestig_pincode")

        if pincode != bevestig_pincode:
            foutmelding = "De pincodes komen niet overeen."
            return render_template("tarieven/dagpas.html", foutmelding=foutmelding)

        data = {
            "voornaam": request.form.get("voornaam"),
            "achternaam": request.form.get("achternaam"),
            "email": request.form.get("email"),
            "telefoon": request.form.get("telefoon"),
            "geboortedatum": request.form.get("geboortedatum"),
            "pincode": pincode
        }
        return render_template("tarieven/bedankt.html", data=data)

    return render_template("tarieven/dagpas.html")

@routes.route("/tarieven/weekpas", methods=["GET", "POST"])
def weekpass():
    if request.method == "POST":
        pincode = request.form.get("pincode")
        bevestig_pincode = request.form.get("bevestig_pincode")

        if pincode != bevestig_pincode:
            foutmelding = "De pincodes komen niet overeen."
            return render_template("tarieven/weekpas.html", foutmelding=foutmelding)

        data = {
            "voornaam": request.form.get("voornaam"),
            "achternaam": request.form.get("achternaam"),
            "email": request.form.get("email"),
            "telefoon": request.form.get("telefoon"),
            "geboortedatum": request.form.get("geboortedatum"),
            "pincode": pincode
        }
        return render_template("tarieven/bedankt.html", data=data)

    return render_template("tarieven/weekpas.html")

@routes.route("/tarieven/jaarkaart", methods=["GET", "POST"])
def jaarkaart():
    if request.method == "POST":
        if not request.form.get("voorwaarden"):
            foutmelding = "Je moet akkoord gaan met de algemene voorwaarden."
            return render_template("tarieven/jaarkaart.html", foutmelding=foutmelding)

        data = {
            "voornaam": request.form.get("voornaam"),
            "achternaam": request.form.get("achternaam"),
            "email": request.form.get("email"),
            "telefoon": request.form.get("telefoon"),
            "geboortedatum": request.form.get("geboortedatum"),
            "postcode": request.form.get("postcode"),
            "gemeente": request.form.get("gemeente"),
            "betaalmethode": request.form.get("betaalmethode"),
            "ontleenmodus": "velo_app"
        }
        return render_template("tarieven/bedankt.html", data=data)

    return render_template("tarieven/jaarkaart.html")




# ======================
# ADMIN ROUTE
# ======================



@routes.route("/admin", methods=["GET", "POST"])
def admin():
    boodschap = None
    ritten = []

    if request.method == "POST":
        try:
            gebruikers_aantal = int(request.form.get("gebruikers"))
            fietsen_aantal = int(request.form.get("fietsen"))
            dagen = int(request.form.get("dagen"))
            gebruikers = simulation.genereer_gebruikers(gebruikers_aantal)
            fietsen = simulation.genereer_fietsen(fietsen_aantal, simulation.stations)
            ritten = simulation.simulatie(simulation.stations, gebruikers, fietsen, dagen)

            boodschap = f"✅ Simulatie is gestart met {len(ritten)} ritten."

        except Exception as e:
            boodschap = f"❌ Fout bij simulatie: {str(e)}"

    return render_template("admin.html", boodschap=boodschap, ritten=ritten)



