from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, DECIMAL
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

# Basis voor SQLAlchemy-modellen
Base = declarative_base()

# 👤 Gebruikerstabellen met relatie naar geschiedenis
class Gebruiker(Base):
    __tablename__ = "gebruikers"

    id = Column(Integer, primary_key=True)
    voornaam = Column(String)
    achternaam = Column(String)
    email = Column(String)
    abonnementstype = Column(String)
    postcode = Column(String)

    geschiedenis = relationship("Geschiedenis", back_populates="gebruiker")

# 📍 Stations
class Station(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True)
    naam = Column(String)
    straat = Column(String)
    postcode = Column(String)
    latitude = Column(DECIMAL)
    longitude = Column(DECIMAL)
    capaciteit = Column(Integer)
    status = Column(String)
    free_slots = Column(Integer)
    parked_bikes = Column(Integer)

    start_geschiedenis = relationship(
        "Geschiedenis",
        foreign_keys="Geschiedenis.start_station_id",
        back_populates="start_station"
    )
    end_geschiedenis = relationship(
        "Geschiedenis",
        foreign_keys="Geschiedenis.eind_station_id",
        back_populates="end_station"
    )

# 🚲 Fietsen
class Fiets(Base):
    __tablename__ = "fietsen"

    id = Column(Integer, primary_key=True)
    station_id = Column(Integer, ForeignKey("stations.id"))
    status = Column(String)

    geschiedenis = relationship("Geschiedenis", back_populates="fiets")

# 📜 Geschiedenis van ritten
class Geschiedenis(Base):
    __tablename__ = "geschiedenis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gebruiker_id = Column(Integer, ForeignKey("gebruikers.id"))
    fiets_id = Column(Integer, ForeignKey("fietsen.id"))
    start_station_id = Column(Integer, ForeignKey("stations.id"))
    eind_station_id = Column(Integer, ForeignKey("stations.id"))
    starttijd = Column(DateTime, default=datetime.utcnow)
    eindtijd = Column(DateTime)
    duur_minuten = Column(DECIMAL)
    prijs = Column(DECIMAL)

    gebruiker = relationship("Gebruiker", back_populates="geschiedenis")
    fiets = relationship("Fiets", back_populates="geschiedenis")
    start_station = relationship("Station", foreign_keys=[start_station_id], back_populates="start_geschiedenis")
    end_station = relationship("Station", foreign_keys=[eind_station_id], back_populates="end_geschiedenis")
