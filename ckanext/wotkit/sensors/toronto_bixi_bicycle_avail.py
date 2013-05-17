from lxml import etree
import requests
import sys
import time
import sensetecnic

BIXI_GET_URI = 'http://toronto.bixi.com/data/bikeStations.xml'
SENSOR_POST_URI = 'http://127.0.0.1:8080/api/sensors/daniel.toronto-bixi-bicycle-avail/data'
SENSOR_TIME_DELAY = 60
WOTKIT_KEY_USER = '9c7158f02d16f68b'
WOTKIT_KEY_PASS = '85e0753e41b709d1'

SENSOR_NAME = 'toronto-bixi-bicycle-avail'
def updateWotkit():
    
    try:
        r = requests.get(BIXI_GET_URI, stream=True)
        xml = etree.parse(r.raw)
        value = sum((int(x) for x in xml.xpath('/stations/station/nbBikes/text()')))
        
        wotkit_data = {'value': value}
        sensetecnic.sendData(SENSOR_NAME, None, None, wotkit_data)
        return [SENSOR_NAME]
    except Exception as e:
        sys.stderr.write(str(e))
    
