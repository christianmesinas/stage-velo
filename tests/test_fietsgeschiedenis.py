import unittest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# 📦 Voeg de rootmap toe zodat 'tests' importeerbaar wordt
sys.path.append(os.path.abspath("."))

# ✅ Importeer modellen uit test_models
from tests.test_models import Gebruiker, Station, Fiets, Geschiedenis, Base

# 🔧 In-memory SQLite database voor unittests
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(bind=engine)

class TestFietsGeschiedenis(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(engine)
        self.db = TestingSessionLocal()

        self.gebruiker = Gebruiker(
            voornaam="Test",
            achternaam="Gebruiker",
            email="test@fiets.be",
            abonnementstype="Maand",
            postcode="2000"
        )
        self.db.add(self.gebruiker)
        self.db.commit()
        self.db.refresh(self.gebruiker)

        self.station1 = Station(
            naam="Station A", straat="Straat A", postcode="2000",
            latitude=51.2, longitude=4.4, capaciteit=20,
            status="Actief", free_slots=5, parked_bikes=15
        )
        self.station2 = Station(
            naam="Station B", straat="Straat B", postcode="2018",
            latitude=51.3, longitude=4.5, capaciteit=20,
            status="Actief", free_slots=3, parked_bikes=17
        )
        self.db.add_all([self.station1, self.station2])
        self.db.commit()

        self.fiets = Fiets(
            station_id=self.station1.id,
            status="Actief"
        )
        self.db.add(self.fiets)
        self.db.commit()
        self.db.refresh(self.fiets)

        self.rit = Geschiedenis(
            gebruiker_id=self.gebruiker.id,
            fiets_id=self.fiets.id,
            start_station_id=self.station1.id,
            eind_station_id=self.station2.id,
            starttijd=datetime.utcnow() - timedelta(minutes=30),
            eindtijd=datetime.utcnow(),
            duur_minuten=30,
            prijs=1.75
        )
        self.db.add(self.rit)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=engine)

    def test_geschiedenis_ophalen(self):
        geschiedenis = self.db.query(Geschiedenis).filter_by(gebruiker_id=self.gebruiker.id).all()

        print("\n📋 Opgehaalde fietsgeschiedenis:")
        for rit in geschiedenis:
            print(
                f"  - Rit ID: {rit.id} | Fiets ID: {rit.fiets_id} | "
                f"Van station {rit.start_station_id} → Naar {rit.eind_station_id} | "
                f"Duur: {rit.duur_minuten} min | Prijs: €{rit.prijs}"
            )

        self.assertEqual(len(geschiedenis), 1)
        self.assertEqual(geschiedenis[0].prijs, 1.75)
        self.assertEqual(geschiedenis[0].duur_minuten, 30)

        print("✅ Fietsgeschiedenis correct opgehaald.")

if __name__ == '__main__':
    unittest.main(verbosity=2)
