from bs4 import BeautifulSoup, NavigableString
import sensetecnic
import requests
import traceback
import logging
log = logging.getLogger(__name__)
import highways_agency_common
DATA_GET_URI = "http://hatrafficinfo.dft.gov.uk/feeds/datex/England/MatrixSignals/content.xml"
SENSOR_NAME = "matrix-signals"


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


def getSensorSchema():
    schema = [
              {"name":"lat","type":"NUMBER","required":False,"longName":"latitude"},
              {"name":"lng","type":"NUMBER","required":False,"longName":"longitude"},
              {"name":"direction","type":"STRING","required":False,"longName":"Direction"},
              {"name":"starttime","type":"STRING","required":False,"longName":"Status start time"},
              {"name":"updatedtime","type":"STRING","required":False,"longName":"Status last updated time"},
              {"name":"locationref","type":"STRING","required":False,"longName":"DATEX2 Matrix Location Reference"},
              {"name":"matrixid","type":"STRING","required":False,"longName":"Matrix identifier"},
              {"name":"display","type":"STRING","required":False,"longName":"DATEX2 Aspect Displayed"},
              {"name":"reason","type":"STRING","required":False,"longName":"Reason of status"},
              {"name":"value","type":"NUMBER","required":False,"longName":"Always 0, ignore"},
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
    
    highways_agency_common.initLocationInfo("http://hatrafficinfo.dft.gov.uk/feeds/datex/England/PredefinedLocationVMSAndMatrix/content.xml")
    
    r = requests.get(DATA_GET_URI)
    text = r.text
    parsedXML = BeautifulSoup(text, "xml")
    combined_data = []

    errors = {}
    errors["location"] = 0
    for field in getSensorSchema():
        errors[field["name"]] = 0
        
    for data in parsedXML.findAll("situationRecord"):
        wotkit_data = {}
        try:
            wotkit_data["value"] = 0
            try: wotkit_data["updatedtime"] = data.situationRecordVersionTime.string
            except: errors["updatedtime"] += 1
            
            try: wotkit_data["starttime"] = data.validity.validityTimeSpecification.overallStartTime.string
            except: errors["starttime"] += 1
            
            try: wotkit_data["locationref"] = data.groupOfLocations.locationContainedInGroup.predefinedLocationReference.string
            except: errors["locationref"] += 1
            
            try: wotkit_data["matrixid"] = data.matrixIdentifier.string
            except: errors["matrixid"] += 1
            
            try: wotkit_data["display"] = aspect_map[data.aspectDisplayed.string]
            except: errors["display"] += 1
            
            try: wotkit_data["reason"] = data.reasonForSetting.value.string
            except: errors["reason"] += 1

            try: highways_agency_common.populateLocationInfo(wotkit_data, wotkit_data["locationref"])
            except: errors["location"] += 1
            
            try: wotkit_data["timestamp"] = sensetecnic.getWotkitTimeStamp()
            except: errors["timestamp"] += 1

            # change all strings to number where needed
            for schema in getSensorSchema():
                if schema["type"] == "NUMBER" and schema["name"] in wotkit_data and wotkit_data[schema["name"]]:
                    try:
                        wotkit_data[schema["name"]] = float(wotkit_data[schema["name"]])
                    except Exception as e:
                        errors[schema["name"]] += 1
                        
            combined_data.append(wotkit_data)
        except Exception as e:
            log.debug("Failed to parse single matrix data item: " + traceback.format_exc())
            
    if any(errors.values()):
        log.warning("Errors in parsing: " + str(errors))
        
    try:
        sensetecnic.sendBulkData(SENSOR_NAME, combined_data)
    except Exception as e:
        log.debug("Failed to update wotkit sensor data")
        
    return [SENSOR_NAME]

