from bs4 import BeautifulSoup, NavigableString
import sensetecnic
import requests

import logging
log = logging.getLogger(__name__)

DATA_GET_URI = "http://hatrafficinfo.dft.gov.uk/feeds/datex/England/MatrixSignals/content.xml"
SENSOR_NAME = "matrix-signals"

def getSensorSchema():
    schema = [
              {"name":"lat","type":"NUMBER","required":False,"longName":"latitude"},
              {"name":"lng","type":"NUMBER","required":False,"longName":"longitude"},
              {"name":"value","type":"NUMBER","required":False,"longName":"Fault if 1"},
              {"name":"starttime","type":"STRING","required":False,"longName":"Status start time"},
              {"name":"updatedtime","type":"STRING","required":False,"longName":"Last updated time"},
              {"name":"locationref","type":"STRING","required":False,"longName":"DATEX2 Matrix Location Reference"},
              {"name":"matrixid","type":"STRING","required":False,"longName":"Matrix identifier"},
              {"name":"display","type":"STRING","required":False,"longName":"DATEX2 Aspect Displayed"},
              {"name":"active","type":"STRING","required":False,"longName":"Matrix Status"},
              {"name":"reason","type":"STRING","required":False,"longName":"Reason of status"}
                            ]
    return schema

def getSensorRegistration():
    sensor = {
              "name":SENSOR_NAME,
              "longName":"England Matrix Signals",
              "description":"Sensor data parsed from http://hatrafficinfo.dft.gov.uk/feeds/datex/England/MatrixSignals/content.xml",
              "latitude": "51.506178",
              "longitude": "-0.113995",
              "private":False,
              "tags":["traffic", "road"],
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
    for data in parsedXML.findAll("situationRecord"):
        wotkit_data = {}
        try:
            wotkit_data["active"] = data.validity.validityStatus.string
            wotkit_data["value"] = 0 if wotkit_data["active"] == "active" else 1 
            wotkit_data["updatedtime"] = data.situationRecordVersionTime.string
            wotkit_data["starttime"] = data.validity.validityTimeSpecification.overallStartTime.string
            wotkit_data["locationref"] = data.groupOfLocations.locationContainedInGroup.predefinedLocationReference.string
            wotkit_data["matrixid"] = data.matrixIdentifier.string
            wotkit_data["display"] = data.aspectDisplayed.string
            wotkit_data["reason"] = data.reasonForSetting.value.string

        except Exception as e:
            log.debug("Failed to parse single traffic data: " + str(e))
        try:
            sensetecnic.sendData(SENSOR_NAME, None, None, wotkit_data)
        except Exception as e:
            log.debug("Failed to update wotkit sensor data")
        
    return [SENSOR_NAME]

