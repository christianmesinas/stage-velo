from datetime import datetime

import stripe
from flask import jsonify



import pytz
from app.database.models import Usertable, Gebruiker
from flask import Blueprint, send_file, session, redirect, url_for, request, render_template,flash
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
from app.database.models import Usertable, Defect, Fiets, Geschiedenis
from app.database import SessionLocal
from app.simulation import simulation
from collections import Counter
from functools import wraps
from werkzeug.utils import secure_filename


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        gebruiker = session.get("Gebruiker")
        if not gebruiker:
            return redirect(url_for("routes.login", next=request.path))
        if gebruiker.get("email") != os.getenv("ADMIN_EMAIL"):
            return "❌ Geen toegang: je bent geen administrator", 403
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
    redirect_to = request.json.get("redirect_to", "/profile")

    if not token:
        return {"error": "Access token ontbreekt"}, 400  # Нет токена / Geen toegangstoken

    headers = {'Authorization': f'Bearer {token}'}  # Заголовок с токеном / Authorization-header
    try:
        user_info = requests.get(
            f'https://{env.get("AUTH0_DOMAIN")}/userinfo', headers=headers
        ).json()  # Получение инфо о юзере / Haal gebruikersinfo op
    except Exception as e:
        return {"error": f"Fout bij ophalen userinfo: {str(e)}"}, 500

    user_id = user_info.get("sub")
    email = user_info.get("email")
    name = user_info.get("name", "")
    profile_picture = user_info.get("picture", "img/default.png")

    session["Gebruiker"] = {  # Сохранить в сессию / Sla op in sessie
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

    return redirect(redirect_to)

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
def dagpas():
    if request.method == "POST":
        pincode = request.form.get("pincode")
        bevestig_pincode = request.form.get("bevestig_pincode")

        if pincode != bevestig_pincode:
            foutmelding = "De pincodes komen niet overeen!"
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

        try:
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
            return redirect(stripe_session.url)
        except Exception as e:
            return f"Fout bij aanmaken van Stripe sessie: {str(e)}", 500

    return render_template("tarieven/dagpas.html", formdata={})



@routes.route("/tarieven/weekpas", methods=["GET", "POST"])
def weekpass():
    if request.method == "POST":
        pincode = request.form.get("pincode")
        bevestig_pincode = request.form.get("bevestig_pincode")

        if pincode != bevestig_pincode:
            foutmelding = "De pincodes komen niet overeen!"
            return render_template("tarieven/weekpas.html", foutmelding=foutmelding, formdata=request.form)

        session["abonnement_data"] = {
            "type": "Weekpas",
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

        try:
            stripe_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "eur",
                        "unit_amount": prijzen["Weekpas"],
                        "product_data": {
                            "name": "Weekpas"
                        }
                    },
                    "quantity": 1
                }],
                mode="payment",
                success_url=request.host_url + "betaling-succes",
                cancel_url=request.host_url + "betaling-annulatie",
            )
            return redirect(stripe_session.url)
        except Exception as e:
            return f"Fout bij aanmaken Stripe sessie: {str(e)}", 500

    return render_template("tarieven/weekpas.html", formdata={})




@routes.route("/tarieven/jaarkaart", methods=["GET", "POST"])
def jaarkaart():
    if request.method == "POST":
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
    if 'Gebruiker' not in session:
        return redirect(url_for("routes.login", next=request.path))

    foutmelding = None

    if request.method == 'POST':
        fiets_id = request.form.get('fiets_id')
        probleem = request.form.get('probleem')

        if not fiets_id or not probleem:
            foutmelding = 'Gelieve alle velden in te vullen.'
        else:
            db = SessionLocal()
            try:
                fiets = db.query(Fiets).filter_by(id=fiets_id).first()
                if not fiets:
                    foutmelding = "⚠️ Deze fiets bestaat niet in het systeem."
                else:
                    nieuw_defect = Defect(
                        fiets_id=int(fiets_id),
                        probleem=probleem
                    )
                    db.add(nieuw_defect)
                    db.commit()
                    flash('✅ Je melding is doorgestuurd naar de administratie.', 'success')
                    return redirect(url_for('routes.profile'))
            except Exception as e:
                db.rollback()
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
            session["laatste_csv"] = csv_bestand

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




# ================= Stripe - Betalingen ====================
@routes.route("/betalen")
def betalen():
    return render_template("betalen.html", public_key=os.getenv("STRIPE_PUBLIC_KEY"))


@routes.route("/create-checkout-session")
def create_checkout_session():
    abonnement_type = request.args.get("abonnement_type", "dagpas")

    prijzen = {
        "dagpas": 500,
        "weekpas": 1000,
        "jaarkaart": 5000
    }

    bedrag = prijzen.get(abonnement_type, 500)

    try:
        session = stripe.checkout.Session.create(
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
    data = session.pop("abonnement_data", None)
    if not data:
        return "Geen gegevens gevonden.", 400

    from app.database import SessionLocal
    from app.database.models import Usertable

    db = SessionLocal()
    gebruiker = db.query(Usertable).filter_by(user_id=session["Gebruiker"]["id"]).first()
    if gebruiker:
        gebruiker.abonnement = data["type"]
        db.commit()
        session["Gebruiker"]["abonnement"] = data["type"]
    db.close()

    flash(f"{data['type']} succesvol geactiveerd!", "success")
    return render_template("tarieven/bedankt.html", data=data)

@routes.route("/betaling-annulatie")
def betaling_annulatie():
    flash("Je betaling werd geannuleerd.", "danger")
    return redirect(url_for("routes.tarieven"))
