from bs4 import BeautifulSoup, NavigableString
import sensetecnic
import requests
import traceback

import logging
log = logging.getLogger(__name__)

"""

DATEX II Locations mapping to lat/lng, direction used by several sensors. They are obtained from huge datasets so it caches and does lazy loading.

"""
url_cache = set()
point_map = {}
linear_map = {}


def populateLocationInfo(wotkit_data, location_id):
    location_info = point_map.get(location_id, None)
    
    if location_info:
        # this is  a point
        wotkit_data["lat"], wotkit_data["lng"] = location_info["lat"], location_info["lng"]
        wotkit_data["direction"] = location_info["direction"]
    else:
        location_info = linear_map.get(location_id, None)
        if location_info:
            wotkit_data["latfrom"], wotkit_data["lngfrom"] = location_info["from"]
            wotkit_data["latto"], wotkit_data["lngto"] = location_info["to"]
            wotkit_data["locationname"] = location_info["locationname"]
            wotkit_data["direction"] = location_info["direction"]
            
            # For now lng lat same as from
            wotkit_data["lat"], wotkit_data["lng"] = wotkit_data["latfrom"], wotkit_data["lngfrom"]
        else:
            raise Exception("No matching location for id: " + str(location_id))
    
    
def initLocationInfo(url):
    global url_cache, point_map, linear_map
    
    if url in url_cache:
        log.debug("URL: %s already exists in cache" % url)
        # Already loaded this url
        return
    log.debug("Retrieving location info for url: %s" % url)
    
    r = requests.get(url)
    
    location_info = BeautifulSoup(r.text, "xml")
    locations = location_info.findAll("predefinedLocation", attrs={"id": True})
    

    for location in locations:
        if location.find("predefinedLocation", attrs={"type": "Point"}):
            # These coordinates are used for matrix, and vms locations
            coordinates = location.find("pointCoordinates")
            direction = location.find("tpegDirection")
            try:
                # No name extraction since it is just the matrix/vms identifier
                point_map[location["id"]] = {"lat": float(coordinates.latitude.string),
                                             "lng": float(coordinates.longitude.string),
                                             "direction": direction.string
                                             }
            except:
                log.warning("Failed to parse point %s: " % str(location["id"]) + traceback.format_exc())
                
        elif location.find("predefinedLocation", attrs={"type": "Linear"}):
            # These coordinates are used for journey time, traffic info for road segments

            from_location = location.find("from")
            to_location = location.find("to")
            direction = location.find("tpegDirection")
            
            try:
                linear_map[location["id"]] = {"from": (float(from_location.pointCoordinates.latitude.string), float(from_location.pointCoordinates.longitude.string)),
                                              "to": (float(to_location.pointCoordinates.latitude.string), float(to_location.pointCoordinates.longitude.string)),
                                              "direction": direction.string,
                                              "locationname":location.predefinedLocationName.value.string
                                              } 
            except Exception:
                log.warning("Failed to parse location lat long for section %s. " % str(location["id"]) + traceback.format_exc())
        else:
            log.warning("Can't find point or linear coordinates for location: " + str(location))

    
    url_cache.add(url)

# This schema is the same for events and roadworks
def getEventSensorSchema():
    schema = [
              {"name":"lat","type":"NUMBER","required":False,"longName":"latitude"},
              {"name":"lng","type":"NUMBER","required":False,"longName":"longitude"},
              {"name":"direction","type":"STRING","required":False,"longName":"Direction"},
              {"name":"value","type":"NUMBER","required":False,"longName":"Operational Lanes"},
              {"name":"restrictedlanes","type":"NUMBER","required":False,"longName":"Restricted Lanes"},
              {"name":"endtime","type":"STRING","required":False,"longName":"End Time"},
              {"name":"starttime","type":"STRING","required":False,"longName":"Start Time"},
              {"name":"updatedtime","type":"STRING","required":False,"longName":"Record Last Updated Time"},
              {"name":"comment","type":"STRING","required":False,"longName":"Comments"},
              {"name":"impact","type":"STRING","required":False,"longName":"Impact on traffic"},
              {"name":"delaytime","type":"NUMBER","required":False,"longName":"Delay Time", "units": "seconds"},
              {"name":"occurrence","type":"STRING","required":False,"longName":"Probability of occurrence"},
              {"name":"latfrom","type":"NUMBER","required":False,"longName":"latitude from"},
              {"name":"lngfrom","type":"NUMBER","required":False,"longName":"longitude from"},
              {"name":"latto","type":"NUMBER","required":False,"longName":"latitude to"},
              {"name":"lngto","type":"NUMBER","required":False,"longName":"longitude to"}
              ]
    return schema
    
def retrieveCommonEventFormat(url):
    r = requests.get(url)
    text = r.text
    parsedXML = BeautifulSoup(text, "xml")
    combined_data = []
    
    errors = {}
    errors["location"] = 0
    for field in getEventSensorSchema():
        errors[field["name"]] = 0
        
    for data in parsedXML.findAll("situationRecord"):
        wotkit_data = {}
        try:            
            try: location = data.groupOfLocations.locationContainedInGroup.tpegpointLocation
            except: errors["location"] += 1
            
            if location:
                from_location = location.find("from")
                to_location = location.find("to")
                
                try: wotkit_data["direction"] = location.tpegDirection.string
                except: errors["direction"] += 1
                
                try:
                    wotkit_data["lat"] = location.framedPoint.pointCoordinates.latitude.string
                    wotkit_data["lng"] = location.framedPoint.pointCoordinates.longitude.string
                    wotkit_data["latfrom"] = from_location.pointCoordinates.latitude.string
                    wotkit_data["lngfrom"] = from_location.pointCoordinates.longitude.string        
                    wotkit_data["latto"] = to_location.pointCoordinates.latitude.string
                    wotkit_data["lngto"] = to_location.pointCoordinates.longitude.string
                except Exception as e:
                    try:
                        wotkit_data["lat"] = location.point.pointCoordinates.latitude.string
                        wotkit_data["lng"] = location.point.pointCoordinates.longitude.string
                    except: errors["location"] += 1
            
            try: wotkit_data["value"] = data.impact.impactDetails.numberOfOperationalLanes.string
            except: 
                # need a value, set as -1
                wotkit_data["value"] = -1
                errors["value"] += 1
            
            try: wotkit_data["recordedtime"] = data.situationRecordVersionTime.string
            except: errors["recordedtime"] += 1
            
            try: wotkit_data["restrictedlanes"] = data.impact.impactDetails.numberOfLanesRestricted.string
            except: errors["restrictedlanes"] += 1
            
            try: wotkit_data["delaytime"] = data.impact.delays.delayTimeValue.string
            except: errors["delaytime"] += 1
            
            try: wotkit_data["endtime"] = data.validity.validityTimeSpecification.overallEndTime.string
            except: errors["endtime"] += 1
            
            try: wotkit_data["starttime"] = data.validity.validityTimeSpecification.overallStartTime.string
            except: errors["starttime"] += 1
            
            try: wotkit_data["comment"] = data.nonGeneralPublicComment.comment.value.string
            except: errors["comment"] += 1
            
            try: wotkit_data["impact"] = data.impact.impactOnTraffic.string
            except: errors["impact"] += 1
            
            try: wotkit_data["occurrence"] = data.probabilityOfOccurrence.string
            except: errors["occurence"] += 1
            
            try: wotkit_data["timestamp"] = sensetecnic.getWotkitTimeStamp()
            except: errors["timestamp"] += 1
            
            for schema in getEventSensorSchema():
                if schema["type"] == "NUMBER" and schema["name"] in wotkit_data and wotkit_data[schema["name"]]:
                    try:
                        wotkit_data[schema["name"]] = float(wotkit_data[schema["name"]])
                    except Exception as e:
                        errors[schema["name"]] += 1
                
            combined_data.append(wotkit_data)
        except Exception as e:
            log.debug("Failed to parse single traffic data: " + traceback.format_exc())
            
    if any(errors.values()):
        log.warning("Errors in parsing: " + str(errors))
        
    return combined_data