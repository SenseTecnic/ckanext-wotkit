import requests
import sys
import time
import sensetecnic
import logging
import json
import csv
import urllib2

log = logging.getLogger(__name__)


DATA_GET_URI = "http://countdown.api.tfl.gov.uk/interfaces/ura/instant_V1?ReturnList=StopPointName,StopID,Towards,Bearing,Latitude,Longitude,VisitNumber,TripID,VehicleID,RegistrationNumber,LineID,LineName,DirectionID,DestinationText,DestinationName,EstimatedTime,ExpireTime"
SENSOR_NAME = "london-live-bus"

def getDataSchema():
    schema = [
              {"name":"StopPointName", "type": "STRING", "required":False, "longName":"StopPointName"},
              {"name":"StopID", "type": "STRING", "required":False, "longName":"StopID"},
              {"name":"Towards", "type": "STRING", "required":False, "longName":"Bus is headed towards"},
              {"name":"Bearing", "type": "STRING", "required":False, "longName":"Direction the bus is traveling"},
              {"name":"lat","type":"NUMBER","required":False,"longName":"latitude"},
              {"name":"lng","type":"NUMBER","required":False,"longName":"longitude"},
              {"name":"VisitNumber", "type": "STRING", "required":False, "longName":"Indicates a stop is visited the first time"},
              {"name":"TripID", "type": "STRING", "required":False, "longName":"Trip Identifier"},
              {"name":"VehicleID", "type": "STRING", "required":False, "longName":"Vehicle Identifier"},
              {"name":"RegistrationNumber", "type": "STRING", "required":False, "longName":"Registration number"},
              {"name":"LineID", "type": "STRING", "required":False, "longName":"Internal Route identifier"},
              {"name":"LineName", "type": "STRING", "required":False, "longName":"Public Route identifier"},
              {"name":"DirectionID", "type": "STRING", "required":False, "longName":"Outbound or Inbound direction"},
              {"name":"DestinationText", "type": "STRING", "required":False, "longName":"Abbreviated destination name"},
              {"name":"DestinationName", "type": "STRING", "required":False, "longName":"Destination name"},
              {"name":"EstimatedTime", "type": "NUMBER", "required":False, "longName":"Estimated arrival time at the given bus stop"},
              {"name":"ExpireTime", "type": "NUMBER", "required":False, "longName":"Time at which prediction should expire"}
              ]
    return schema

def getSensorSchema():
    schema = [
              {"name":"value", "type": "NUMBER", "required":True, "longName":"value"}
              ]
    schema.extend(getDataSchema())
    return schema

def getSensorRegistration():
    sensor = {
              "name":SENSOR_NAME,
              "longName":"London Bus Live Arrivals",
              "description":"Live bus data from London. For more detail please look at http://www.tfl.gov.uk/assets/downloads/businessandpartners/tfl-live-bus-and-river-bus-arrivals-api-documentation.pdf",
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
    try:
        req = urllib2.urlopen(DATA_GET_URI)
        combined_data = []
        for x in range(0,300):
            line = req.readline().strip('[]\r\n ')
            if not line: 
                break
            retrieved_fields = line.split(',')
            schema = getDataSchema()
            result = {}
            try:
                if retrieved_fields[0] == "1":
                    if not len(retrieved_fields) == len(schema) + 1:
                        print "Schema length does not match retrieved data."
                        continue
                    for (counter, field) in enumerate(schema):
                        result[field["name"]] = retrieved_fields[counter+1].strip('"\\')
                        
                    result["value"] = result["EstimatedTime"]
                    print "value: " + str(result["value"])
                    
                    result["timestamp"] = sensetecnic.getWotkitTimeStamp()
                    combined_data.append(result)
                   
            except Exception as e:
                print "err"
            print str(len(result)) + ", " + pprint.pformat(result)
        sensetecnic.sendBulkData(SENSOR_NAME, None, None, combined_data)    
        #r = requests.get(DATA_GET_URI, timeout=0.4, stream=True)
    except Exception as e:
        print "Error in retrieving data from london instant bus api"
        
    return [SENSOR_NAME]
    
    
    
    