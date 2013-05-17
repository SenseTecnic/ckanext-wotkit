import requests
import sys
import time
import sensetecnic

DATA_GET_URI = 'https://api.jcdecaux.com/vls/v1/stations?apiKey=005c91663949e681c192e1f53a3499ab642a682a'
SENSOR_POST_URI = 'http://127.0.0.1:8080/api/sensors/daniel.velib-bicycle-avail/data'
SENSOR_TIME_DELAY = 60
WOTKIT_KEY_USER = '9c7158f02d16f68b'
WOTKIT_KEY_PASS = '85e0753e41b709d1'
SENSOR_NAME = 'velib-bicycle-avail'

def updateWotkit():
    
    try:
        r = requests.get(DATA_GET_URI)
        j = r.json()
        
        value = sum((v['available_bikes'] for v in j))
        
        wotkit_data = {'value': value}
        sensetecnic.sendData(SENSOR_NAME, None, None, wotkit_data)    
        return [SENSOR_NAME]
    except Exception as e:
        sys.stderr.write(str(e))
