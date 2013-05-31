from bs4 import BeautifulSoup, NavigableString
import sensetecnic
import requests


import logging
log = logging.getLogger(__name__)

DATA_GET_URI = "http://hatrafficinfo.dft.gov.uk/feeds/datex/England/FuturePlanned/content.xml"
SENSOR_NAME = "future-planned-events"

def getSensorSchema():
    schema = [
              {"name":"lat","type":"NUMBER","required":False,"longName":"latitude"},
              {"name":"lng","type":"NUMBER","required":False,"longName":"longitude"},
              {"name":"value","type":"NUMBER","required":False,"longName":"Operational Lanes"},
              {"name":"restrictedlanes","type":"NUMBER","required":False,"longName":"Restricted Lanes"},
              {"name":"endtime","type":"STRING","required":False,"longName":"End Time"},
              {"name":"starttime","type":"STRING","required":False,"longName":"Start Time"},
              {"name":"recordedtime","type":"STRING","required":False,"longName":"Recorded Time"},
              {"name":"comment","type":"STRING","required":False,"longName":"Comments"},
              {"name":"impact","type":"STRING","required":False,"longName":"Impact on traffic"},
              {"name":"occurrence","type":"STRING","required":False,"longName":"Probability of occurrence"}
              ]
    return schema

def getSensorRegistration():
    sensor = {
              "name":SENSOR_NAME,
              "longName":"Future planned events that affect traffic",
              "description":"Sensor data parsed from http://hatrafficinfo.dft.gov.uk/feeds/datex/England/FuturePlanned/content.xml",
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
            wotkit_data["lat"] = data.groupOfLocations.locationContainedInGroup.tpegpointLocation.framedPoint.pointCoordinates.latitude.string
            wotkit_data["lng"] = data.groupOfLocations.locationContainedInGroup.tpegpointLocation.framedPoint.pointCoordinates.longitude.string
            wotkit_data["value"] = data.impact.impactDetails.numberOfOperationalLanes.string
            wotkit_data["updatedtime"] = data.situationRecordVersionTime.string
            wotkit_data["restrictedlanes"] = data.impact.impactDetails.numberOfLanesRestricted.string
            wotkit_data["endtime"] = data.validity.validityTimeSpecification.overallEndTime.string
            wotkit_data["starttime"] = data.validity.validityTimeSpecification.overallStartTime.string
            wotkit_data["comment"] = data.nonGeneralPublicComment.comment.value.string
            wotkit_data["impact"] = data.impact.impactOnTraffic.string
            wotkit_data["occurrence"] = data.probabilityOfOccurrence.string
            
        except Exception as e:
            log.debug("Failed to parse single traffic data: " + str(e))
        try:
            sensetecnic.sendData(SENSOR_NAME, None, None, wotkit_data)
        except Exception as e:
            log.debug("Failed to update wotkit sensor data")
        
    return [SENSOR_NAME]

