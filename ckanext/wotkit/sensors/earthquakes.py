import requests
import sys
import time
import sensetecnic

DATA_GET_URI = 'http://earthquake.usgs.gov/earthquakes/feed/v0.1/summary/1.0_hour.geojson'
SENSOR_POST_URI = 'http://127.0.0.1:8080/api/sensors/daniel.earthquakes/data'
SENSOR_TIME_DELAY = 600
WOTKIT_KEY_USER = '9c7158f02d16f68b'
WOTKIT_KEY_PASS = '85e0753e41b709d1'

SENSOR_NAME = "earthquakes"

def updateWotkit():

    try:
        r = requests.get(DATA_GET_URI)
        j = r.json()
        
        strongest = 0.0
        for q in [q for q in j['features'] ]:
            if strongest <= float(q['properties']['mag']):
                strongest = float(q['properties']['mag'])
                lat = q['geometry']['coordinates'][1]
                lng = q['geometry']['coordinates'][0]
        
        if strongest > 0:
            wotkit_data = {'value': strongest, 'lat': lat, 'lng': lng}
            sensetecnic.sendData(SENSOR_NAME, None, None, wotkit_data)
            print "Sent data to wotkit " + str(wotkit_data)
            return [SENSOR_NAME]
            
    except Exception as e:
        sys.stderr.write(str(e))
    
