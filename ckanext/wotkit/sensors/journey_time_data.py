from bs4 import BeautifulSoup, NavigableString
import sensetecnic
import requests


import logging
log = logging.getLogger(__name__)

DATA_GET_URI = "http://hatrafficinfo.dft.gov.uk/feeds/datex/England/JourneyTimeData/content.xml"
SENSOR_NAME = "journey-time"

location_info = None

location_map = {}

def initLocationInfo():
    print "init location info.."
    r = requests.get("http://hatrafficinfo.dft.gov.uk/feeds/datex/England/PredefinedLocationJourneyTimeSections/content.xml")
    
    location_info = BeautifulSoup(r.text, "xml")
    sensors = location_info.findAll("predefinedLocation", attrs={"id": True})
    global location_map
    for sensor in sensors:
        # linear segments
        from_location = sensor.find("from")
        to_location = sensor.find("to")
        
        # from lat/long, to lat/lng
        try:
            location_map[sensor["id"]] = ((from_location.pointCoordinates.latitude.string, from_location.pointCoordinates.longitude.string), 
                                          (to_location.pointCoordinates.latitude.string, to_location.pointCoordinates.longitude.string))
        except Exception as e:
            print "to/from fields?"
    print "done init location info.."
    
def findLocationInfo(id):
    return location_map[id]

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
              {"name":"latfrom","type":"NUMBER","required":False,"longName":"latitude from"},
              {"name":"lngfrom","type":"NUMBER","required":False,"longName":"longitude from"},
              {"name":"latto","type":"NUMBER","required":False,"longName":"latitude to"},
              {"name":"lngto","type":"NUMBER","required":False,"longName":"longitude to"}
              ]
    return schema

def getSensorRegistration():
    sensor = {
              "name":SENSOR_NAME,
              "longName":"UK Traffic Travel Time",
              "description":"Sensor data parsed from http://hatrafficinfo.dft.gov.uk/feeds/datex/England/JourneyTimeData/content.xml",
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
    
    initLocationInfo()
    
    r = requests.get(DATA_GET_URI)
    text = r.text
    parsedXML = BeautifulSoup(text, "xml")
    combined_data = []
    for data in parsedXML.findAll("elaboratedData"):
        wotkit_data = {}
        try:
            wotkit_data["sourceid"] = data.sourceInformation.sourceIdentification.string
            wotkit_data["recordedtime"] = data.basicDataValue.time.string
            wotkit_data["locationref"] = data.basicDataValue.affectedLocation.locationContainedInGroup.predefinedLocationReference.string
            wotkit_data["value"] = data.basicDataValue.travelTime.string
            wotkit_data["idealtime"] = data.basicDataValue.freeFlowTravelTime.string
            wotkit_data["historictime"] = data.basicDataValue.normallyExpectedTravelTime.string
            (wotkit_data["latfrom"], wotkit_data["lngfrom"]),(wotkit_data["latto"], wotkit_data["lngto"]) = findLocationInfo(wotkit_data["locationref"])
            # For now lng lat same as from
            wotkit_data["lat"], wotkit_data["lng"] = wotkit_data["latfrom"], wotkit_data["lngfrom"]
            wotkit_data["timestamp"] = sensetecnic.getWotkitTimeStamp()
            
            combined_data.append(wotkit_data)
        except Exception as e:
            log.debug("Failed to parse traffic info: " + str(e))
    try:
        sensetecnic.sendBulkData(SENSOR_NAME, None, None, combined_data)
    except Exception as e:
        log.debug("Failed to update wotkit sensor data")
        
    return [SENSOR_NAME]
