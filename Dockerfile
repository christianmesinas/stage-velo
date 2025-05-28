# Gebruik een lichte Python image
FROM python:3.13-slim

# Werkmap in de container
WORKDIR /app

# Kopieer requirements en installeer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopieer alle overige bestanden
COPY . .

# Start de app
CMD ["python", "app.py"]

# Start de simulatie
CMD ["python", "app/simulation/simulation.py"]


