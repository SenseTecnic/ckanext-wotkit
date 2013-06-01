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

BROKER_BASE_URL='http://localhost:8800/osgibroker/event'
STS_WOTKIT_URL=''
STS_API_URL=''
STS_PROCESSOR_URL=''
STS_ID=''
STS_KEY=''

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

    sensorExists = getSensor(sensor["name"], user, password)
    if sensorExists: return True        
    
        #only register non-existing ones
    jsonSensor = json.dumps(sensor)
    log.debug( "JSON DUMP of register: " + jsonSensor)
    user, password = _checkPassword(user, password)
    # send authorization headers preemptively otherwise we get redirected to a login page
    base64string = base64.encodestring('%s:%s' % (user, password))[:-1]
        
    headers = {
        'User-Agent': 'httplib',
        'Content-Type': 'application/json',
        'Authorization': "Basic %s" % base64string
    }
    log.debug( "Headers: " + str(headers))
    
    url = STS_API_URL+'/sensors'
    req = urllib2.Request(url,jsonSensor, headers)
    log.debug("registering sensor: " + url)
    try:
        response = urllib2.urlopen(req)
        if response.code == 201:
            log.debug("success registering sensor")
            return True
        else:
            print "Not Success: Code: " + response.getCode()
    except urllib2.HTTPError, e:
        if (e.code != 204):
            print '%s while registering: %s' % (e,sensor["name"])
            raise SenseTecnicError(e,e)
            print e.message
    except urllib2.URLError, e:
        print 'error - registering sensor: %s' % (sensor["name"])
        raise SenseTecnicError('URLError while registering %s' % (sensor["name"]),e)

    return False


