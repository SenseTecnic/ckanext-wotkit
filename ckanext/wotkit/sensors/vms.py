from bs4 import BeautifulSoup, NavigableString
import sensetecnic
import requests
import highways_agency_common
import traceback
import logging
log = logging.getLogger(__name__)

DATA_GET_URI = "http://hatrafficinfo.dft.gov.uk/feeds/datex/England/VariableMessageSign/content.xml"
SENSOR_NAME = "variable-message-sign"

def getSensorSchema():
    schema = [
              {"name":"lat","type":"NUMBER","required":False,"longName":"latitude"},
              {"name":"lng","type":"NUMBER","required":False,"longName":"longitude"},
              {"name":"direction","type":"STRING","required":False,"longName":"Direction"},
              {"name":"value","type":"NUMBER","required":False,"longName":"Fault if 1"},
              {"name":"starttime","type":"STRING","required":False,"longName":"Status start time"},
              {"name":"updatedtime","type":"STRING","required":False,"longName":"Last updated time"},
              {"name":"locationref","type":"STRING","required":False,"longName":"DATEX2 VMS Location Reference"},
              {"name":"vmsid","type":"STRING","required":False,"longName":"VMS identifier"},
              {"name":"vmstype","type":"STRING","required":False,"longName":"VMS Type"},
              {"name":"message","type":"STRING","required":False,"longName":"Message displayed"},
              {"name":"fault","type":"STRING","required":False,"longName":"Fault reasons"},
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
        log.warning("Failed to register sensor %s. " % SENSOR_NAME + str(e))

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
            
            try: wotkit_data["vmsid"] = data.vmsIdentifier.string
            except: errors["vmsid"] += 1
            
            try: wotkit_data["vmstype"] = data.vmsType.string
            except: errors["vmstype"] += 1
            
            try: wotkit_data["starttime"] = data.validity.validityTimeSpecification.overallStartTime.string
            except: errors["starttime"] += 1
            
            try: wotkit_data["updatedtime"] = data.situationRecordVersionTime.string
            except: errors["updatedtime"] += 1
            
            try: wotkit_data["locationref"] = data.groupOfLocations.locationContainedInGroup.predefinedLocationReference.string
            except: errors["locationref"] += 1
            
            try: wotkit_data["vmsid"] = data.vmsIdentifier.string
            except: errors["vmsid"] += 1
            
            try: wotkit_data["message"] = "".join([message.string for message in data.findAll("vmsLegend")])
            except: errors["message"] += 1
            
            try: wotkit_data["probability"] = data.probabilityOfOccurrence.string
            except: errors["probability"] += 1
            
            try: wotkit_data["reason"] = data.reasonForSetting.value.string
            except: errors["reason"] += 1
            
            try: wotkit_data["fault"] = ",".join([message.string for message in data.findAll("vmsFault")])
            except: errors["fault"] += 1 
            
            wotkit_data["value"] = 1 if "fault" in wotkit_data else 0
            
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
            log.warning("Failed to parse single vms data. " + traceback.format_exc())
    
    if any(errors.values()):
        log.warning("Errors in parsing: " + str(errors))
    
    try:
        sensetecnic.sendBulkData(SENSOR_NAME, combined_data)
    except Exception as e:
        log.error("Failed to update wotkit sensor data for %s" % SENSOR_NAME)
        
    return [SENSOR_NAME]
