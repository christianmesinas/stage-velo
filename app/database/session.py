from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from os import getenv
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("❌ DATABASE_URL ontbreekt. Controleer je .env-bestand.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 👇 Dit zorgt dat je tabellen aangemaakt worden
from app.database.models import Base  # of: from .models import Base als je in hetzelfde pakket zit
Base.metadata.create_all(bind=engine)
