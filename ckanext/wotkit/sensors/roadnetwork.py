from bs4 import BeautifulSoup, NavigableString
import sensetecnic
import requests


import logging
log = logging.getLogger(__name__)

DATA_GET_URI = "http://hatrafficinfo.dft.gov.uk/feeds/datex/England/JourneyTimeData/content.xml"
SENSOR_NAME = "highway-traffic"

def getSensorSchema():
    schema = [
              {"name":"lat","type":"NUMBER","required":False,"longName":"latitude"},
              {"name":"lng","type":"NUMBER","required":False,"longName":"longitude"},
              {"name":"value","type":"NUMBER","required":False,"longName":"Expected Traffic time", "units":"seconds"},
              {"name":"idealtime","type":"NUMBER","required":False,"longName":"Ideal Traffic time (no traffic)", "units":"seconds"},
              {"name":"historictime","type":"NUMBER","required":False,"longName":"Historical Traffic time", "units":"seconds"},
              {"name":"locationref","type":"STRING","required":False,"longName":"DATEX2 Traffic Location Reference"},
              {"name":"sourceid","type":"NUMBER","required":False,"longName":"DATEX2 Traffic Link ID"},
              {"name":"recordedtime","type":"STRING","required":False,"longName":"Timestamp of traffic record"},
              
              ]
    return schema

def getSensorRegistration():
    sensor = {
              "name":SENSOR_NAME,
              "longName":"Amsterdam Wind Data",
              "description":"Sensor taken from openweathermap.org of wind data in Amsterdam",
              "latitude": "51.506178",
              "longitude": "-0.113993",
              "private":False,
              "tags":["traffic", "highway", "road"],
              "fields":getSensorSchema()
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
    
    r = requests.get(DATA_GET_URI)
    text = r.text
    parsedXML = BeautifulSoup(text, "xml")
    for data in parsedXML.findAll("elaboratedData"):
        wotkit_data = {}
        try:
            wotkit_data["sourceid"] = data.sourceInformation.sourceIdentification.string
            wotkit_data["recordedtime"] = data.basicDataValue.time.string
            wotkit_data["locationref"] = data.basicDataValue.affectedLocation.locationContainedInGroup.predefinedLocationReference.string
            wotkit_data["value"] = data.basicDataValue.travelTime.string
            wotkit_data["idealtime"] = data.basicDataValue.freeFlowTravelTime.string
            wotkit_data["historictime"] = data.basicDataValue.normallyExpectedTravelTime.string
        except Exception as e:
            log.debug("Failed to parse traffic info" + str(e))
        try:
            sensetecnic.sendData(SENSOR_NAME, None, None, wotkit_data)
        except Exception as e:
            log.debug("Failed to update wotkit sensor data")
        
    return [SENSOR_NAME]
