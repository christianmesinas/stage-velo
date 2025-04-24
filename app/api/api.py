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
if stations_info:
    for station in stations_info:
        print(f"ID: {station['id']}")
        print(f"Naam: {station['name']}")
        print(f"Locatie: {station['location']['latitude']}, {station['location']['longitude']}")
        print(f"heeft zoveel vrije fietsen: {station['free_bikes']}")
        print(f"heeft zoveel vrije plaatsen: {station['empty_slots']}")
        print(f"bij adress: {station['extra']['adress']}")
        print("-" * 50)