from bs4 import BeautifulSoup, NavigableString
import sensetecnic
import requests
import traceback
import highways_agency_common
import logging
log = logging.getLogger(__name__)

DATA_GET_URI = "http://hatrafficinfo.dft.gov.uk/feeds/datex/England/JourneyTimeData/content.xml"
SENSOR_NAME = "journey-time"

location_info = None

location_map = {}


    
def findLocationInfo(id):
    return location_map[id]

def getSensorSchema():
    schema = [
              {"name":"lat","type":"NUMBER","required":False,"longName":"latitude"},
              {"name":"lng","type":"NUMBER","required":False,"longName":"longitude"},
              {"name":"direction","type":"STRING","required":False,"longName":"Direction"},
              {"name":"value","type":"NUMBER","required":False,"longName":"Expected Traffic time", "units":"seconds"},
              {"name":"idealtime","type":"NUMBER","required":False,"longName":"Ideal Traffic time (no traffic)", "units":"seconds"},
              {"name":"historictime","type":"NUMBER","required":False,"longName":"Historical Traffic time", "units":"seconds"},
              {"name":"locationref","type":"STRING","required":False,"longName":"DATEX2 Traffic Location Reference"},
              {"name":"locationname","type":"STRING","required":False,"longName":"Location Name"},
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
    
    highways_agency_common.initLocationInfo("http://hatrafficinfo.dft.gov.uk/feeds/datex/England/PredefinedLocationJourneyTimeSections/content.xml")
    
    r = requests.get(DATA_GET_URI)
    text = r.text
    parsedXML = BeautifulSoup(text, "xml")
    combined_data = []
    
    errors = {}
    errors["location"] = 0
    for field in getSensorSchema():
        errors[field["name"]] = 0
        
    for data in parsedXML.findAll("elaboratedData"):
        wotkit_data = {}
        try:
            try: wotkit_data["sourceid"] = data.sourceInformation.sourceIdentification.string
            except: errors["sourceid"] += 1
            
            try: wotkit_data["recordedtime"] = data.basicDataValue.time.string
            except: errors["recordedtime"] += 1
            
            try: wotkit_data["locationref"] = data.basicDataValue.affectedLocation.locationContainedInGroup.predefinedLocationReference.string
            except: errors["locationref"] += 1
            
            try: wotkit_data["value"] = data.basicDataValue.travelTime.string
            except:
                # required value so set to -1
                wotkit_data["value"] = -1 
                errors["value"] += 1
                
            try: wotkit_data["idealtime"] = data.basicDataValue.freeFlowTravelTime.string
            except: errors["idealtime"] += 1
            
            try: wotkit_data["historictime"] = data.basicDataValue.normallyExpectedTravelTime.string
            except: errors["historictime"] += 1
            
            try: highways_agency_common.populateLocationInfo(wotkit_data, wotkit_data["locationref"])
            except: errors["location"] += 1
            
            try: wotkit_data["timestamp"] = sensetecnic.getWotkitTimeStamp()
            except: errors["timestamp"] += 1
            
            for schema in getSensorSchema():
                if schema["type"] == "NUMBER" and schema["name"] in wotkit_data and wotkit_data[schema["name"]]:
                    try:
                        wotkit_data[schema["name"]] = float(wotkit_data[schema["name"]])
                    except Exception as e:
                        errors[schema["name"]] += 1
            combined_data.append(wotkit_data)
        except Exception as e:
            log.debug("Failed to parse traffic info: " + str(e))
            
    if any(errors.values()):
        log.warning("Errors in parsing: " + str(errors))
        
    try:
        sensetecnic.sendBulkData(SENSOR_NAME, None, None, combined_data)
    except Exception as e:
        log.debug("Failed to update wotkit sensor data")
        
    return [SENSOR_NAME]
