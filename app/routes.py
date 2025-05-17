from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv, find_dotenv
from urllib.parse import quote_plus, urlencode
from os import environ as env
import requests
import os

from app.api import api as api
from app.database.models import Usertable, Gebruiker
from app.database import SessionLocal

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
    redirect_to = request.json.get("redirect_to", "/profile")

    if not token:
        return {"error": "Access token ontbreekt"}, 400

    headers = {'Authorization': f'Bearer {token}'}
    try:
        user_info = requests.get(
            f'https://{env.get("AUTH0_DOMAIN")}/userinfo', headers=headers
        ).json()
    except Exception as e:
        return {"error": f"Fout bij ophalen userinfo: {str(e)}"}, 500

    user_id = user_info.get("sub")
    email = user_info.get("email")
    name = user_info.get("name", "")
    profile_picture = user_info.get("picture", "img/default.png")

    session["Gebruiker"] = {
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

    return redirect(redirect_to)

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
    next_url = request.args.get("next", "/profile")
    return render_template("login.html",
                           auth0_client_id=env.get("AUTH0_CLIENT_ID"),
                           auth0_domain=env.get("AUTH0_DOMAIN"),
                           next_url=next_url)

@routes.route("/profile")
def profile():
    if 'Gebruiker' not in session:
        return redirect(url_for("routes.login", next=request.path))

    db = SessionLocal()
    user_table = db.query(Usertable).filter_by(user_id=session["Gebruiker"]["id"]).first()
    user_data = db.query(Gebruiker).filter_by(email=session["Gebruiker"]["email"]).first()
    db.close()

    return render_template("profile.html", user=user_table, user_data=user_data)

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
def dagpas():
    if request.method == "POST":
        pincode = request.form.get("pincode")
        bevestig_pincode = request.form.get("bevestig_pincode")

        if pincode != bevestig_pincode:
            foutmelding = "De pincodes komen niet overeen!"
            return render_template("tarieven/dagpas.html", foutmelding=foutmelding, formdata=request.form)

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
            return render_template("tarieven/weekpas.html", foutmelding=foutmelding, formdata=request.form)

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
            return render_template("tarieven/jaarkaart.html", foutmelding=foutmelding, formdata=request.form)

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
    if 'Gebruiker' not in session:
        return redirect(url_for("routes.login", next=request.path))
    return render_template("defect.html")

@routes.route("/instellingen", methods=["GET", "POST"])
def instellingen():
    if "Gebruiker" not in session or "id" not in session["Gebruiker"]:
        return redirect(url_for("routes.login"))

    db = SessionLocal()
    gebruiker = db.query(Usertable).filter_by(user_id=session["Gebruiker"]["id"]).first()

    if request.method == "POST":
        nieuwe_naam = request.form.get("naam")
        voornaam = request.form.get("voornaam")
        achternaam = request.form.get("achternaam")
        telefoonnummer = request.form.get("telefoonnummer")
        titel = request.form.get("titel")
        nieuwe_email = request.form.get("email")
        taal = request.form.get("taal")

        file = request.files.get("profile_picture")
        filename = None

        if file and file.filename:
            filename = secure_filename(file.filename)
            upload_path = os.path.join("app", "static", "uploads", filename)
            file.save(upload_path)

        if gebruiker:
            gebruiker.voornaam = voornaam
            gebruiker.achternaam = achternaam
            gebruiker.telefoonnummer = telefoonnummer
            gebruiker.titel = titel
            gebruiker.naam = nieuwe_naam
            gebruiker.email = nieuwe_email
            gebruiker.taal = taal
            if filename:
                gebruiker.profile_picture = filename
            db.commit()

            # обновляем сессию - updaten de session
            session["Gebruiker"]["naam"] = nieuwe_naam
            session["Gebruiker"]["email"] = nieuwe_email
            session["Gebruiker"]["taal"] = taal

        flash("Instellingen succesvol opgeslagen.", "success")
        db.close()
        return redirect(url_for("routes.profile"))

    # GET-запрос — возвращаем объект из базы - Get - krijg de gegevens van DB
    db.close()
    return render_template("instellingen.html", user=gebruiker)

@routes.route("/delete_account", methods=["POST"])
def delete_account():
    if "Gebruiker" not in session:
        return redirect(url_for("routes.login"))

    db = SessionLocal()
    gebruiker = db.query(Usertable).filter_by(user_id=session["Gebruiker"]["id"]).first()
    if gebruiker:
        db.delete(gebruiker)
        db.commit()
    db.close()
    session.clear()
    flash("Uw account is verwijderd.", "danger")
    return redirect(url_for("routes.index"))

@routes.app_errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@routes.app_errorhandler(500)
def internal_server_error(error):
    return render_template('500.html'), 500
