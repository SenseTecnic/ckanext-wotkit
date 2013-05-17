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
    log.debug("Setting wotkit url: " + wotkit_url)
    log.debug("Setting wotkit api url: " + api_url)
    log.debug("Setting wotkit id: " + id)
    log.debug("Setting wotkit key: " + key)
    log.debug("Setting wotkit processor url: " + processor_url)
    
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

def sendDataSenseTecnic(sensor, user, password, attributes):
    encoded_args = urllib.urlencode(attributes)

    user, password = _checkPassword(user, password)

    # send authorization headers premptively otherwise we get redirected to a login page
    base64string = base64.encodestring('%s:%s' % (user, password))[:-1]
        
    headers = {
        'User-Agent': 'httplib',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': "Basic %s" % base64string
    }
    
    url = STS_API_URL+'/sensors/'+sensor+'/data'
    req = urllib2.Request(url,encoded_args,headers)
    try:
        urllib2.urlopen(req)
    except urllib2.URLError, e:
        print 'error - sending event to sensor: %s' % (sensor)
        print e.reason
        return -1
    return 0

def getSensor(sensorName, user = None, password = None):
    # send authorization headers preemptively otherwise we get redirected to a login page
    user, password = _checkPassword(user, password)
    base64string = base64.encodestring('%s:%s' % (user, password))[:-1]
        
    headers = {
        'User-Agent': 'httplib',
        'Content-Type': 'application/json',
        'Authorization': "Basic %s" % base64string
    }
    
    url = STS_API_URL+'/sensors/'+user + '.' + sensorName
    req = urllib2.Request(url,None,headers)
    log.debug("getting sensor: " + url)
    try:
        
        result = urllib2.urlopen(req)
        if result.code == 204:
            log.debug("success getting sensor")
        else:
            log.debug("failed getting sensor, code: " + result.code)
        sensor = json.load(result)
        
    except urllib2.HTTPError, e:
        if (e.code == 404):
            raise SenseTecnicError('%s does not exist' % (sensorName), e)
            return
        
        if (e.code != 204):
            print '%s while getting: %s' % (e,sensorName)
            raise SenseTecnicError(e,e)
            return
               
    except urllib2.URLError, e:
        print 'error - getting sensor: %s' % (sensorName)
        raise SenseTecnicError('URLError while registering %s' % (sensorName),e)
        return
    
    return sensor

def checkAndRegisterSensor(sensor, user = None, password = None):
    try:
        sensor = getSensor(sensor, user, password)
        return True if sensor else False
    except Exception as e:
        log.debug("Probably not found. Attempting to register new sensor")
        
    
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


