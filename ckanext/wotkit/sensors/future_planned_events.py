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
              {"name":"occurrence","type":"STRING","required":False,"longName":"Probability of occurrence"},
              {"name":"latfrom","type":"NUMBER","required":False,"longName":"latitude from"},
              {"name":"lngfrom","type":"NUMBER","required":False,"longName":"longitude from"},
              {"name":"latto","type":"NUMBER","required":False,"longName":"latitude to"},
              {"name":"lngto","type":"NUMBER","required":False,"longName":"longitude to"}
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
    combined_data = []
    for data in parsedXML.findAll("situationRecord"):
        wotkit_data = {}
        try:
            location = data.groupOfLocations.locationContainedInGroup.tpegpointLocation
            from_location = location.find("from")
            to_location = location.find("to")
            try:
                wotkit_data["lat"] = location.framedPoint.pointCoordinates.latitude.string
                wotkit_data["lng"] = location.framedPoint.pointCoordinates.longitude.string
                wotkit_data["latfrom"] = from_location.pointCoordinates.latitude.string
                wotkit_data["lngfrom"] = from_location.pointCoordinates.longitude.string                
                wotkit_data["latto"] = to_location.pointCoordinates.latitude.string
                wotkit_data["lngto"] = to_location.pointCoordinates.longitude.string
            except Exception as e:
                wotkit_data["lat"] = location.point.pointCoordinates.latitude.string
                wotkit_data["lng"] = location.point.pointCoordinates.longitude.string
            
            wotkit_data["value"] = data.impact.impactDetails.numberOfOperationalLanes.string
            wotkit_data["updatedtime"] = data.situationRecordVersionTime.string
            wotkit_data["restrictedlanes"] = data.impact.impactDetails.numberOfLanesRestricted.string
            wotkit_data["endtime"] = data.validity.validityTimeSpecification.overallEndTime.string
            wotkit_data["starttime"] = data.validity.validityTimeSpecification.overallStartTime.string
            wotkit_data["comment"] = data.nonGeneralPublicComment.comment.value.string
            wotkit_data["impact"] = data.impact.impactOnTraffic.string
            wotkit_data["occurrence"] = data.probabilityOfOccurrence.string
            wotkit_data["timestamp"] = sensetecnic.getWotkitTimeStamp()
            
            combined_data.append(wotkit_data)
        except Exception as e:
            log.debug("Failed to parse single traffic data: " + str(e))
    try:
        sensetecnic.sendBulkData(SENSOR_NAME, None, None, combined_data)
    except Exception as e:
        log.debug("Failed to update wotkit sensor data")
        
    return [SENSOR_NAME]

