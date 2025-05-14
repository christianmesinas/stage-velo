from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Usertable(Base):
    __tablename__ = "inlog_gegevens"

    user_id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    profile_picture = Column(String, nullable=False, default="img/default.png")

    @classmethod
    def get_or_create(cls, db, user_id, email, name, profile_picture):
        user = db.query(cls).filter_by(user_id=user_id).first()
        if not user:
            user = cls(user_id=user_id, email=email, name=name, profile_picture=profile_picture)
            db.add(user)
            db.commit()
        return user



class User(Base):
    __tablename__ = 'users'

    # De ID wordt automatisch gegenereerd
    id = Column(Integer, primary_key=True, autoincrement=True)  # autoincrement zorgt ervoor dat de ID automatisch verhoogt
    voornaam = Column(String)
    achternaam = Column(String)
    email = Column(String)
    abonnementstype = Column(String)
    registratie_datum = Column(DateTime, default=datetime)
    postcode = Column(String)
    stad = Column(String)

    rentals = relationship('Rental', back_populates='user')

class Station(Base):
    __tablename__ = 'stations'

    id = Column(Integer, primary_key=True, autoincrement=True)  # autoincrement zorgt voor automatische generatie
    naam = Column(String)
    adres = Column(String)
    latitude = Column(DECIMAL)
    longitude = Column(DECIMAL)
    capaciteit = Column(Integer)
    free_slots = Column(Integer)
    parked_bikes = Column(Integer)

    bike_locations = relationship('BikeLocation', back_populates='station')
    start_rentals = relationship('Rental', foreign_keys='Rental.start_station_id', back_populates='start_station')
    end_rentals = relationship('Rental', foreign_keys='Rental.eind_station_id', back_populates='end_station')

class Bike(Base):
    __tablename__ = 'bikes'

    id = Column(Integer, primary_key=True, autoincrement=True)  # autoincrement voor automatische generatie
    type = Column(String)
    status = Column(String)

    rentals = relationship('Rental', back_populates='bike')
    maintenance = relationship('Maintenance', back_populates='bike')
    bike_locations = relationship('BikeLocation', back_populates='bike')

class Rental(Base):
    __tablename__ = 'rentals'

    id = Column(Integer, primary_key=True, autoincrement=True)  # autoincrement voor automatische generatie
    user_id = Column(Integer, ForeignKey('users.id'))
    bike_id = Column(Integer, ForeignKey('bikes.id'))
    start_station_id = Column(Integer, ForeignKey('stations.id'))
    eind_station_id = Column(Integer, ForeignKey('stations.id'))
    starttijd = Column(DateTime, default=datetime.utcnow)
    eindtijd = Column(DateTime)
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

class Maintenance(Base):
    __tablename__ = 'maintenance'

    id = Column(Integer, primary_key=True, autoincrement=True)  # autoincrement zorgt voor automatische generatie
    bike_id = Column(Integer, ForeignKey('bikes.id'))
    datum = Column(DateTime, default=datetime.utcnow)
    beschrijving = Column(String)
    status = Column(String)

    bike = relationship('Bike', back_populates='maintenance')



