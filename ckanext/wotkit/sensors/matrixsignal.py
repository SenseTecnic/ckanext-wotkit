from bs4 import BeautifulSoup, NavigableString
import sensetecnic
import requests

import logging
log = logging.getLogger(__name__)

DATA_GET_URI = "http://hatrafficinfo.dft.gov.uk/feeds/datex/England/MatrixSignals/content.xml"
SENSOR_NAME = "matrix-signals"

location_map = {}

aspect_map = {
              "UDF": "Undefined",
              "OFF": "Off",
              "NR": "Nation Restriction",
              "RE": "Restriction End",
              "STOP": "Stop",
              "20": "Advisory 20",
              "30": "Advisory 30",
              "40": "Advisory 40",
              "50": "Advisory 50",
              "60": "Advisory 60",
              "70": "Advisory 70",
              "80": "Advisory 80",
              "100": "Advisory 100",
              "120": "Advisory 120",
              "LDR": "Lane Divert Right",
              "REDX": "Tidal Close",
              "LDL": "Lane Divert Left",
              "MDVL": "Motorway Divert Left",
              "TWAY": "Two Way Traffic",
              "1T": "Lane 2 closed of 2",
              "T1": "Land 1 closed of 2",
              "TT1": "Lanes 1 & 2 closed of 3",
              "T11": "Lane 1 closed of 3",
              "1TT": "Lanes 2 & 3 closed of 3",
              "11T": "Lane 3 closed of 3",
              "1(C)": "Lane Open",
              "MDVR": "Motorway Divert Right",
              "FOG": "Fog",
              "Q": "Queue",
              "111T": "Lane 4 closed of 4",
              "11TT": "Lanes 3 & 4 closed of 4",
              "1TTT": "Lanes 2, 3, & 4 closed of 4",
              "T111": "Lane 1 closed of 4",
              "TT11": "Lanes 1 & 2 closed of 4",
              "TTT1": "Lanes 1, 2, & 3 closed of 4",
              "20R": "Mandatory 20",
              "30R": "Mandatory 30",
              "40R": "Mandatory 40",
              "50R": "Mandatory 50",
              "60R": "Mandatory 60",
              "70R": "Mandatory 70",
              "80R": "Mandatory 80",
              "100R": "Mandatory 100",
              "120R": "Mandatory 120",
              "TST1": "Test 1",
              "TST2": "Test 2",
              "TST3": "Test 3",
              "TST4": "Test 4",
              "MOFF": "MIDAS Off",
              "AMB": "Amber Flashers",
              "tDL": "Tidal Divert Left",
              "None": "None yet Allocated",
              }


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
    
    initLocationInfo()
    
    r = requests.get(DATA_GET_URI)
    text = r.text
    parsedXML = BeautifulSoup(text, "xml")
    combined_data = []
    for data in parsedXML.findAll("situationRecord"):
        wotkit_data = {}
        try:
            wotkit_data["active"] = data.validity.validityStatus.string
            wotkit_data["value"] = 0 if wotkit_data["active"] == "active" else 1 
            wotkit_data["updatedtime"] = data.situationRecordVersionTime.string
            wotkit_data["starttime"] = data.validity.validityTimeSpecification.overallStartTime.string
            wotkit_data["locationref"] = data.groupOfLocations.locationContainedInGroup.predefinedLocationReference.string
            wotkit_data["matrixid"] = data.matrixIdentifier.string
            wotkit_data["display"] = aspect_map[data.aspectDisplayed.string]
            
            
            wotkit_data["reason"] = data.reasonForSetting.value.string

            wotkit_data["lat"], wotkit_data["lng"] = findLocationInfo(wotkit_data["locationref"])
            wotkit_data["timestamp"] = sensetecnic.getWotkitTimeStamp()
            combined_data.append(wotkit_data)
        except Exception as e:
            log.debug("Failed to parse single traffic data: " + str(e))
    try:
        sensetecnic.sendBulkData(SENSOR_NAME, None, None, combined_data)
    except Exception as e:
        log.debug("Failed to update wotkit sensor data")
        
    return [SENSOR_NAME]

