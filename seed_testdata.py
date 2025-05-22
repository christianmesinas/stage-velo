# seed_testdata.py

import os
# Overschrijf Docker connectie met lokale connectie
os.environ["DATABASE_URL"] = "postgresql://admin:Velo123@localhost:5432/velo_community"

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from app.database.models import Gebruiker, Usertable, Fiets, Station, Geschiedenis
from app.database.session import SessionLocal
from datetime import datetime
