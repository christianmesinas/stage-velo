import requests

BASE_URL = "https://api.citybik.es/v2/networks/velo-antwerpen"
HEADERS = {}

def get_info():
    params = {}
    response = requests.get(BASE_URL, headers=HEADERS, params=params)
    if response.status_code == 200:
        data = response.json()
        stations = data['network']['stations']
        result = [
            {
                'id': station['id'],
                'name': station['name'],
                'location': {
                    'latitude': station['latitude'],
                    'longitude': station['longitude']
                },
                'free_bikes': station['free_bikes'],
                'empty_slots': station['empty_slots'],
                'extra': {
                    'adress': station['extra']['address'],
                }

            }
            for station in stations
        ]
        return result
    else:
        return None


stations_info = get_info()

def print_alle_date():
    if stations_info:
        stations = []
        for station in stations_info:
            print(f"ID: {station['id']}")
            print(f"Naam: {station['name']}")
            print(f"Locatie: {station['location']['latitude']}, {station['location']['longitude']}")
            print(f"heeft zoveel vrije fietsen: {station['free_bikes']}")
            print(f"heeft zoveel vrije plaatsen: {station['empty_slots']}")
            print(f"bij adress: {station['extra']['adress']}")
            print("-" * 50)
            stations.append({station['id'], station['name'], station['location']['latitude'], station['location']['longitude'], station['free_bikes'],station['empty_slots'], station['extra']['adress']})
    return stations

def zoek_lege_slots():
    for station in stations_info:
        if station['empty_slots'] > 0:
            print(f"er zijn {station['empty_slots']} lege slots bij de station op {station['extra']['adress']}")

data = print_alle_date()
print(data)