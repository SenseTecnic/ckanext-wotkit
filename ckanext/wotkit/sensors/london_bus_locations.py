import requests
import sys
import time
import sensetecnic
import logging
import json
import csv
import urllib2
import traceback

log = logging.getLogger(__name__)

return_fields = [
                 "StopPointName",
                 "StopID",
                 "Towards",
                 "Bearing",
                 "Latitude",
                 "Longitude",
                 "VisitNumber",
                 "TripID",
                 "RegistrationNumber",
                 "LineName",
                 "DirectionID",
                 "DestinationText",
                 "DestinationName",
                 "EstimatedTime",
                 "ExpireTime"
                 ]

DATA_GET_URI = "http://countdown.api.tfl.gov.uk/interfaces/ura/instant_V1?ReturnList=" + ",".join(return_fields)
SENSOR_NAME = "london-live-bus"

def getSensorSchema():
    schema = [
              {"name":"StopPointName", "type": "STRING", "required":False, "longName":"StopPointName"},
              {"name":"StopID", "type": "STRING", "required":False, "longName":"StopID"},
              {"name":"Towards", "type": "STRING", "required":False, "longName":"Bus is headed towards"},
              {"name":"Bearing", "type": "STRING", "required":False, "longName":"Direction the bus is traveling", "units": "degrees"},
              {"name":"lat","type":"NUMBER","required":False,"longName":"latitude"},
              {"name":"lng","type":"NUMBER","required":False,"longName":"longitude"},
              {"name":"VisitNumber", "type": "STRING", "required":False, "longName":"Indicates a stop is visited the first time"},
              {"name":"TripID", "type": "STRING", "required":False, "longName":"Trip Identifier"},
              {"name":"RegistrationNumber", "type": "STRING", "required":False, "longName":"Registration number"},
              {"name":"LineName", "type": "STRING", "required":False, "longName":"Public Route identifier"},
              {"name":"DirectionID", "type": "STRING", "required":False, "longName":"Outbound or Inbound direction"},
              {"name":"DestinationText", "type": "STRING", "required":False, "longName":"Abbreviated destination name"},
              {"name":"DestinationName", "type": "STRING", "required":False, "longName":"Destination name"},
              {"name":"value", "type": "NUMBER", "required":True, "longName":"Estimated arrival time at the given bus stop", "units": "epoch time in milliseconds"},
              {"name":"ExpireTime", "type": "NUMBER", "required":False, "longName":"Time at which prediction should expire"}
              ]
    
    return schema

def getSensorRegistration():
    sensor = {
              "name":SENSOR_NAME,
              "longName":"London Bus Live Arrivals",
              "description":"Live bus data from London. Data provided by Transport for London. For more detail please look at http://www.tfl.gov.uk/assets/downloads/businessandpartners/tfl-live-bus-and-river-bus-arrivals-api-documentation.pdf",
              "latitude": "51.506178",
              "longitude": "-0.113983",
              "private":False,
              "tags":["london", "transport", "bus"],
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
    import pprint
    results = []
    r = None
    errors = {}
    errors["length"] = 0
    errors["other"] = []
    try:
        # need to use urllib2 instead of requests because this dataset is too large (streaming?)
        req = urllib2.urlopen(DATA_GET_URI)
        combined_data = []
        for x in range(0,300):
            line = req.readline().strip('[]\r\n ')
            if not line: 
                break
            retrieved_fields = line.split(',')

            result = {}
            try:
                if retrieved_fields[0] == "1":
                    if not len(retrieved_fields) == len(return_fields) + 1:
                        errors["length"] += 1
                        continue
                    for (counter, field) in enumerate(return_fields):
                        result[field] = retrieved_fields[counter+1].strip('"\\')
                        
                    # value is the estimated time and wotkit requires value
                    result["value"] = result["EstimatedTime"]
                    result["lat"] = result["Latitude"]
                    result["lng"] = result["Longitude"]
                    del result["Latitude"]
                    del result["Longitude"]
                    del result["EstimatedTime"]
                    
                    result["timestamp"] = sensetecnic.getWotkitTimeStamp()
                    #log.debug(str(result))

                    # change all strings to number where needed
                    for schema in getSensorSchema():
                        if schema["type"] == "NUMBER" and schema["name"] in result and result[schema["name"]]:
                            try:
                                result[schema["name"]] = float(result[schema["name"]])
                            except Exception as e:
                                errors[schema["name"]] += 1
                                
                    combined_data.append(result)
                   
            except Exception as e:
                errors["other"].append(traceback.format_exc())
    except Exception as e:
        log.warning("Error in retrieving data from london instant bus api")
    
    if any(errors.values()):
        log.warning("Errors in retrieving london instant bus data: " + str(errors))
    
    try:
        sensetecnic.sendBulkData(SENSOR_NAME, None, None, combined_data)
    except:
        log.error("Failed to send bulk data to wotkit for london bus instant. " + traceback.format_exc())    
        #r = requests.get(DATA_GET_URI, timeout=0.4, stream=True)

        
    return [SENSOR_NAME]
    
    
    
    