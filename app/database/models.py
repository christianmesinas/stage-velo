from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, DECIMAL, create_engine
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Usertable(Base):
    __tablename__ = "inlog_gegevens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True)
    email = Column(String, unique=True)
    name = Column(String)
    profile_picture = Column(String)

    voornaam = Column(String)
    achternaam = Column(String)
    telefoonnummer = Column(String)
    titel = Column(String)
    abonnement = Column(String, default="Geen abonnement")
    taal = Column(String, default="nl")
    darkmode = Column(String, default="False")

    @classmethod
    def get_or_create(cls, db, user_id, email, name, profile_picture):
        user = db.query(cls).filter_by(user_id=user_id).first()
        if not user:
            user = cls(user_id=user_id, email=email, name=name, profile_picture=profile_picture)
            db.add(user)
            db.commit()
        return user

    def set_abonnement(self, db, new_type):
        self.abonnement = new_type
        db.commit()

class Gebruiker(Base):
    __tablename__ = 'gebruikers'

    # De ID wordt automatisch gegenereerd
    id = Column(Integer, primary_key=True)
    voornaam = Column(String)
    achternaam = Column(String)
    email = Column(String)
    abonnementstype = Column(String)
    registratie_datum = Column(DateTime, default=datetime.utcnow)
    postcode = Column(String)

    geschiedenis = relationship('Geschiedenis', back_populates='gebruiker')

class Station(Base):
    __tablename__ = 'stations'

    id = Column(Integer, primary_key=True)  # autoincrement zorgt voor automatische generatie
    naam = Column(String)
    straat = Column(String)
    postcode = Column(String)
    latitude = Column(DECIMAL)
    longitude = Column(DECIMAL)
    capaciteit = Column(Integer)
    status = Column(String)
    free_slots = Column(Integer)
    parked_bikes = Column(Integer)

    start_geschiedenis = relationship('Geschiedenis', foreign_keys='Geschiedenis.start_station_id', back_populates='start_station')
    end_geschiedenis = relationship('Geschiedenis', foreign_keys='Geschiedenis.eind_station_id', back_populates='end_station')


class Fiets(Base):
    __tablename__ = 'fietsen'

    id = Column(Integer, primary_key=True)  # autoincrement voor automatische generatie
    station_id = Column(Integer, ForeignKey('stations.id'))
    status = Column(String)

    geschiedenis = relationship('Geschiedenis', back_populates='fiets')


class Geschiedenis(Base):
    __tablename__ = 'geschiedenis'

    id = Column(Integer, primary_key=True, autoincrement=True)  # autoincrement voor automatische generatie
    gebruiker_id = Column(Integer, ForeignKey('gebruikers.id'))
    fiets_id = Column(Integer, ForeignKey('fietsen.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    bike_id = Column(Integer, ForeignKey('bikes.id'))
    start_station_id = Column(Integer, ForeignKey('stations.id'))
    eind_station_id = Column(Integer, ForeignKey('stations.id'))
    starttijd = Column(DateTime, default=datetime.utcnow)
    eindtijd = Column(DateTime)
    duur_minuten = Column(DECIMAL)
    prijs = Column(DECIMAL)

    user = relationship('User', back_populates='rentals')
    bike = relationship('Bike', back_populates='rentals')
    start_station = relationship('Station', foreign_keys=[start_station_id], back_populates='start_rentals')
    end_station = relationship('Station', foreign_keys=[eind_station_id], back_populates='end_rentals')

class BikeLocation(Base):
    __tablename__ = 'bike_locations'

    bike_id = Column(Integer, ForeignKey('bikes.id'), primary_key=True)
    station_id = Column(Integer, ForeignKey('stations.id'), primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    bike = relationship('Bike', back_populates='bike_locations')
    station = relationship('Station', back_populates='bike_locations')
