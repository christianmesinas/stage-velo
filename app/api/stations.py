import requests
import csv
import os
from pathlib import Path

BASE_URL = "https://api.citybik.es/v2/networks/velo-antwerpen"

def clean_text_field(text):
    """Verwerk tekstvelden om speciale tekens te vervangen en CSV-compatibel te maken."""
    if text is None:
        return ""
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("\n", " ").replace("\t", " ")
    text = text.replace('"', '""')
    return text.strip()

def get_stations_info():
    """Haal stationsgegevens op van de API"""
    try:
        response = requests.get(BASE_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data['network']['stations']
    except requests.exceptions.RequestException as e:
        print(f"Fout bij ophalen data: {e}")
        return None

def process_stations_data(raw_stations):
    """Verwerk ruwe stationsdata naar bruikbaar formaat"""
    if not raw_stations:
        return None

    processed_stations = []
    for station in raw_stations:
        try:
            free_bikes = station.get('free_bikes', 0)
            empty_slots = station.get('empty_slots', 0)

            processed_stations.append((
                clean_text_field(station['id']),
                clean_text_field(station['name']),
                clean_text_field(station['extra']['address']),
                station['latitude'],
                station['longitude'],
                free_bikes + empty_slots,  # capaciteit
                empty_slots,               # free_slots
                free_bikes                 # parked_bikes
            ))
        except KeyError as e:
            print(f"Ontbrekend veld in station data: {e}")
            continue

    return processed_stations

def save_to_csv(stations_data, filename='stations.csv'):
    if not stations_data:
        print("Geen data om op te slaan")
        return False

    try:
        filepath = Path(__file__).parent / filename

        with open(filepath, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow([
                'id', 'naam', 'adres',
                'latitude', 'longitude',
                'capaciteit', 'free_slots',
                'parked_bikes'
            ])
            writer.writerows(stations_data)

        print(f"CSV succesvol opgeslagen in: {filepath}")
        print(f"Bestandsgrootte: {os.path.getsize(filepath)} bytes")
        return True
    except Exception as e:
        print(f"Fout bij opslaan CSV: {e}")
        return False

def main():
    # Stap 1: Data ophalen
    raw_stations = get_stations_info()

    # Stap 2: Data verwerken
    stations_data = process_stations_data(raw_stations)

    if not stations_data:
        print("Geen stationsgegevens beschikbaar")
        return

    # Stap 3: Opslaan als CSV
    if save_to_csv(stations_data):
        print(f"Aantal stations verwerkt: {len(stations_data)}")
    else:
        print("Opslaan mislukt")

if __name__ == "__main__":
    main()