import requests

BASE_URL = "https://api.citybik.es/v2/networks/velo-antwerpen"
HEADERS = {}

#functie om alle data op te halen van de api
def get_info():
    params = {} #we halen alles op dus er zijn geen queries vereist
    response = requests.get(BASE_URL, headers=HEADERS, params=params)
    #controle of api call succesvol is.
    if response.status_code == 200:
        data = response.json() #parse de JSON-response
        stations = data['network']['stations'] #haal de lijst van de stations op
        #een lijst maken waar we enkel de nodige info uit de rauwe data halen en in een lijst results steken
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
                    'status': station['extra']['status'],
                }

            }
            for station in stations
        ]
        return result
    else:
        #Indien de API faalt, return None
        return None


stations_info = get_info()

#functie om gestructureerde lijst te krijgen van alle stations.
def get_alle_stations():
    if stations_info:
        stations = []
        for station in stations_info:
            free_bikes = station.get('free_bikes', 0) #aantal vrije fietsen
            empty_slots = station.get('empty_slots', 0) #aantal lege plaatsen

            capaciteit = free_bikes + empty_slots #totale capaciteit van het station

            #voeg gestructureerde station-informatie toe aan de lijst
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
        return stations # return de volledige lijst van stations


#Functie om info te verzamelen over de lege plaatsen per station
def zoek_lege_slots():
    stations = []
    station_met_slots = []
    #Bouw een lijst van tuples met info over lege slots
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



