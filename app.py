from flask import Flask, session
from dotenv import load_dotenv
from os import getenv

from app.database import SessionLocal
from app.database.models import Base
from app.routes import routes
from authlib.integrations.flask_client import OAuth

# ✅ Laad .ENV-bestand
load_dotenv()

# ✅ Initialiseer Flask
app = Flask(__name__, template_folder="app/templates", static_folder="app/static")

# ✅ Stel de secret key in voor sessies
app.secret_key = getenv("SECRET_KEY", "fallback-secret")

# ✅ OAuth instellen
oauth = OAuth(app)
oauth.register(
    "auth0",
    client_id=getenv("AUTH0_CLIENT_ID"),
    client_secret=getenv("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
        "audience": "https://" + getenv("AUTH0_DOMAIN") + "/api/v2/"
    },
    server_metadata_url=f'https://{getenv("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

# ✅ Registreer je Blueprint-routes
app.register_blueprint(routes)

with app.app_context():
    db = SessionLocal()
    Base.metadata.create_all(bind=db.bind)
    db.close()
    print("✅ Tabellen automatisch aangemaakt bij opstart!")


@app.context_processor
def inject_user():
    return dict(user=session.get("user"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)




