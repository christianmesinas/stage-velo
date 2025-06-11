#### Velocity Velo

### Reflectie project

Dit project dat we "Velocity Velo" noemen is een simulatie van een fietsdeelsysteem, het is gebaseerd op Velo Antwerpen.
Het bootst de werking na van gebruikers die ritten maken tussen verschillende stations met beschikbare fietsen.
Er is ook een gebruiker kant waar men een abonnement kan kopen en fietsen kan ontlenen en terugzetten. De focus van 
de app blijft wel op de admin kant en transporteur kant. 


## FUNCTIONALITEIT

# Gebruiker:
    - Inloggen/registreren
    - Aanschaffen abonnementen
    - Ontlenen/terugzetten fietsen
    - Bekijken geschiedenis

# Admin:
    - Inloggen adminportaal
    - Simuleren realistische scenario (versnellen a.d.h.v. aantal dagen)
    - Per gebruiker verbruik bekijken
    - Meest gebruikte stations vinden
    - Drukste uur van gebruik vinden
    - Live Data bekijken (real time api)
    - Dummy data genereren voor virtuele simulatie

# transporteurs:
    - Inloggen transporteurPortaal
    - Bekijken welke stations fietsen nodig hebben 
    - Fietsen verplaatsen van station naar een andere station
    - Fietsen die defect zijn herstellen en toewijzen aan een station


## COMPONENTEN/TECHNISCHE WERKING:

de app bestaat uit meerdere componenten

# Programmeertaal + web framework:
    - Python
    - Javascript
    - Flask
    - api

# Database:
    - PostgreSQL
    - SQLAlchemy

# CCNTAINERISATIE:
    - Docker
    - Docker Compose

# AUTHENTICATIE:
    - Auth0


## GEDETAILLEERDE TECHINSCHE WERKING: 

# Python + Flask:
    Python 
        - Regelt de hoofdtaken van de programma, zoals simuleren van de fietsritten, 
          genereren gebruikers/fietsen en communicatie met de database, dit gebeurd allemaal met Python.
    
    Flask  
        - Regelt de structuur van de webapplicatie (routes, views, templates)

    Javascript 
        - Javascript wordt gebruikt aan de frontend zijde voor dynamisch gedrag in de browser. bevoorbeeld: knoppen, modals, grafieken


# Database:
    PostgreSQL
        - Relationele SQL-database waarin gegevens zoals de gebruikers, fietsen, stations en geschiedenis worden opgeslagen.
          Elke entiteit is een aparte tabel dus er is een tabel (gebruikers, fietsen, stations, geschiedenis)
          Er zijn ook andere tabellen waar abonnementen, defectmeldingen en contactberichten. maar die zijn secundair.
    
    SQLAlchemy
        - SQLAlcheny zorgt ervoor dat we met in plaats van puur SQL entiteiten kunnen werken met python objecten zoals gebruikers,fietsen en geschiedenis


# Containerisatie:
    Docker
        - Dcokerfile beschrijft stap voor stap hoe onze image gebouwd wordt. 
    
    Docker Compose
        - in de docker compose definieren we meerdere services tegelijkertijd. in ons geval is dit de Database en de App zelf die daar worden gedefinieerd


# Authenticatie:
    Auth0
        - Auth0 is een externe provider van authenticatie voor je webapp. dit zorgt voor aanmelden met google , facebook. etc...


## FUNCTIES DIE ER NIET BIJ ZIJN:
    Simulatie starten via terminal
        - We hebben dit geprobeerd te implementeren in de 2de sprint. Na een paar onsuccesvolle pogingen hadden we besloten om deze functie uit te stellen voor later.
          We zijn het hierna vergeten om het te implementeren op het einde.
    