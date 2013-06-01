from bs4 import BeautifulSoup, NavigableString
import sensetecnic
import requests

import logging
log = logging.getLogger(__name__)

DATA_GET_URI = "http://hatrafficinfo.dft.gov.uk/feeds/datex/England/VariableMessageSign/content.xml"
SENSOR_NAME = "variable-message-sign"


location_map = {}

def initLocationInfo():
    print "init location info.."
    r = requests.get("http://hatrafficinfo.dft.gov.uk/feeds/datex/England/PredefinedLocationVMSAndMatrix/content.xml")
    
    location_info = BeautifulSoup(r.text, "xml")
    sensors = location_info.findAll("predefinedLocation", attrs={"id": True})
    global location_map
    for sensor in sensors:
        location_map[sensor["id"]] = (sensor.find("latitude").string, sensor.find("longitude").string)

    print "done init location info.."
    
def findLocationInfo(id):
    return location_map[id]

def getSensorSchema():
    schema = [
              {"name":"lat","type":"NUMBER","required":False,"longName":"latitude"},
              {"name":"lng","type":"NUMBER","required":False,"longName":"longitude"},
              {"name":"value","type":"NUMBER","required":False,"longName":"Fault if 1"},
              {"name":"starttime","type":"STRING","required":False,"longName":"Status start time"},
              {"name":"updatedtime","type":"STRING","required":False,"longName":"Last updated time"},
              {"name":"locationref","type":"STRING","required":False,"longName":"DATEX2 VMS Location Reference"},
              {"name":"vmsid","type":"STRING","required":False,"longName":"VMS identifier"},
              {"name":"message","type":"STRING","required":False,"longName":"Message displayed"},
              {"name":"fault","type":"STRING","required":False,"longName":"Fault reason"},
              {"name":"probability","type":"STRING","required":False,"longName":"Chance of occurance"},
              {"name":"reason","type":"STRING","required":False,"longName":"Reason of status"}
              ]
    return schema

def getSensorRegistration():
    sensor = {
              "name":SENSOR_NAME,
              "longName":"England Variable Message Sign Data",
              "description":"Sensor data parsed from http://hatrafficinfo.dft.gov.uk/feeds/datex/England/VariableMessageSign/content.xml",
              "latitude": "51.506175",
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
    
    initLocationInfo()
    
    r = requests.get(DATA_GET_URI)
    text = r.text
    parsedXML = BeautifulSoup(text, "xml")
    combined_data = []
    for data in parsedXML.findAll("situationRecord"):
        wotkit_data = {}
        try:
            if hasattr(data, "vmsFault") and data.vmsFault is str:
                wotkit_data["fault"] = data.vmsFault.string
                
            wotkit_data["value"] = 1 if "fault" in wotkit_data else 0 
            wotkit_data["vmsid"] = data.vmsIdentifier.string
            wotkit_data["starttime"] = data.validity.validityTimeSpecification.overallStartTime.string
            wotkit_data["updatedtime"] = data.situationRecordVersionTime.string
            wotkit_data["locationref"] = data.groupOfLocations.locationContainedInGroup.predefinedLocationReference.string
            wotkit_data["vmsid"] = data.vmsIdentifier.string
            wotkit_data["message"] = " ".join(data.vmsLegend)
            wotkit_data["probability"] = data.probabilityOfOccurrence.string
            wotkit_data["reason"] = data.reasonForSetting.value.string
            
            wotkit_data["lat"], wotkit_data["lng"] = findLocationInfo(wotkit_data["locationref"])
            wotkit_data["timestamp"] = sensetecnic.getWotkitTimeStamp()
            combined_data.append(wotkit_data)
        except Exception as e:
            log.debug("Failed to parse traffic info" + str(e))
    try:
        sensetecnic.sendBulkData(SENSOR_NAME, None, None, combined_data)
    except Exception as e:
        log.debug("Failed to update wotkit sensor data")
        
    return [SENSOR_NAME]
