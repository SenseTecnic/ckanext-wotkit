'''
Created on Jul 7, 2010

@author: mike
'''
import pdb
import urllib
import urllib2
import base64
import random
import time
import datetime
import simplejson as json
import requests
from datetime import datetime
import logging
log = logging.getLogger(__name__)
import traceback


BROKER_BASE_URL='http://localhost:8800/osgibroker/event'
STS_WOTKIT_URL='http://guiness.sensetecnic.com/wotkit'
STS_API_URL='http://guiness.sensetecnic.com/wotkit/api'
STS_PROCESSOR_URL=''
STS_ID='mduppes'
STS_KEY='aMUSEment2'

def init(wotkit_url, api_url, processor_url, id, key):
    """
    Initialize globals of this module. For now only used for harvesting into wotkit
    """
    global STS_WOTKIT_URL, STS_API_URL, STS_ID, STS_KEY
    
    STS_WOTKIT_URL = wotkit_url
    STS_API_URL = api_url 
    STS_PROCESSOR_URL
    STS_ID = id
    STS_KEY = key

def getWotkitUrl():
    return STS_WOTKIT_URL

def getWotkitApiUrl():
    return STS_API_URL

def getWotkitProcessorUrl():
    return STS_PROCESSOR_URL

def getWotkitTimeStamp():
    return datetime.utcnow().isoformat() + "Z"
#format("%Y-%m-%dT%H:%M:%SZ")

def _checkPassword(user, password):
    """ If user or password is empty, change it to the default configured credentials 
    """
    if not user or not password:
        return (STS_ID, STS_KEY)
    else:
        return (user, password)
    
class SenseTecnicError(Exception):
    """Exception raised for errors in the input.

    Attributes:
        msg  -- explanation of the error
        e    -- exception that caused this exception
    """

    def __init__(self, msg, e=None):
        self.msg = msg
        self.e = e

def sendData(sensor, user, password, attributes):
    #use SenseTecnic
    print "Sending data to wotkit for sensor " + sensor + ": " + str(attributes)
    sendDataSenseTecnic(sensor, user, password, attributes);

def sendBulkData(sensor, user, password, attributes):
    json_data = json.dumps(attributes)
    
    user, password = _checkPassword(user, password)
    url = STS_API_URL+'/sensors/'+sensor+'/data'

    # send authorization headers premptively otherwise we get redirected to a login page

    try:
        response = requests.put(url = url, auth=(user, password), data = json_data, headers = {"content-type": "application/json"})
        if response.status_code == 204:
            print "Success updating wotkit for sensor: " + sensor
        else:
            print "Not successful in updating sensor: error code " + str(response.status_code)
            
    except Exception, e:
        print 'error - sending event to sensor: %s' % (sensor)
        print e.message
        return -1
    return 0

def sendDataSenseTecnic(sensor, user, password, attributes):
    

    user, password = _checkPassword(user, password)
    url = STS_API_URL+'/sensors/'+sensor+'/data'

    # send authorization headers premptively otherwise we get redirected to a login page

    try:
        response = requests.post(url = url, auth=(user, password), data = attributes)
        if response.status_code == 201:
            print "Success updating wotkit for sensor: " + sensor
        else:
            print "Not successful in updating sensor: error code " + str(response.status_code)
            
    except Exception, e:
        print 'error - sending event to sensor: %s' % (sensor)
        print e.message
        return -1
    return 0

def getSensor(sensorName, user = STS_ID, password = STS_KEY):
    # send authorization headers preemptively otherwise we get redirected to a login page
    user, password = _checkPassword(user, password)       
    
    
    try:
    
        url = STS_API_URL+'/sensors/'+user + '.' + sensorName
        req = requests.get(url, auth = (user, password))
    
        log.debug("getting sensor: " + url)
        
        if req.status_code == 200:
            log.debug("success getting sensor " + sensorName)
            return json.loads(req.text)       
        else:
            log.debug("failed getting sensor, code: " + str(req.status_code))
            return None
                
    except Exception as e:
        print "Error: " + str(e)
        return None
    

def checkAndRegisterSensor(sensor, user = None, password = None):

    sensor_data = getSensor(str(sensor["name"]), user, password)


    jsonSensor = json.dumps(sensor)
    log.debug( "JSON DUMP of register sensor schema: " + jsonSensor)
    user, password = _checkPassword(user, password)
    url = STS_API_URL+'/sensors'
    headers = {"content-type": "application/json"}
    # send authorization headers premptively otherwise we get redirected to a login page


    if sensor_data: 
        url = url + "/" + str(sensor_data["id"])
        response = requests.put(url = url, auth=(user, password), data = jsonSensor, headers = headers)
    else:
        response = requests.post(url = url, auth=(user, password), data = jsonSensor, headers = headers)
            
    if response.ok:
        log.debug("success registering/updating sensor schema")
        return True
    else:
        log.warning("Error while registering/updating sensor %s to url: %s  " % (sensor["name"], url))
        return False
