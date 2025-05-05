from flask import Blueprint, render_template, session, redirect, url_for, request
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv, find_dotenv
from urllib.parse import quote_plus, urlencode
from os import environ as env
import requests
import os
from app.api import api as api

from app.database.models import Usertable
from app.database import SessionLocal

routes = Blueprint("routes", __name__)

# Laad .ENV
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

# Auth0 setup
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

@routes.route("/")
def index():
    return render_template("index.html",
                           auth0_client_id=env.get("AUTH0_CLIENT_ID"),
                           auth0_domain=env.get("AUTH0_DOMAIN"),
                           user=session.get("user"))

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

@routes.route("/profile")
def profile():
    if 'user' not in session:
        return redirect(url_for("routes.login"))
    return render_template("profile.html", user=session.get("user"))

@routes.route("/login")
def login():
    return render_template("login.html",
                           auth0_client_id=env.get("AUTH0_CLIENT_ID"),
                           auth0_domain=env.get("AUTH0_DOMAIN"))

@routes.route("/maps")
def markers():
    markers = []
    for location in api.get_alle_stations():
        markers.append({
                'lat':  location[4],
                'lon':  location[5],
                'name': location[1],
                'free-bikes': location[6],
                'empty-slots': location[7],
                'status': location[2],
        })
    return render_template('maps.html', markers=markers)

