from flask import Flask, session, request, render_template, redirect, url_for
from dotenv import load_dotenv
from os import getenv
from datetime import datetime
import stripe
from app.database import SessionLocal
from app.database.models import Base
from app.routes import routes
from authlib.integrations.flask_client import OAuth
from flask_babel import Babel, _
import logging

# ✅ Laad .ENV-bestand
load_dotenv()
stripe.api_key = getenv('STRIPE_SECRET_KEY')

# ✅ Initialiseer Flask
app = Flask(__name__, template_folder="app/templates", static_folder="app/static")

# Babel configuratie
app.config['BABEL_DEFAULT_LOCALE'] = 'nl'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'app/translations'
app.config['BABEL_SUPPORTED_LOCALES'] = ['nl', 'en', 'fr', 'es', 'de']

def get_locale():
    # Check query parameter
    #check taal van de site
    if 'lang' in request.args:
        language = request.args.get('lang')
        if language in ['nl', 'en', 'fr', 'es', 'de']:
            session['language'] = language
            logging.debug(f"Set language from query param: {language}")
            return language
    # Check session als het niet in de url zit
    if 'language' in session:
        language = session['language']
        logging.debug(f"Language from session: {language}")
        return language
    # standaardtaal Nederlands
    logging.debug("Using default language: nl")
    return 'nl'

#initialiseer babel
babel = Babel(app, locale_selector=get_locale)

app.secret_key = getenv("SECRET_KEY", "fallback-secret")

# Stel de secret key in voor sessies,
app.secret_key = getenv("SECRET_KEY", "fallback-secret")

# OAuth instellen,
oauth = OAuth(app)
oauth.register(
    "auth0",
    client_id=getenv("AUTH0_CLIENT_ID"),
    client_secret=getenv("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
        "audience": "https://" + getenv("AUTH0_DOMAIN") + "/api/v2/"
    },
    server_metadata_url=f'https://{getenv("auth0_domain")}/.well-known/openid-configuration'
)

# ✅ Registreer je Blueprint-routes
app.register_blueprint(routes)

#zorg dat de databasetabellen automatisch worden aangemaakt bij het opstarten van de app
# with app.app_context():
#     db = SessionLocal()
#     Base.metadata.create_all(bind=db.bind)
#     db.close()
#     print("✅ Tabellen automatisch aangemaakt bij opstart!")


@app.context_processor
def inject_user(): #voeg ingelogde gebruiker toe aan elke template
    return dict(user=session.get("user"))

@app.context_processor
def inject_datetime():
    return dict(datetime=datetime)

@app.context_processor
def inject_language():
    # Ensure the current locale is always available to templates as {{ language }}
    return {
        'language': str(get_locale())  # Convert Locale object to string like "en", "fr", etc.
    }

#opstart app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)