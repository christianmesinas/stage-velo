import requests
from app.simulation.simulation import genereer_fietsen

BASE_URL = "https://api.citybik.es/v2/networks/velo-antwerpen"
HEADERS = {}

def get_info(simulated=False):
    params = {}
    response = requests.get(BASE_URL, headers=HEADERS, params=params)
    if response.status_code == 200:
        data = response.json()
        stations = data['network']['stations']

        if simulated:
            simulated_stations = genereer_fietsen()
            simulated_lookup = {s['id']: s for s in simulated_stations}

        result = [
            {
                'id': station['id'],
                'name': station['name'],
                'location': {
                    'latitude': station['latitude'],
                    'longitude': station['longitude']
                },
                'free_bikes': simulated_lookup.get(station['id'], {}).get('free_bikes', station['free_bikes']),
                'empty_slots': simulated_lookup.get(station['id'], {}).get('empty_slots', station['empty_slots']),
                'extra': {
                    'adress': station['extra']['address'],
                    'status': station['extra']['status'],
                }

            }
            for station in stations
        ]
        return result
    else:
        return None


stations_info = get_info()

simulated_stations_info = get_info(simulated=True)

def get_alle_stations():
    if stations_info:
        stations = []
        for station in stations_info:
            free_bikes = station.get('free_bikes', 0)
            empty_slots = station.get('empty_slots', 0)

            capaciteit = free_bikes + empty_slots

            stations.append((
                station['id'],
                station['name'],
                station['extra']['adress'],
                station['extra']['status'],
                station['location']['latitude'],
                station['location']['longitude'],
                free_bikes,
                empty_slots,
                capaciteit,
            ))
        return stations

def zoek_lege_slots():
    stations = []
    station_met_slots = []
    for station in stations_info:
        stations.append((
            station['id'],
            station['name'],
            station['extra']['adress'],
            station['empty_slots']
        ))
    for station in stations:
        station_met_slots.append(())


#lege_slots = zoek_lege_slots()
#alle_stations = get_alle_stations()


