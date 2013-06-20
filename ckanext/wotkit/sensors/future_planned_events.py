from bs4 import BeautifulSoup, NavigableString
import sensetecnic
import requests

import highways_agency_common 
import logging
log = logging.getLogger(__name__)

DATA_GET_URI = "http://hatrafficinfo.dft.gov.uk/feeds/datex/England/FuturePlanned/content.xml"
SENSOR_NAME = "future-planned-events"

def getSensorRegistration():
    sensor = {
              "name":SENSOR_NAME,
              "longName":"Future planned events that affect traffic",
              "description":"Sensor data parsed from http://hatrafficinfo.dft.gov.uk/feeds/datex/England/FuturePlanned/content.xml",
              "latitude": "51.506178",
              "longitude": "-0.113995",
              "private":False,
              "tags":["traffic", "road"],
              "fields":highways_agency_common.getEventSensorSchema()
              }
    return sensor
    

def checkSensorExist():
    sensor_registration_schema = getSensorRegistration()
    try:
        sensetecnic.checkAndRegisterSensor(sensor_registration_schema)
    except Exception as e:
        log.warning(str(e))
        log.warning("Failed to register sensor %s. " % SENSOR_NAME)


def updateWotkit():
    checkSensorExist()
    
    combined_data = highways_agency_common.retrieveCommonEventFormat(DATA_GET_URI)

    try:
        sensetecnic.sendBulkData(SENSOR_NAME, None, None, combined_data)
    except Exception as e:
        log.debug("Failed to update wotkit sensor data")
        
    return [SENSOR_NAME]

