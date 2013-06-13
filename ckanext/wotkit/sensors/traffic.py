from bs4 import BeautifulSoup, NavigableString
import sensetecnic
import requests
import traceback

import logging
log = logging.getLogger(__name__)

DATA_GET_URI = "http://hatrafficinfo.dft.gov.uk/feeds/datex/England/TrafficData/content.xml"
SENSOR_NAME = "traffic-general"

location_info = None

location_map = {}

def initLocationInfo(url):
    print "init location info for url: %s" % url
    r = requests.get(url)
    
    location_info = BeautifulSoup(r.text, "xml")
    sensors = location_info.findAll("predefinedLocation", attrs={"id": True})
    global location_map
    for sensor in sensors:
        # linear segments
        from_location = sensor.find("from")
        to_location = sensor.find("to")
        direction = sensor.find("tpegDirection")
        
        # from lat/long, to lat/lng
        try:
            location_map[sensor["id"]] = {"from": (from_location.pointCoordinates.latitude.string, from_location.pointCoordinates.longitude.string),
                                          "to": (to_location.pointCoordinates.latitude.string, to_location.pointCoordinates.longitude.string),
                                          "direction": direction.string,
                                          "name":sensor.predefinedLocationName.value.string}
        
        except Exception as e:
            log.debug("Failed to parse location lat long for section %s" % str(sensor["id"]))
            traceback.print_exc()
    
def findLocationInfo(id):
    return location_map[id]
    

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
        log.warning(str(e))
        traceback.print_exc()
        log.warning("Failed to register sensor %s. " % SENSOR_NAME)

def assignField(wotkit_data, field_name, new_value):
    """Assigns the field while checking that the previous value matches the new value"""
    if field_name in wotkit_data and wotkit_data[field_name] != new_value:
            raise Exception("recordedtime mismatch for field: %s" % field_name)
    wotkit_data[field_name] = new_value
        
def updateWotkit():
    checkSensorExist()
    
    initLocationInfo("http://hatrafficinfo.dft.gov.uk/feeds/datex/England/PredefinedLocationLinks/content.xml")
    initLocationInfo("http://hatrafficinfo.dft.gov.uk/feeds/datex/England/PredefinedLocationJourneyTimeSections/content.xml")
    
    log.debug("Getting data from url: %s" % DATA_GET_URI)
    r = requests.get(DATA_GET_URI)
    parsedXML = BeautifulSoup(r.text, "xml")
    
    existing_data = {}
    # xml data is disorganized so that multiple elaboratedData sections refer to the same road section and contains different parts of the data.
    # currently compares all xml data for a sourceId, and makes sure the common values are the same (or else it discards it)
    
    for data in parsedXML.findAll("elaboratedData"):
        
        try:
            source_id = data.sourceInformation.sourceIdentification.string
            
            if source_id in existing_data:
                wotkit_data = existing_data[source_id]
            else:
                wotkit_data = {}
                
            wotkit_data["sourceid"] = source_id
            
            basic_data_value = data.basicDataValue
            recorded_time = basic_data_value.time.string
            assignField(wotkit_data, "recordedtime", recorded_time)
            
            location_reference = basic_data_value.affectedLocation.locationContainedInGroup.predefinedLocationReference.string
            assignField(wotkit_data, "locationref", location_reference)
            
            if not "lat" in wotkit_data:
                location_info = findLocationInfo(location_reference)
                wotkit_data["latfrom"], wotkit_data["lngfrom"] = location_info["from"]
                wotkit_data["latto"], wotkit_data["lngto"] = location_info["to"]
                wotkit_data["direction"] = location_info["direction"]
                wotkit_data["locationname"] = location_info["name"]
                # For now lng lat same as from
                wotkit_data["lat"], wotkit_data["lng"] = wotkit_data["latfrom"], wotkit_data["lngfrom"]
            
            
            # Just update timestamp
            wotkit_data["timestamp"] = sensetecnic.getWotkitTimeStamp()
            
            data_type = basic_data_value["type"]
            
            if data_type == "TravelTimeValue":
                wotkit_data["expectedtime"] = basic_data_value.travelTime.string
                wotkit_data["idealtime"] = basic_data_value.freeFlowTravelTime.string
                wotkit_data["historictime"] = basic_data_value.normallyExpectedTravelTime.string
                
            elif data_type == "TrafficSpeed":
                wotkit_data["averagespeed"] = basic_data_value.averageVehicleSpeed.string
            
            elif data_type == "TrafficConcentration":
                try:
                    wotkit_data["occupancy"] = basic_data_value.occupancy.string
                except Exception:
                    pass
                
            elif data_type == "TrafficFlow":
                try:
                    # Try to extract data assuming it is one of small, medium, large, or long (largest) flows
                    vehicle_characteristics = basic_data_value.vehicleCharacteristics
                    
                    flow = basic_data_value.vehicleFlow.string
                    # only checking vehicle lengths to determine the category of flow
                    if len(vehicle_characteristics.contents) == 1:
                        # smallest or largest vehicle size
                        if vehicle_characteristics.lengthCharacteristic.vehicleLength.string == "5.2":
                            # This is smallest vehicle
                            wotkit_data["smallflow"] = flow
                        elif vehicle_characteristics.lengthCharacteristic.vehicleLength.string == "11.6":
                            wotkit_data["longflow"] = flow
                    elif len(vehicle_characteristics.contents) == 2:
                        # compare size bounds of vehicle
                        medium_lengths = ["5.2", "6.6"]
                        large_lengths = ["6.6", "11.6"]
                        lengths = [vehicle_characteristics.contents[0].vehicleLength.string, vehicle_characteristics.contents[1].vehicleLength.string]
                        if all([x for x in lengths if x in medium_lengths]):
                             wotkit_data["mediumflow"] = flow
                        elif all([x for x in lengths if x in large_lengths]):
                             wotkit_data["largeflow"] = flow
                             
                except Exception as e:
                    # this is the total data
                    try:
                        wotkit_data["longvehicles"] = basic_data_value.percentageLongVehicles.string
                    except Exception: 
                        pass
                    wotkit_data["value"] = basic_data_value.vehicleFlow.string
            
            # store back
            existing_data[source_id] = wotkit_data
            print wotkit_data
        except Exception as e:
            log.debug("Failed to parse traffic info: " + str(e))
            traceback.print_exc()
    try:
        sensetecnic.sendBulkData(SENSOR_NAME, None, None, existing_data.values())
    except Exception as e:
        log.debug("Failed to update wotkit sensor data")
        
    return [SENSOR_NAME]
