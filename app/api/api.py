import requests
from typing import List, Dict, Optional
from datetime import datetime

# Configuratie
BASE_URL = "https://api.citybik.es/v2/networks/velo-antwerpen"
HEADERS = {"Accept": "application/json"}
TIMEOUT = 10


def fetch_bike_stations() -> Optional[List[Dict]]:
    """Haal fietsstationsdata op van de API."""
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()['network']['stations']
    except Exception as e:
        print(f"Fout bij ophalen data: {e}")
        return None


def format_station_list(stations: List[Dict]) -> str:
    """Formatteer stations als genummerde lijst."""
    result = []
    for idx, station in enumerate(stations, start=1):
        result.append(
            f"{idx}. {station['name']}\n"
            f"   Vrije fietsen: {station['free_bikes']}\n"
            f"   Vrije plaatsen: {station['empty_slots']}\n"
            f"   Adres: {station['extra']['address']}\n"
            f"   Locatie: {station['latitude']}, {station['longitude']}\n"
        )
    return "\n".join(result)


def main():
    stations = fetch_bike_stations()
    if not stations:
        print("Kon geen stations ophalen.")
        return

    print("=== VELO ANTWERPEN - BESCHIKBARE STATIONS ===")
    print(format_station_list(stations))


if __name__ == "__main__":
    main()