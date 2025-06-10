from datetime import datetime
import stripe
from flask import jsonify
import psycopg2
import pytz
from app.database.models import Usertable, Gebruiker, Station
from flask import Blueprint, send_file, session, redirect, url_for, request, render_template,flash
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv, find_dotenv
from urllib.parse import quote_plus, urlencode
from os import environ as env
import requests
import re
import csv
import uuid
import os
import copy
from app.api import api as api
from app.api.api import get_alle_stations, get_info
from app.database.models import Usertable, Defect, Fiets, Geschiedenis
from app.database.models import ContactBericht
from app.database import SessionLocal
from app.simulation import simulation
from collections import Counter
from functools import wraps
from werkzeug.utils import secure_filename
from app.utils.email import send_abonnement_email
from flask import request, render_template, session
import copy
import csv
import uuid
from datetime import datetime
import pytz
from collections import Counter


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        gebruiker = session.get("Gebruiker") #eerst checken of er is ingelogd
        if not gebruiker:
            return redirect(url_for("routes.login", next=request.path))
        if gebruiker.get("email") != os.getenv("ADMIN_EMAIL"): #hierna checken we of de user email overeenkomt met admin_email
            return "❌ Geen toegang: je bent geen administrator", 403
        return f(*args, **kwargs)
    return decorated_function


def transport_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        gebruiker = session.get("Gebruiker")
        if not gebruiker:
            return redirect(url_for("routes.login", next=request.path))
        if gebruiker.get("email") not in [os.getenv("ADMIN_EMAIL"), os.getenv("TRANSPORT_EMAIL")]:
            return "❌ Geen toegang: je bent geen transporteur", 403
        return f(*args, **kwargs)
    return decorated_function



# ✅ Создание Blueprint / Maak een Blueprint
routes = Blueprint("routes", __name__)
# ======================
# .env en Auth0 configuratie
# ======================
ENV_FILE = find_dotenv()  # Найти .env / Zoek .env-bestand
if ENV_FILE:
    load_dotenv(ENV_FILE)  # Загрузить .env / Laad de variabelen uit het bestand

oauth = OAuth()  # Инициализация OAuth / Initialiseer OAuth
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
# ✅ Обработка авторизации / AUTHENTICATIE
# ======================
@routes.route("/auth/process", methods=["POST"])
def process_auth():
    '''token = request.json.get("access_token")
    if not token:
        return {"error": "Access token ontbreekt"}, 400'''

    token = request.json.get("access_token")
    redirect_to = request.json.get("redirect_to")

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
    session.permanent = True

    db = SessionLocal()
    Usertable.get_or_create(
        db=db,
        user_id=user_id,
        email=email,
        name=name,
        profile_picture=profile_picture
    )  # Создание или обновление пользователя / Maak of update gebruiker
    db.close()

    # ✅ Automatische redirect op basis van rol/e-mail
    if email == os.getenv("ADMIN_EMAIL"):
        return redirect(url_for("routes.admin"))
    elif email == os.getenv("TRANSPORT_EMAIL"):
        return redirect(url_for("routes.transport_dashboard"))
    else:
        return redirect(redirect_to or url_for("routes.profile"))


# ✅ Выход / Afmelden
@routes.route("/logout")
def logout():
    session.clear()  # Очистить сессию / Leeg de sessie
    return redirect(
        f'https://{env.get("AUTH0_DOMAIN")}/v2/logout?' + urlencode({
            "returnTo": url_for("routes.index", _external=True),
            "client_id": env.get("AUTH0_CLIENT_ID"),
        }, quote_plus)
    )


# ======================
# ✅ Общие маршруты / Algemene routes
# ======================
@routes.route("/")
def index():
    return render_template("index.html",
                           auth0_client_id=env.get("AUTH0_CLIENT_ID"),
                           auth0_domain=env.get("AUTH0_DOMAIN"))


@routes.route("/contact/bevestiging")
def contact_bevestiging():
    return render_template("contact_bevestiging.html",)

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
    gebruiker_id = session["Gebruiker"]["id"]

    # Haal de gebruiker uit beide tabellen op
    user_table = db.query(Usertable).filter_by(user_id=gebruiker_id).first()
    user_data = db.query(Gebruiker).filter_by(email=session["Gebruiker"]["email"]).first()

    # Haal de fietsritten (geschiedenis) op als de gebruiker bestaat
    rentals = []
    if user_data:
        rentals = db.query(Geschiedenis).filter_by(gebruiker_id=user_data.id).all()

    db.close()

    return render_template(
        "profile.html",
        user=user_table,
        user_data=user_data,
        rentals=rentals  # hier geef je de geschiedenis door
    )

@routes.route("/help")
def help():
    return render_template("help.html")


@routes.route("/maps")
def markers():
    import psycopg2
    conn = psycopg2.connect( #connecteren met de database voor de stations data
        dbname="velo_community",
        user=env.get("POSTGRES_USER"),
        password=env.get("POSTGRES_PASSWORD"),
        host="host.docker.internal",
        port="5433"
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM stations")
    stations = cur.fetchall()
    markers = []
    for station in stations: #filteren van de data met een loop
        markers.append({
            'lat': float(station[3]),
            'lon': float(station[4]),
            'name': station[1],
            'free-bikes': station[8],
            'empty-slots': station[7],
            'status': station[6],
        })
    cur.close()
    conn.close()
    return render_template("maps.html", markers=markers)


@routes.route("/tarieven")
def tarieven():
    if "Gebruiker" in session and "id" in session["Gebruiker"]:
        db = SessionLocal()
        try:
            gebruiker = db.query(Usertable).filter_by(user_id=session["Gebruiker"]["id"]).first()
            if gebruiker:
                # updaten van sessie met de juiste abonnement van de gebruiker
                session["Gebruiker"]["abonnement"] = gebruiker.abonnement
                session.modified = True  # opslaan van sessie
            else:
                # als gebruiker niet bestaat de sessie leegmaken
                session.pop("Gebruiker", None)
        finally:
            db.close()
    return render_template("tarieven.html")


@routes.route("/tarieven/dagpas", methods=["GET", "POST"])
def dagpas():
    # Controleer of gebruiker is ingelogd
    if "Gebruiker" not in session:
        return redirect(url_for("routes.login", next="/tarieven/dagpas"))

    db = SessionLocal()
    gebruiker = db.query(Usertable).filter_by(user_id=session["Gebruiker"]["id"]).first()

    if request.method == "POST":
        if gebruiker and gebruiker.abonnement != "Geen abonnement":
            foutmelding = f"Je hebt al een {gebruiker.abonnement.lower()}."
            db.close()
            return render_template("tarieven/dagpas.html", foutmelding=foutmelding, formdata=request.form)

        pincode = request.form.get("pincode")
        bevestig_pincode = request.form.get("bevestig_pincode")

        if pincode != bevestig_pincode:
            foutmelding = "De pincodes komen niet overeen!"
            db.close()
            return render_template("tarieven/dagpas.html", foutmelding=foutmelding, formdata=request.form)

        session["abonnement_data"] = {
            "type": "Dagpas",
            "voornaam": request.form.get("voornaam"),
            "achternaam": request.form.get("achternaam"),
            "email": request.form.get("email"),
            "telefoon": request.form.get("telefoon"),
            "geboortedatum": request.form.get("geboortedatum"),
            "pincode": pincode
        }

        prijzen = {
            "Dagpas": 500,
            "Weekpas": 1500,
            "Jaarkaart": 3000
        }

        try: #stripe checkout sessie aanmaken
            stripe_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "eur",
                        "unit_amount": prijzen["Dagpas"],
                        "product_data": {
                            "name": "Dagpas"
                        }
                    },
                    "quantity": 1
                }],
                mode="payment",
                success_url=request.host_url + "betaling-succes",
                cancel_url=request.host_url + "betaling-annulatie",
            )
            db.close()
            return redirect(stripe_session.url)
        except Exception as e:
            db.close()
            return f"Fout bij aanmaken van Stripe sessie: {str(e)}", 500

    db.close()
    return render_template("tarieven/dagpas.html", formdata={})


@routes.route("/tarieven/weekpas", methods=["GET", "POST"])
def weekpass():
    # Controleer of gebruiker is ingelogd
    if "Gebruiker" not in session:
        return redirect(url_for("routes.login", next="/tarieven/weekpas"))

    db = SessionLocal()
    gebruiker = db.query(Usertable).filter_by(user_id=session["Gebruiker"]["id"]).first()

    if request.method == "POST":
        if gebruiker and gebruiker.abonnement != "Geen abonnement":
            foutmelding = f"Je hebt al een {gebruiker.abonnement.lower()}."
            db.close()
            return render_template("tarieven/weekpas.html", foutmelding=foutmelding, formdata=request.form)

        pincode = request.form.get("pincode")
        bevestig_pincode = request.form.get("bevestig_pincode")

        if pincode != bevestig_pincode:
            foutmelding = "De pincodes komen niet overeen!"
            db.close()
            return render_template("tarieven/weekpas.html", foutmelding=foutmelding, formdata=request.form)

        # 🔐 Bewaar formulierdata tijdelijk in sessie
        session["abonnement_data"] = {
            "type": "Weekpas",
            "voornaam": request.form.get("voornaam"),
            "achternaam": request.form.get("achternaam"),
            "email": request.form.get("email"),
            "telefoon": request.form.get("telefoon"),
            "geboortedatum": request.form.get("geboortedatum"),
            "pincode": pincode
        }

        # 💳 Stripe prijzen (centen)
        prijzen = {
            "Dagpas": 500,
            "Weekpas": 1500,
            "Jaarkaart": 3000
        }

        # 🎯 Start een Stripe checkout sessie
        try:
            stripe_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "eur",
                        "unit_amount": prijzen["Weekpas"],
                        "product_data": {"name": "Weekpas"}
                    },
                    "quantity": 1
                }],
                mode="payment",
                success_url=request.host_url + "betaling-succes",
                cancel_url=request.host_url + "betaling-annulatie",
            )
            db.close()
            return redirect(stripe_session.url)
        except Exception as e:
            db.close()
            return f"Fout bij aanmaken van Stripe sessie: {str(e)}", 500

    db.close()
    return render_template("tarieven/weekpas.html", formdata={})


@routes.route("/tarieven/jaarkaart", methods=["GET", "POST"])
def jaarkaart():
    if "Gebruiker" not in session:
        return redirect(url_for("routes.login", next="/tarieven/jaarkaart"))

    db = SessionLocal()
    gebruiker = db.query(Usertable).filter_by(user_id=session["Gebruiker"]["id"]).first()

    if request.method == "POST":
        if gebruiker and gebruiker.abonnement != "Geen abonnement":
            foutmelding = f"Je hebt al een {gebruiker.abonnement.lower()}."
            db.close()
            return render_template("tarieven/jaarkaart.html", foutmelding=foutmelding, formdata=request.form)

        pincode = request.form.get("pincode")
        bevestig_pincode = request.form.get("bevestig_pincode")

        if pincode != bevestig_pincode:
            foutmelding = "De pincodes komen niet overeen!"
            return render_template("tarieven/jaarkaart.html", foutmelding=foutmelding, formdata=request.form)

        session["abonnement_data"] = {
            "type": "Jaarkaart",
            "voornaam": request.form.get("voornaam"),
            "achternaam": request.form.get("achternaam"),
            "email": request.form.get("email"),
            "telefoon": request.form.get("telefoon"),
            "geboortedatum": request.form.get("geboortedatum"),
            "pincode": pincode
        }

        return redirect(url_for("routes.create_checkout_session", abonnement_type="jaarkaart"))

    return render_template("tarieven/jaarkaart.html", formdata={})


@routes.route('/defect', methods=['GET', 'POST'])
def defect():
    if 'Gebruiker' not in session: #controle of gebruiker is ingelogd
        return redirect(url_for("routes.login", next=request.path))

    foutmelding = None

    if request.method == 'POST':
        fiets_id = request.form.get('fiets_id')
        probleem = request.form.get('probleem')

        if not fiets_id or not probleem:
            foutmelding = 'Gelieve alle velden in te vullen.'
        else:
            db = SessionLocal() #database sessie openen
            try:
                fiets = db.query(Fiets).filter_by(id=fiets_id).first() #zoekt de fiets in de database
                if not fiets:
                    foutmelding = "⚠️ Deze fiets bestaat niet in het systeem."
                else:
                    nieuw_defect = Defect( #een record aanmaken van de defect
                        fiets_id=int(fiets_id),
                        station_naam=fiets.station_naam,
                        probleem=probleem
                    )
                    db.add(nieuw_defect) #toevoegen aan de database
                    db.commit()
                    flash('✅ Je melding is doorgestuurd naar de administratie.', 'success')
                    return redirect(url_for('routes.profile'))
            except Exception as e:
                db.rollback() #bij foutmelding de db query annuleren
                foutmelding = f"Er ging iets mis bij het opslaan van de melding: {str(e)}"
            finally:
                db.close()

    return render_template("defect.html", foutmelding=foutmelding)


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
            db.refresh(gebruiker)

            session["Gebruiker"]["naam"] = nieuwe_naam
            session["Gebruiker"]["email"] = nieuwe_email
            session["Gebruiker"]["taal"] = taal

        flash("Instellingen succesvol opgeslagen.", "success")
        db.close()
        return redirect(url_for("routes.profile"))

    db.close()
    return render_template("instellingen.html", user=gebruiker)


@routes.route("/delete_account", methods=["POST"])
def delete_account():
    if "Gebruiker" not in session:
        return redirect(url_for("routes.login"))

    db = SessionLocal() #database connectie en checken of gebruiker in database is
    gebruiker = db.query(Usertable).filter_by(user_id=session["Gebruiker"]["id"]).first()
    if gebruiker: #als gebruiker in database is , wordt hij/zij verwijdert
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

# ======================
# TRANSPORT ROUTE
# ======================
@routes.route('/transport_dashboard')
@transport_required
def transport_dashboard():
    db_session = SessionLocal()
    stations = db_session.query(Station).all()

    # Haal defecte fietsen op
    defecten = db_session.query(Defect, Fiets, Station).join(Fiets, Defect.fiets_id == Fiets.id).join(Station, Defect.station_naam == Station.naam).all()

    LEEG_DREMPEL = 5  # minder dan 5 fietsen
    VOL_DREMPEL = 0.9  # 90% vol

    lege_stations = [s for s in stations if s.parked_bikes < LEEG_DREMPEL]
    volle_stations = [s for s in stations if s.parked_bikes / s.capaciteit > VOL_DREMPEL]

    # Haal fietsen op voor elk vol station
    station_fietsen = {}
    for station in volle_stations:
        fietsen = db_session.query(Fiets).filter(Fiets.station_naam == station.naam).all()
        station_fietsen[station.id] = [{"id": fiets.id, "status": fiets.status} for fiets in fietsen]
        print(f"Station {station.naam} (ID: {station.id}): {len(fietsen)} fietsen")  # Debug logging

    print("station_fietsen:", station_fietsen)
    # Sluit de database sessie
    db_session.close()

    return render_template(
        'transport.html',
        lege_stations=lege_stations,
        volle_stations=volle_stations,
        defecten=defecten,
        stations=stations,
        station_fietsen=station_fietsen
    )

@routes.route('/verplaats_geselecteerde_fietsen', methods=['POST'])
@transport_required
def verplaats_geselecteerde_fietsen():
    db_session = SessionLocal()
    try:
        from_station_id = request.form['from_station_id']  # Geen int() nodig
        to_station_id = request.form['to_station_id']      # Geen int() nodig
        fiets_ids = request.form.getlist('fiets_ids')      # Meerdere fiets-ID's

        if not fiets_ids:
            db_session.close()
            return redirect(url_for('routes.transport_dashboard', _anchor='volle_stations', message="Geen fietsen geselecteerd."))

        from_station = db_session.query(Station).filter_by(id=from_station_id).first()
        to_station = db_session.query(Station).filter_by(id=to_station_id).first()

        # Validatie
        if not from_station or not to_station:
            message = "Station niet gevonden."
        elif len(fiets_ids) > from_station.parked_bikes:
            message = f"Niet genoeg fietsen in {from_station.naam}."
        elif to_station.parked_bikes + len(fiets_ids) > to_station.capaciteit:
            message = f"{to_station.naam} heeft niet genoeg ruimte."
        else:
            # Update fietsen
            for fiets_id in fiets_ids:
                fiets = db_session.query(Fiets).filter_by(id=int(fiets_id)).first()  # fiets_id is een integer
                if fiets and fiets.station_naam == from_station.naam:
                    fiets.station_naam = to_station.naam

            # Update stations
            from_station.parked_bikes -= len(fiets_ids)
            to_station.parked_bikes += len(fiets_ids)
            db_session.commit()
            message = f"{len(fiets_ids)} fiets(en) verplaatst van {from_station.naam} naar {to_station.naam}."

    except Exception as e:
        db_session.rollback()
        message = f"Fout: {str(e)}"
    finally:
        db_session.close()

    return redirect(url_for('routes.transport_dashboard', _anchor='volle_stations', message=message))

@routes.route('/verplaats_defecte_fiets', methods=['POST'])
@transport_required
def verplaats_defecte_fiets():
    db_session = SessionLocal()
    try:
        fiets_id = int(request.form['fiets_id'])
        defect_id = int(request.form['defect_id'])
        to_station_id = request.form['to_station_id']
        nieuwe_status = request.form['status']

        print(f"DEBUG: fiets_id={fiets_id}, defect_id={defect_id}, to_station_id={to_station_id}, status={nieuwe_status}")


        # Haal fiets, defect en bestemmingsstation op
        fiets = db_session.query(Fiets).filter_by(id=fiets_id).first()
        defect = db_session.query(Defect).filter_by(id=defect_id).first()
        to_station = db_session.query(Station).filter_by(id=to_station_id).first()

        print(f"DEBUG: fiets={fiets}, defect={defect}, to_station={to_station}")

        if not fiets or not defect or not to_station:
            db_session.close()
            return redirect(url_for('routes.transport_dashboard', _anchor='defecten', message="Fiets, defect of station niet gevonden."))

        # Controleer of het bestemmingsstation ruimte heeft
        if to_station.parked_bikes >= to_station.capaciteit:
            db_session.close()
            return redirect(url_for('routes.transport_dashboard', _anchor='defecten', message=f"{to_station.naam} heeft geen ruimte meer."))

        # Huidige station bijwerken (fiets verwijderen)
        from_station = db_session.query(Station).filter_by(naam=fiets.station_naam).first()
        if from_station:
            from_station.parked_bikes -= 1

        # Bestemmingsstation bijwerken (fiets toevoegen)
        to_station.parked_bikes += 1

        # Fiets en defect bijwerken
        fiets.station_naam = to_station.naam
        fiets.status = nieuwe_status
        defect.station_naam = to_station.naam

        # Als status niet meer "onderhoud" is, verwijder het defect
        if nieuwe_status != "onderhoud":
            db_session.delete(defect)

        db_session.commit()
        message = f"Fiets {fiets_id} verplaatst naar {to_station.naam} met status '{nieuwe_status}'."
    except Exception as e:
        db_session.rollback()
        message = f"Fout: {str(e)}"
    finally:
        db_session.close()

    return redirect(url_for('routes.transport_dashboard', _anchor='defecten', message=message))

# ======================
# ADMIN ROUTE
# ======================
@routes.route("/admin")
@admin_required
def admin():
    laatste_simulatie = session.get("laatste_simulatie")
    return render_template("admin.html", laatste_simulatie=laatste_simulatie)


@routes.route("/admin/livedata", methods=["GET"])
@admin_required
def admin_livedata():
    boodschap = None
    ritten = []
    data_bron = "database"

    aantal_ritten = 0
    gemiddelde_duur = 0
    langste_rit = 0
    meest_gebruikte_fiets = 0
    populairst_station = None
    drukste_per_station = []

    db = SessionLocal()

    try:
        db_ritten = db.query(Geschiedenis).all()
        for rit in db_ritten:
            ritten.append({
                "gebruiker_id": rit.gebruiker_id,
                "fiets_id": rit.fiets_id,
                "begin_station_naam": rit.start_station_naam,
                "eind_station_naam": rit.eind_station_naam,
                "duur_minuten": float(rit.duur_minuten) if rit.duur_minuten else 0,
                "starttijd": rit.starttijd
            })

        if ritten:
            aantal_ritten = len(ritten)
            gemiddelde_duur = round(sum(r["duur_minuten"] for r in ritten) / aantal_ritten, 2)
            langste_rit = max(r["duur_minuten"] for r in ritten)

            fiets_teller = Counter(r["fiets_id"] for r in ritten)
            meest_gebruikte_fiets = fiets_teller.most_common(1)[0][0] if fiets_teller else None

            station_teller = Counter(r["begin_station_naam"] for r in ritten)
            populairst_station = station_teller.most_common(1)[0] if station_teller else None

            station_uren_counter = {}
            for rit in ritten:
                station_naam = rit["begin_station_naam"]
                starttijd = rit["starttijd"]
                startuur = datetime.strptime(starttijd, "%Y-%m-%d %H:%M:%S").hour if isinstance(starttijd, str) else starttijd.hour
                station_uren_counter.setdefault(station_naam, Counter())[startuur] += 1

            db_stations = db.query(Station).all()
            for station in db_stations:
                station_naam = station.naam
                if station_naam in station_uren_counter:
                    meest_uur, aantal = station_uren_counter[station_naam].most_common(1)[0]
                    tijdvak = f"{meest_uur:02d}:00 - {meest_uur:02d}:59"
                    drukste_per_station.append({
                        "naam": station_naam,
                        "tijdvak": tijdvak,
                        "aantal": aantal
                    })

            drukste_per_station.sort(key=lambda x: x["aantal"], reverse=True)

    except Exception as e:
        boodschap = f"⚠️ Fout bij ophalen database data: {str(e)}"

    stations_overzicht = []
    try:
        db_stations = db.query(Station).all()
        for s in db_stations:
            stations_overzicht.append({
                "naam": s.naam,
                "fietsen": s.parked_bikes,
                "vrij": s.free_slots
            })
    except:
        boodschap = "⚠️ Fout bij ophalen stationgegevens."

    return render_template(
        "admin_livedata.html",
        boodschap=boodschap,
        ritten=ritten,
        csv_bestand=None,
        stations_overzicht=stations_overzicht,
        aantal_ritten=aantal_ritten,
        gemiddelde_duur=gemiddelde_duur,
        langste_rit=langste_rit,
        meest_gebruikte_fiets=meest_gebruikte_fiets,
        populairst_station=populairst_station,
        drukste_per_station=drukste_per_station,
        data_bron=data_bron
    )


@routes.route("/admin/simulatie", methods=["GET", "POST"])
@admin_required
def admin_simulatie():
    boodschap = None
    ritten = []
    csv_bestand = None
    data_bron = "simulatie"
    stations_copy = None
    aantal_ritten = 0
    gemiddelde_duur = 0
    langste_rit = 0
    meest_gebruikte_fiets = None
    populairst_station = None
    drukste_per_station = []

    stations_copy = None

    if request.method == "POST":
        actie = request.form.get("actie", "")

        if actie == "simulatie":
            try:
                gebruikers_aantal = int(request.form.get("gebruikers"))
                fietsen_aantal = int(request.form.get("fietsen"))
                dagen = int(request.form.get("dagen"))

                gebruikers = simulation.genereer_gebruikers(gebruikers_aantal)
                stations_copy = copy.deepcopy(simulation.stations)
                fietsen = simulation.genereer_fietsen(fietsen_aantal, stations_copy)
                ritten = simulation.genereer_geschiedenis(gebruikers, fietsen, stations_copy, dagen)

                aantal_ritten = len(ritten)
                gemiddelde_duur = round(sum(r["duur_minuten"] for r in ritten) / aantal_ritten, 2) if ritten else 0
                langste_rit = max((r["duur_minuten"] for r in ritten), default=0)

                fiets_teller = Counter(r["fiets_id"] for r in ritten)
                meest_gebruikte_fiets = fiets_teller.most_common(1)[0][0] if fiets_teller else None

                station_teller = Counter(r["begin_station_naam"] for r in ritten)
                populairst_station = station_teller.most_common(1)[0] if station_teller else None

                station_uren_counter = {}
                for rit in ritten:
                    station_naam = rit["begin_station_naam"]
                    starttijd = rit["starttijd"]
                    startuur = datetime.strptime(starttijd, "%Y-%m-%d %H:%M:%S").hour if isinstance(starttijd, str) else starttijd.hour
                    station_uren_counter.setdefault(station_naam, Counter())[startuur] += 1

                drukste_per_station = []
                for station in stations_copy:
                    naam = station["name"]
                    if naam in station_uren_counter:
                        meest_uur, aantal = station_uren_counter[naam].most_common(1)[0]
                        tijdvak = f"{meest_uur:02d}:00 - {meest_uur:02d}:59"
                        drukste_per_station.append({
                            "naam": naam,
                            "tijdvak": tijdvak,
                            "aantal": aantal
                        })

                drukste_per_station.sort(key=lambda x: x["aantal"], reverse=True)

                # CSV export
                csv_bestand = f"/tmp/ritten_simulatie_{uuid.uuid4().hex}.csv"
                with open(csv_bestand, mode="w", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow(["gebruiker_id", "fiets_id", "begin_station_naam", "eind_station_naam", "duur_minuten"])
                    for rit in ritten:
                        writer.writerow([
                            rit["gebruiker_id"],
                            rit["fiets_id"],
                            rit["begin_station_naam"],
                            rit["eind_station_naam"],
                            rit["duur_minuten"]
                        ])
                session["laatste_csv"] = csv_bestand
                session["laatste_simulatie"] = datetime.now(pytz.timezone("Europe/Brussels")).strftime("%d-%m-%Y om %H:%M")

                boodschap = f"✅ Simulatie uitgevoerd met {len(ritten)} ritten."

            except Exception as e:
                boodschap = f"❌ Fout bij simulatie: {str(e)}"

    # Stationen tonen
    stations_overzicht = []
    if stations_copy:
        for s in stations_copy:
            stations_overzicht.append({
                "naam": s["name"],
                "fietsen": s["free_bikes"],
                "vrij": s["free_slots"]
            })
    else:
        for s in simulation.stations:
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
        data_bron=data_bron
    )

@routes.route("/admin/download_csv")
@admin_required
def download_csv():
    csv_filename = session.get("laatste_csv")
    if not csv_filename:
        return "Geen CSV-bestand beschikbaar.", 404

    csv_path = os.path.join("/tmp", csv_filename)
    if not os.path.exists(csv_path):
        return "Bestand bestaat niet meer.", 404

    return send_file(csv_path, as_attachment=True)


@routes.route("/admin/data")
@admin_required
def admin_data():
    stations = get_alle_stations()
    print("DEBUG: voorbeeldstation =", stations[0] if stations else "No stations")
    if not stations:
        flash("Failed to fetch station data from API", "error")

    # Calculate totals
    total_bikes = sum(int(s['free-bikes']) for s in stations if s.get('free-bikes') is not None)
    total_slots = sum(int(s['empty-slots']) for s in stations if s.get('empty-slots') is not None)
    total_capacity = sum(int(s['capacity']) for s in stations if s.get('capacity') is not None)
    print(f"DEBUG: Totals - bikes: {total_bikes}, slots: {total_slots}, capacity: {total_capacity}")

    session["live_data_update"] = datetime.now().strftime("%H:%M:%S")
    populairste_station = {
        "naam": "Station Zuid",
        "ritten": 23
    }
    return render_template(
        "live_data.html",
        stations=stations,
        populairste_station=populairste_station,
        total_bikes=total_bikes,
        total_slots=total_slots,
        total_capacity=total_capacity
    )


@routes.route("/admin/user_filter", methods=["GET", "POST"])
@admin_required
def admin_filter():
    from sqlalchemy.orm import aliased
    from collections import defaultdict
    from datetime import datetime

    db = SessionLocal()

    try:
        gebruikers = db.query(Gebruiker).all()
        print("DEBUG: aantal gebruikers =", len(gebruikers))

        geselecteerde_gebruiker = None
        ritten = []
        ritten_per_dag = {}

        if request.method == "POST":
            gebruiker_id = request.form.get("gebruiker_id")
            print(f"DEBUG: geselecteerde gebruiker_id = {gebruiker_id}")

            if gebruiker_id:
                # Converteer naar int als het een string is
                try:
                    gebruiker_id = int(gebruiker_id)
                except (ValueError, TypeError):
                    print(f"DEBUG: Ongeldige gebruiker_id: {gebruiker_id}")
                    gebruiker_id = None

                if gebruiker_id:
                    geselecteerde_gebruiker = db.query(Gebruiker).filter_by(id=gebruiker_id).first()
                    print(f"DEBUG: geselecteerde gebruiker gevonden = {geselecteerde_gebruiker is not None}")

                    if geselecteerde_gebruiker:
                        # Haal alle ritten op voor deze gebruiker
                        ritten = db.query(Geschiedenis).filter(
                            Geschiedenis.gebruiker_id == geselecteerde_gebruiker.id
                        ).order_by(Geschiedenis.starttijd.desc()).all()

                        print(f"DEBUG: aantal ritten gevonden = {len(ritten)}")

                        # Bereken ritten per dag
                        ritten_per_dag_count = defaultdict(int)
                        for rit in ritten:
                            if rit.starttijd:
                                try:
                                    # Converteer naar datetime als het een string is
                                    if isinstance(rit.starttijd, str):
                                        datum = datetime.strptime(rit.starttijd, "%Y-%m-%d %H:%M:%S").date()
                                    else:
                                        datum = rit.starttijd.date()

                                    datum_str = datum.strftime("%Y-%m-%d")
                                    ritten_per_dag_count[datum_str] += 1
                                except Exception as e:
                                    print(f"DEBUG: Fout bij datum conversie: {e}")
                                    continue

                        # Sorteer op datum (nieuwste eerst)
                        ritten_per_dag = dict(sorted(ritten_per_dag_count.items(), reverse=True))
                        print(f"DEBUG: ritten_per_dag = {len(ritten_per_dag)} dagen")

        return render_template(
            "user_filter.html",
            gebruikers=gebruikers,
            geselecteerde_gebruiker=geselecteerde_gebruiker,
            ritten=ritten,
            ritten_per_dag=ritten_per_dag
        )

    except Exception as e:
        print(f"ERROR in admin_filter: {e}")
        import traceback
        traceback.print_exc()

        # Return lege data bij fout, maar wel de gebruikers
        try:
            gebruikers = db.query(Gebruiker).all()
        except:
            gebruikers = []

        return render_template(
            "user_filter.html",
            gebruikers=gebruikers,
            geselecteerde_gebruiker=None,
            ritten=[],
            ritten_per_dag={}
        )

    finally:
        db.close()



# ================= Stripe - Betalingen ====================
@routes.route("/betalen")
def betalen():
    return render_template("betalen.html", public_key=os.getenv("STRIPE_PUBLIC_KEY"))


@routes.route("/create-checkout-session")
def create_checkout_session():
    abonnement_type = request.args.get("abonnement_type", "dagpas") #type abonnement van url halen

    prijzen = {
        "dagpas": 500,
        "weekpas": 1000,
        "jaarkaart": 5000
    }

    bedrag = prijzen.get(abonnement_type, 500)

    try:
        session = stripe.checkout.Session.create( #stripe cheeckout sessie
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "unit_amount": bedrag,
                    "product_data": {
                        "name": abonnement_type.capitalize(),
                    },
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=request.host_url + "succes",
            cancel_url=request.host_url + "annulatie",
        )
        return redirect(session.url, code=303)
    except Exception as e:
        return jsonify(error=str(e)), 400


@routes.route("/betaling-succes")
def betaling_succes():
    if "Gebruiker" not in session or "id" not in session["Gebruiker"]:
        return "Geen geldige sessie gevonden. Log opnieuw in.", 401

    data = session.pop("abonnement_data", None)
    if not data:
        return "Geen gegevens gevonden.", 400

    from app.database import SessionLocal
    from app.database.models import Usertable, Pas
    from datetime import datetime, timedelta
    from app.utils.email import send_abonnement_email

    db = SessionLocal()

    # Check of gebruiker ingelogd is
    gebruiker = None
    if "Gebruiker" in session and "id" in session["Gebruiker"]:
        gebruiker = db.query(Usertable).filter_by(user_id=session["Gebruiker"]["id"]).first()
    else:
        db.close()
        return "Je moet ingelogd zijn om een abonnement aan te maken.", 403


    # Bepaal soort en einddatum
    soort = data["type"].lower()
    start_datum = datetime.utcnow()

    if soort in ["dag", "dagpas"]:
        eind_datum = start_datum + timedelta(days=1)
        soort = "dag"
    elif soort in ["week", "weekpas"]:
        eind_datum = start_datum + timedelta(weeks=1)
        soort = "week"
    elif soort in ["jaar", "jaarkaart"]:
        eind_datum = None
        soort = "jaar"
    else:
        db.close()
        return f"Ongeldig abonnementstype: {data['type']}", 400

    gebruiker.abonnement = data["type"]
    session["Gebruiker"]["abonnement"] = data["type"]

    nieuwe_pas = Pas(
        gebruiker_id=gebruiker.id,
        soort=soort,
        pincode=data["pincode"],
        start_datum=start_datum,
        eind_datum=eind_datum
    )
    db.add(nieuwe_pas)
    db.commit()
    db.close()

    if soort in ["dag", "week"]:
        einddatum_tekst = eind_datum.strftime("%d/%m/%Y")
    else:
        einddatum_tekst = "Zolang je abonnement actief is"

    return render_template("tarieven/bedankt.html", gebruiker=gebruiker, data=data, einddatum=einddatum_tekst)


@routes.route("/betaling-annulatie")
def betaling_annulatie():
    flash("Je betaling werd geannuleerd.", "danger")

@routes.route("/annulatie")
def annulatie():
    return "<h1>❌ Betaling geannuleerd.</h1>"


@routes.route("/contact", methods=["GET", "POST"])
def contact():
    foutmelding = None

    if request.method == "POST":
        naam = request.form.get("naam")
        email = request.form.get("email")
        telefoon = request.form.get("telefoon")
        reden = request.form.get("reden")
        onderwerp = request.form.get("onderwerp")
        bericht = request.form.get("bericht")

        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        telefoon_regex = r"^(?:\+32|0)[1-9][0-9]{7,8}$"

        if not re.match(email_regex, email):
            foutmelding = "❌ Ongeldig e-mailadres. Voorbeeld: naam@voorbeeld.be"
        elif telefoon and not re.match(telefoon_regex, telefoon):
            foutmelding = "❌ Ongeldig telefoonnummer. Voorbeeld: 0471234567 of +32471234567"
        elif not naam or not email or not reden or not onderwerp or not bericht:
            foutmelding = "❌ Gelieve alle verplichte velden in te vullen."
        else:
            db = SessionLocal()
            nieuw_bericht = ContactBericht(
                naam=naam,
                email=email,
                telefoon=telefoon,
                reden=reden,
                onderwerp=onderwerp,
                bericht=bericht
            )
            db.add(nieuw_bericht)
            db.commit()
            db.close()

            return redirect(url_for("routes.contact_bevestiging"))

    return render_template("contact.html", foutmelding=foutmelding)

