from flask import Blueprint, render_template, session, redirect, url_for, request
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv, find_dotenv
from urllib.parse import quote_plus, urlencode
from os import environ as env
import requests
import os
import logging

from app.api import api as api
from app.database.models import Usertable
from app.database import SessionLocal
#vertalingen
from flask_babel import _, lazy_gettext, get_locale

routes = Blueprint("routes", __name__)

# Stel logging in
logging.basicConfig(level=logging.DEBUG)

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

    return redirect(redirect_to)

@routes.route("/logout")
def logout():
    current_language = get_locale()  # Sla de huidige taal op
    logging.debug(f"Logging out, preserving language: {current_language}")
    session.clear()
    return redirect(
        f'https://{env.get("AUTH0_DOMAIN")}/v2/logout?' + urlencode({
            "returnTo": url_for("routes.index", _external=True, lang=current_language),
            "client_id": env.get("AUTH0_CLIENT_ID"),
        }, quote_plus)
    )

# ======================
# ALGEMENE ROUTES
# ======================

@routes.route("/")
def index():
    language = get_locale()  # Haal de huidige taal op
    logging.debug(f"Rendering index.html with language: {language}")
    return render_template("index.html",
                           auth0_client_id=env.get("AUTH0_CLIENT_ID"),
                           auth0_domain=env.get("AUTH0_DOMAIN"),
                           language=language)

@routes.route("/login")
def login():
    next_url = request.args.get("next", "/profile")
    language = get_locale()  # Haal de huidige taal op
    logging.debug(f"Rendering login.html with language: {language}")
    return render_template("login.html",
                           auth0_client_id=env.get("AUTH0_CLIENT_ID"),
                           auth0_domain=env.get("AUTH0_DOMAIN"),
                           next_url=next_url,
                           language=language)

@routes.route("/profile")
def profile():
    if 'user' not in session:
        return redirect(url_for("routes.login", next=request.path, lang=get_locale()))
    language = get_locale()  # Haal de huidige taal op
    logging.debug(f"Rendering profile.html with language: {language}")
    return render_template("profile.html", language=language)

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
    language = get_locale()  # Haal de huidige taal op
    logging.debug(f"Rendering maps.html with language: {language}")
    return render_template("maps.html", markers=markers, language=language)

@routes.route("/tarieven")
def tarieven():
    language = get_locale()  # Haal de huidige taal op
    logging.debug(f"Rendering tarieven.html with language: {language}")
    return render_template("tarieven.html", language=language)

@routes.route("/tarieven/dagpas", methods=["GET", "POST"])
def dagpass():
    language = get_locale()  # Haal de huidige taal op
    logging.debug(f"Rendering tarieven/dagpas.html with language: {language}")
    if request.method == "POST":
        pincode = request.form.get("pincode")
        bevestig_pincode = request.form.get("bevestig_pincode")

        if pincode != bevestig_pincode:
            foutmelding = _("De pincodes komen niet overeen!")
            return render_template(
                "tarieven/dagpas.html",
                foutmelding=foutmelding,
                formdata=request.form,
                language=language
            )

        data = {
            "voornaam": request.form.get("voornaam"),
            "achternaam": request.form.get("achternaam"),
            "email": request.form.get("email"),
            "telefoon": request.form.get("telefoon"),
            "geboortedatum": request.form.get("geboortedatum"),
            "pincode": pincode
        }
        return render_template("tarieven/bedankt.html", data=data, language=language)

    return render_template("tarieven/dagpas.html", formdata={}, language=language)

@routes.route("/tarieven/weekpas", methods=["GET", "POST"])
def weekpass():
    language = get_locale()  # Haal de huidige taal op
    logging.debug(f"Rendering tarieven/weekpas.html with language: {language}")
    if request.method == "POST":
        pincode = request.form.get("pincode")
        bevestig_pincode = request.form.get("bevestig_pincode")

        if pincode != bevestig_pincode:
            foutmelding = _("De pincodes komen niet overeen!")
            return render_template(
                "tarieven/weekpas.html",
                foutmelding=foutmelding,
                formdata=request.form,
                language=language
            )

        data = {
            "voornaam": request.form.get("voornaam"),
            "achternaam": request.form.get("achternaam"),
            "email": request.form.get("email"),
            "telefoon": request.form.get("telefoon"),
            "geboortedatum": request.form.get("geboortedatum"),
            "pincode": pincode
        }
        return render_template("tarieven/bedankt.html", data=data, language=language)

    return render_template("tarieven/weekpas.html", formdata={}, language=language)

@routes.route("/tarieven/jaarkaart", methods=["GET", "POST"])
def jaarkaart():
    language = get_locale()  # Haal de huidige taal op
    logging.debug(f"Rendering tarieven/jaarkaart.html with language: {language}")
    if request.method == "POST":
        pincode = request.form.get("pincode")
        bevestig_pincode = request.form.get("bevestig_pincode")

        if pincode != bevestig_pincode:
            foutmelding = _("De pincodes komen niet overeen!")
            return render_template(
                "tarieven/jaarkaart.html",
                foutmelding=foutmelding,
                formdata=request.form,
                language=language
            )

        data = {
            "voornaam": request.form.get("voornaam"),
            "achternaam": request.form.get("achternaam"),
            "email": request.form.get("email"),
            "telefoon": request.form.get("telefoon"),
            "geboortedatum": request.form.get("geboortedatum"),
            "pincode": pincode
        }
        return render_template("tarieven/bedankt.html", data=data, language=language)

    return render_template("tarieven/jaarkaart.html", formdata={}, language=language)

@routes.route("/defect")
def defect():
    if 'user' not in session:
        return redirect(url_for("routes.login", next=request.path, lang=get_locale()))
    language = get_locale()  # Haal de huidige taal op
    logging.debug(f"Rendering defect.html with language: {language}")
    return render_template("defect.html", language=language)

@routes.app_errorhandler(404)
def page_not_found(error):
    language = get_locale()  # Haal de huidige taal op
    logging.debug(f"Rendering 404.html with language: {language}")
    return render_template('404.html', language=language), 404

@routes.app_errorhandler(500)
def internal_server_error(error):
    language = get_locale()  # Haal de huidige taal op
    logging.debug(f"Rendering 500.html with language: {language}")
    return render_template('500.html', language=language), 500