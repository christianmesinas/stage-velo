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



class Gebruiker(Base):
    __tablename__ = 'gebruikers'

    # De ID wordt automatisch gegenereerd
    id = Column(Integer, primary_key=True)
    voornaam = Column(String)
    achternaam = Column(String)
    email = Column(String)
    abonnementstype = Column(String)
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
    start_station_id = Column(Integer, ForeignKey('stations.id'))
    eind_station_id = Column(Integer, ForeignKey('stations.id'))
    starttijd = Column(DateTime, default=datetime.utcnow)
    eindtijd = Column(DateTime)
    duur_minuten = Column(DECIMAL)

    gebruiker = relationship('Gebruiker', back_populates='geschiedenis')
    fiets = relationship('Fiets', back_populates='geschiedenis')
    start_station = relationship('Station', foreign_keys=[start_station_id], back_populates='start_geschiedenis')
    end_station = relationship('Station', foreign_keys=[eind_station_id], back_populates='end_geschiedenis')
