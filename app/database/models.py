from email.charset import Charset

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, DECIMAL
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# 👤 Ingelogde gebruikersgegevens (auth0-profiel)
class Usertable(Base):
    __tablename__ = "inlog_gegevens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True)
    email = Column(String, unique=True)
    name = Column(String)
    profile_picture = Column(String, nullable=False, default="img/default.png")


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
            user = cls(
                user_id=user_id,
                email=email,
                name=name,
                profile_picture=profile_picture
            )
            db.add(user)
            db.commit()
        return user

    def set_abonnement(self, db, new_type):
        self.abonnement = new_type
        db.commit()

# 👤 Gebruikerprofielen met geschiedenis
class Gebruiker(Base):
    __tablename__ = "gebruikers"

    id = Column(Integer, primary_key=True)
    voornaam = Column(String)
    achternaam = Column(String)
    email = Column(String)
    abonnementstype = Column(String)
    postcode = Column(String)

    geschiedenis = relationship("Geschiedenis", back_populates="gebruiker")

# 📍 Fietsstations
class Station(Base):
    __tablename__ = "stations"

    id = Column(String(32), primary_key=True)
    naam = Column(String, unique=True)
    straat = Column(String)
    latitude = Column(DECIMAL)
    longitude = Column(DECIMAL)
    capaciteit = Column(Integer)
    status = Column(String)
    free_slots = Column(Integer)
    parked_bikes = Column(Integer)

    start_geschiedenis = relationship(
        "Geschiedenis",
        foreign_keys="Geschiedenis.start_station_naam",
        back_populates="start_station"
    )
    end_geschiedenis = relationship(
        "Geschiedenis",
        foreign_keys="Geschiedenis.eind_station_naam",
        back_populates="end_station"
    )

# 🚲 Fietsen
class Fiets(Base):
    __tablename__ = "fietsen"

    id = Column(Integer, primary_key=True)
    station_naam = Column(String, ForeignKey("stations.naam"))
    status = Column(String)

    geschiedenis = relationship("Geschiedenis", back_populates="fiets")

# 📜 Geschiedenis van ritten
class Geschiedenis(Base):
    __tablename__ = "geschiedenis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gebruiker_id = Column(Integer, ForeignKey("gebruikers.id"))
    fiets_id = Column(Integer, ForeignKey("fietsen.id"))
    start_station_naam = Column(String, ForeignKey("stations.naam"))
    eind_station_naam = Column(String, ForeignKey("stations.naam"))
    starttijd = Column(DateTime, default=datetime.utcnow)
    eindtijd = Column(DateTime)
    duur_minuten = Column(DECIMAL)
    prijs = Column(DECIMAL)

    gebruiker = relationship("Gebruiker", back_populates="geschiedenis")
    fiets = relationship("Fiets", back_populates="geschiedenis")
    start_station = relationship("Station", foreign_keys=[start_station_naam], back_populates="start_geschiedenis")
    end_station = relationship("Station", foreign_keys=[eind_station_naam], back_populates="end_geschiedenis")

# Defecte fietsen met probleem opslaan in de databank
class Defect(Base):
    __tablename__ = "defecten"
    id = Column(Integer, primary_key=True)
    fiets_id = Column(Integer, ForeignKey("fietsen.id"))
    probleem = Column(String)

    fiets = relationship("Fiets")


class Pas(Base):
    __tablename__ = "passen"

    id = Column(Integer, primary_key=True)
    gebruiker_id = Column(Integer, ForeignKey("inlog_gegevens.id"), nullable=False)
    soort = Column(String, nullable=False)  # dag, week, jaar
    pincode = Column(String, nullable=False)
    start_datum = Column(DateTime, default=datetime.utcnow)
    eind_datum = Column(DateTime, nullable=True)

    gebruiker = relationship("Usertable", backref="passen")


