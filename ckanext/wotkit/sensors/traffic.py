from bs4 import BeautifulSoup, NavigableString
import sensetecnic
import requests
import traceback
import highways_agency_common
import logging
log = logging.getLogger(__name__)

DATA_GET_URI = "http://hatrafficinfo.dft.gov.uk/feeds/datex/England/TrafficData/content.xml"
SENSOR_NAME = "traffic-general"


def getSensorSchema():
    schema = [
              {"name":"lat","type":"NUMBER","required":False,"longName":"latitude"},
              {"name":"lng","type":"NUMBER","required":False,"longName":"longitude"},
              {"name":"occupancy","type":"NUMBER","required":False,"longName":"Percentage Traffic Occupancy", "units":"percentage"},
              {"name":"expectedtime","type":"NUMBER","required":False,"longName":"Expected Traffic time", "units":"seconds"},
              {"name":"idealtime","type":"NUMBER","required":False,"longName":"Ideal Traffic time (no traffic)", "units":"seconds"},
              {"name":"historictime","type":"NUMBER","required":False,"longName":"Historical Traffic time", "units":"seconds"},
              {"name":"longvehicles","type":"NUMBER","required":False,"longName":"Percentage of long vehicles (>11.6m)", "units":"percentage"},
              {"name":"averagespeed","type":"NUMBER","required":False,"longName":"Average vehicle speed", "units":"km/hr"},
              {"name":"value","type":"NUMBER","required":False,"longName":"Total vehicle flow", "units": "number of vehicles"},
              {"name":"smallflow","type":"NUMBER","required":False,"longName":"Small (<=5.2m) vehicle flow", "units": "number of vehicles"},
              {"name":"mediumflow","type":"NUMBER","required":False,"longName":"Medium (>5.2m, <=6.6m) vehicle flow", "units": "number of vehicles"},
              {"name":"largeflow","type":"NUMBER","required":False,"longName":"Large (>6.6m, <=11.6m) vehicle flow", "units": "number of vehicles"},
              {"name":"longflow","type":"NUMBER","required":False,"longName":"Longest (largest) (>11.6m) vehicle flow", "units": "number of vehicles"},
              {"name":"locationref","type":"STRING","required":False,"longName":"DATEX2 Traffic Location Reference"},
              {"name":"direction","type":"STRING","required":False,"longName":"Flow Direction"},
              {"name":"sourceid","type":"STRING","required":False,"longName":"DATEX2 Traffic Link ID"},
              {"name":"recordedtime","type":"STRING","required":False,"longName":"Timestamp of traffic record"},
              {"name":"locationname","type":"STRING","required":False,"longName":"Name of road segment"},
              {"name":"latfrom","type":"NUMBER","required":False,"longName":"latitude from"},
              {"name":"lngfrom","type":"NUMBER","required":False,"longName":"longitude from"},
              {"name":"latto","type":"NUMBER","required":False,"longName":"latitude to"},
              {"name":"lngto","type":"NUMBER","required":False,"longName":"longitude to"}
              ]
    return schema

def getSensorRegistration():
    sensor = {
              "name":SENSOR_NAME,
              "longName":"UK Traffic Data",
              "description":"Contains travel time estimation as well as vehicle counts grouped by size of vehicles. All data is recorded over 5 minute periods. Sensor data parsed from http://hatrafficinfo.dft.gov.uk/feeds/datex/England/TrafficData/content.xml.",
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
        log.warning("Failed to register sensor %s. " % SENSOR_NAME + traceback.format_exc())

def assignField(wotkit_data, field_name, new_value):
    """Assigns the field while checking that the previous value matches the new value"""
    if field_name in wotkit_data and wotkit_data[field_name] != new_value:
        raise Exception("inconsistent field: %s" % field_name)
    wotkit_data[field_name] = new_value
        
def updateWotkit():
    checkSensorExist()
    
    highways_agency_common.initLocationInfo("http://hatrafficinfo.dft.gov.uk/feeds/datex/England/PredefinedLocationLinks/content.xml")
    highways_agency_common.initLocationInfo("http://hatrafficinfo.dft.gov.uk/feeds/datex/England/PredefinedLocationJourneyTimeSections/content.xml")
    
    log.debug("Getting data from url: %s" % DATA_GET_URI)
    r = requests.get(DATA_GET_URI)
    parsedXML = BeautifulSoup(r.text, "xml")
    
    existing_data = {}
    # xml data is disorganized so that multiple elaboratedData sections refer to the same road section and contains different parts of the data.
    # currently compares all xml data for a sourceId, and makes sure the common values are the same (or else it discards it)
    errors = {}
    errors["location"] = 0
    for field in getSensorSchema():
        errors[field["name"]] = 0
    

    for data in parsedXML.findAll("elaboratedData"):
        
        try:
            source_id = data.sourceInformation.sourceIdentification.string
            
            if source_id in existing_data:
                wotkit_data = existing_data[source_id]
            else:
                wotkit_data = {}
                
            wotkit_data["sourceid"] = source_id
        except Exception as e:
            log.warning("SourceId failure. " + traceback.format_exc())
            continue
            
        try:
            basic_data_value = data.basicDataValue
            recorded_time = basic_data_value.time.string
            assignField(wotkit_data, "recordedtime", recorded_time)
            
            location_reference = basic_data_value.affectedLocation.locationContainedInGroup.predefinedLocationReference.string
            assignField(wotkit_data, "locationref", location_reference)
            
            # Just extract location once
            if not "lat" in wotkit_data:
                try: highways_agency_common.populateLocationInfo(wotkit_data, wotkit_data["locationref"])
                except: errors["location"] += 1
            
            
            # Just update timestamp
            wotkit_data["timestamp"] = sensetecnic.getWotkitTimeStamp()
            
            data_type = basic_data_value["type"]

            
            if data_type == "TravelTimeValue":
                try: wotkit_data["expectedtime"] = basic_data_value.travelTime.string
                except: errors["expectedtime"] += 1
                try: wotkit_data["idealtime"] = basic_data_value.freeFlowTravelTime.string
                except: errors["idealtime"] += 1
                try: wotkit_data["historictime"] = basic_data_value.normallyExpectedTravelTime.string
                except: errors["historictime"] += 1
                
            elif data_type == "TrafficSpeed":
                try: wotkit_data["averagespeed"] = basic_data_value.averageVehicleSpeed.string
                except: errors["averagespeed"] += 1
            
            elif data_type == "TrafficConcentration":
                try: wotkit_data["occupancy"] = basic_data_value.occupancy.string
                except: errors["occupancy"] += 1
                    
                
            elif data_type == "TrafficFlow":
                try:
                    # Try to extract data assuming it is one of small, medium, large, or long (largest) flows
                    vehicle_characteristics = basic_data_value.vehicleCharacteristics
                    vehicle_contents = vehicle_characteristics.contents
                except:
                    # this is the total data
                    try: wotkit_data["longvehicles"] = basic_data_value.percentageLongVehicles.string
                    except: errors["longvehicles"] += 1
                    try: wotkit_data["value"] = basic_data_value.vehicleFlow.string
                    except: 
                        # since this is a required field, set to -1
                        wotkit_data["value"] = -1
                        errors["value"] += 1

                else:
                    # only checking vehicle lengths to determine the category of flow
                    if len(vehicle_contents) == 1:
                        # smallest or largest vehicle size
                        try: vehicle_length = vehicle_characteristics.lengthCharacteristic.vehicleLength.string
                        except: log.warning(traceback.format_exc())
                        
                        if vehicle_length == "5.2":
                            # This is smallest vehicle
                            try: wotkit_data["smallflow"] = basic_data_value.vehicleFlow.string
                            except: errors["smallflow"] += 1
                        elif vehicle_length == "11.6":
                            try: wotkit_data["longflow"] = basic_data_value.vehicleFlow.string
                            except: errors["longflow"] += 1
                        else:
                            log.warning("no match for vehicle size %s")
                    elif len(vehicle_contents) == 2:
                        # compare size bounds of vehicle
                        medium_lengths = ["5.2", "6.6"]
                        large_lengths = ["6.6", "11.6"]
                        try: lengths = [vehicle_characteristics.contents[0].vehicleLength.string, vehicle_characteristics.contents[1].vehicleLength.string]
                        except: log.warning(traceback.format_exc())
                        
                        if all([x in medium_lengths for x in lengths]):
                            try: wotkit_data["mediumflow"] = basic_data_value.vehicleFlow.string
                            except: errors["mediumflow"] += 1
                        elif all([x in large_lengths for x in lengths]):
                            try: wotkit_data["largeflow"] = basic_data_value.vehicleFlow.string
                            except: errors["largeflow"] += 1
                        else:
                            log.warning("No match for vehicle sizes: " + str(lengths))
                    else:
                        log.warning("vehicle content size is not 1 or 2: %d" % len(vehicle_contents))
                        
        except Exception as e:
            log.warning("Failed to parse traffic info item: " + traceback.format_exc())
            
        existing_data[source_id] = wotkit_data
    
    for wotkit_data in existing_data:
        for schema in getSensorSchema():
            if schema["type"] == "NUMBER" and schema["name"] in wotkit_data and wotkit_data[schema["name"]]:
                try:
                    wotkit_data[schema["name"]] = float(wotkit_data[schema["name"]])
                except Exception as e:
                    errors[schema["name"]] += 1 
    
    if any(errors.values()):
        log.warning("Errors in parsing: " + str(errors))
        
    try:
        sensetecnic.sendBulkData(SENSOR_NAME, None, None, existing_data.values())
    except Exception as e:
        log.error("Failed to update wotkit sensor data for %s" % SENSOR_NAME)
        
    return [SENSOR_NAME]
