# Velo Fietsdeelsysteem

Een webapplicatie voor het beheren van het Velo fietsdeelsysteem in Antwerpen, ontwikkeld als onderdeel van een stageopdracht. De applicatie ondersteunt fietsverhuur, stationsbeheer, gebruikersbeheer en een simulatiemodus voor fietsverplaatsingen, gebaseerd op de [Open Data Stad Antwerpen - Velo's](https://www.antwerpen.be/nl/info/5203a7147a8a3b9d1e000042/Velo-Antwerpen) dataset.

## Inhoudsopgave
- [Projectoverzicht](#projectoverzicht)
- [Functionaliteiten](#functionaliteiten)
- [Technische Stack](#technische-stack)
- [Installatie](#installatie)
- [Omgevingsvariabelen](#omgevingsvariabelen)
- [Docker Configuratie](#docker-configuratie)
- [Gebruik](#gebruik)
- [Mappenstructuur](#mappenstructuur)
- [Ontwikkelingsnotities](#ontwikkelingsnotities)
- [Inlevering](#inlevering)
- [Licentie](#licentie)

## Projectoverzicht
De Velo-applicatie beheert een fietsdeelsysteem voor Antwerpen, met functionaliteiten voor gebruikers om fietsen te huren en terug te brengen, en voor beheerders om stations, fietsen en transportvoertuigen te beheren. Het systeem simuleert realistische fietsverplaatsingen met ongeveer 4.200 fietsen, 309 stations en 55.000+ gebruikers, gebaseerd op openbare Velo-data. Een webinterface biedt een gebruiksvriendelijke ervaring, met extra functies zoals meertalige ondersteuning en betalingen via Stripe.

## Functionaliteiten
- **Gebruikersbeheer**: Registratie en beheer van gebruikers met willekeurig gegenereerde gegevens.
- **Fiets- en Stationsbeheer**: Beheer van fietsen, stations en slots, inclusief huren en retourneren.
- **Fietstransporteurs**: Modelleren van vrachtwagens die fietsen herverdelen tussen stations.
- **Simulatiemodus**: Automatische fietsverplaatsingen met versnelde tijd, startbaar via webinterface.
- **Meertaligheid**: Ondersteuning voor Nederlands, Engels, Frans, Duits en Spaans.
- **Datapersistentie**: Gegevensopslag in PostgreSQL met keuze tussen reset of voortzetten.
- **Gebruiksvriendelijke UI**: Responsieve webinterface met interactieve kaarten.
- **Extra's**: Gebruikersprofielen, contactformulieren, defectmeldingen, live datavisualisatie en Stripe-betalingen.

## Technische Stack
- **Backend**: Python, Flask
- **Database**: PostgreSQL, SQLAlchemy, Alembic
- **Frontend**: HTML, CSS, JavaScript
- **Lokalisatie**: Flask-Babel
- **Authenticatie**: Auth0
- **Betalingen**: Stripe
- **E-mail**: Gmail
- **Containerisatie**: Docker, Docker Compose
- **Afhankelijkheden**: Zie `requirements.txt`

## Installatie

### Vereisten
- Python 3.13
- PostgreSQL
- Docker (optioneel, voor containerized deployment)
- Virtuele omgeving (aanbevolen)
- Accounts voor Auth0, Stripe en Gmail

### Stappen
1. **Kloon de repository**:
   ```bash
   git clone <repository-url>
   cd velo-app
   ```

2. **Maak een virtuele omgeving**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. **Installeer afhankelijkheden**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configureer omgevingsvariabelen**:
   - Maak een `.env`-bestand (zie [Omgevingsvariabelen](#omgevingsvariabelen)).
   - Voeg benodigde sleutels en credentials toe.

5. **Configureer de database**:
   - Start PostgreSQL.
   - Werk `config.py` of `.env` bij met databasegegevens.
   - Initialiseer en migreer:
     ```bash
     flask db init
     flask db migrate
     flask db upgrade
     ```

6. **Laad initiële data**:
   - Plaats de Velo JSON-dataset in `app/api/stations.csv`.
   - Voer uit:
     ```bash
     python app.py --init-data
     ```

## Omgevingsvariabelen
Configureer de volgende variabelen in een `.env`-bestand in de hoofdmap:

- **PostgreSQL**:
  - `POSTGRES_USER`: Database-gebruikersnaam
  - `POSTGRES_PASSWORD`: Database-wachtwoord
  - `POSTGRES_DB`: Databasenaam
  - `DATABASE_URL`: Verbindingsstring (bijv. `postgresql://<user>:<password>@<host>:<port>/<database>`)

- **pgAdmin**:
  - `PGADMIN_DEFAULT_EMAIL`: E-mail voor pgAdmin
  - `PGADMIN_DEFAULT_PASSWORD`: Wachtwoord voor pgAdmin

- **Flask & Auth0**:
  - `SECRET_KEY`: Geheime sleutel voor Flask
  - `AUTH0_CLIENT_ID`: Auth0 client-ID
  - `AUTH0_CLIENT_SECRET`: Auth0 client-geheim
  - `AUTH0_DOMAIN`: Auth0-domein
  - `AUTH0_CALLBACK_URL`: Callback-URL voor login
  - `AUTH0_LOGOUT_URL`: URL voor uitloggen

- **E-mail**:
  - `ADMIN_EMAIL`: Beheerders-e-mail
  - `TRANSPORT_EMAIL`: E-mail voor transport
  - `GMAIL_EMAIL`: Gmail-adres voor notificaties
  - `GMAIL_APP_PASSWORD`: Gmail app-specifiek wachtwoord

- **Stripe**:
  - `STRIPE_SECRET_KEY`: Stripe geheime sleutel
  - `STRIPE_PUBLIC_KEY`: Stripe publieke sleutel

**Opmerking**: Voeg `.env` toe aan `.gitignore` om gevoelige gegevens te beschermen.

## Docker Configuratie
De applicatie kan worden uitgevoerd met Docker Compose, dat de volgende services definieert:

- **db**: PostgreSQL-database (image: `postgres:15`)
  - Container: `velo_db`
  - Poort: `5433:5432`
  - Volume: `postgres_data` voor persistente opslag
  - Omgevingsvariabelen: Geladen uit `.env`
  - Tijdzone: Europe/Amsterdam

- **pgadmin**: pgAdmin4 voor databasebeheer
  - Container: `velo_pgadmin`
  - Poort: `80:80`
  - Volume: `pgadmin_data` voor configuratie
  - Afhankelijk van: `db`

- **web**: Flask-webapplicatie
  - Container: `velo_web`
  - Poort: `8000:8000`
  - Volume: Projectmap gesynchroniseerd met `/app` voor live reload
  - Commando: `python app.py`
  - Afhankelijk van: `db`

- **app**: Simulatiemodus
  - Bouwt vanuit dezelfde Dockerfile als `web`
  - Werkt in: `/app/app/simulation`
  - Commando: `python simulation.py`
  - Afhankelijk van: `db`

7. **Starten met Docker**:
```bash
docker-compose up --build
```
- Bezoek `http://localhost:8000` voor de webinterface.
- Bezoek `http://localhost` voor pgAdmin.
- Simulatiemodus draait automatisch in de `app`-container.

## Gebruik
- **Webinterface**:
  - **Startpagina**: Toont beschikbare fietsen en stations.
  - **Gebruikers**: Registreer, log in (via Auth0), huur/lever fietsen, meld defecten, neem contact op.
  - **Beheerders**: Beheer stations, fietsen, gebruikers; bekijk live data of simulaties.
  - **Simulatiemodus**: Start via admininterface.
- **Datapersistentie**: Kies bij opstarten voor reset of voortzetting van gegevens.
- **Talen**: Schakel tussen Nederlands, Engels, Frans, Duits en Spaans.
- **Betalingen**: Koop passen (dag, week, jaar) via Stripe.

## Mappenstructuur
```
velo-app/
├── Dockerfile                # Docker-configuratie
├── LICENSE                   # Licentie
├── README.md                 # Documentatie
2├── docker-compose.yml       # Docker Compose-configuratie
├── alembic/                  # Database-migraties
│   ├── env.py                # Alembic-configuratie
│   ├── script.py.mako        # Migratiesjabloon
│   └── versions/             # Migratiescripts
├── alembic.ini               # Alembic-instellingen
├── app/                      # Applicatiecode
│   ├── api/                  # API en gegevensverwerking
│   │   ├── api.py            # API-eindpunten
│   │   ├── stations.csv      # Velo-dataset
│   │   └── stations.py       # Stationsverwerking
│   ├── database/             # Database-modellen
│   │   ├── models.py         # SQLAlchemy-modellen
│   │   └── session.py        # Sessiebeheer
│   ├── profiel_pagina/       # Gebruikersprofielen
│   ├── routes.py             # Flask-routes
│   ├── simulation/           # Simulatiemodus
│   │   ├── simulation.py     # Simulatielogica
│   │   ├── simulatie_output.csv  # Simulatie-uitvoer
│   │   └── velo.csv          # Simulatiegegevens
│   ├── static/               # Statische bestanden
│   │   ├── css/              # Stijlbladen
│   │   ├── images/           # Afbeeldingen/iconen
│   │   ├── img/              # Extra afbeeldingen
│   │   ├── js/               # JavaScript (kaarten, popups)
│   │   └── uploads/          # Geüploade bestanden
│   ├── templates/            # HTML-sjablonen
│   ├── translations/         # Vertaalbestanden
│   └── utils/                # Hulpscripts (e-mail)
├── app.py                    # Hoofdscript
├── config.py                 # Configuratie
├── reflectie/                # Reflectiedocumenten
│   ├── Verslag-project.md    # Reflectieverslag
│   ├── Verslag Velo Stageopdracht.odt  # Stageverslag
│   └── stage logboek.docx    # Logboek
├── requirements.txt          # Afhankelijkheden
└── stage esemte logo.jpeg    # Logo
```

## Ontwikkelingsnotities
- **Migraties**: Alembic beheert databasewijzigingen (bijv. gastpas, contactberichten).
- **Simulatie**: `simulation.py` modelleert fietsverplaatsingen, uitvoer in `simulatie_output.csv`.
- **Integraties**: Auth0 voor authenticatie, Stripe voor betalingen, Gmail voor e-mails.
- **Uitdagingen**:
  - Nauwkeurige fietsherverdeling door transporteurs.
  - Optimalisatie van queries voor grote datasets.
  - Integratie van externe diensten (Auth0, Stripe).
  - Responsieve, meertalige UI.
- **Toekomstige verbeteringen**:
  - Real-time fietstracking op kaarten.
  - Geavanceerde stationsanalyse.
  - Simulatieverbetering met verkeersgegevens.

## Licentie
Zie `LICENSE` voor licentievoorwaarden.