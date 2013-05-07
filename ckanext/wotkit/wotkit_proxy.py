import sys
from ckan.lib.base import request
from ckan.lib.base import c, g, h
from ckan.lib.base import model
from ckan.lib.base import render
from ckan.lib.base import _

from ckan.lib.navl.validators import not_empty

from logging import getLogger

import ckan.logic as logic

import urllib2
import json
import pprint

log = getLogger(__name__)

_wotkit_url = "http://localhost:8080"

def getBasicAuthenticationResponse(url, user, pwd, base_url = _wotkit_url):
    """Connect to wotkit api with basic authentication given by user, pwd"""
    auth_handler = urllib2.HTTPBasicAuthHandler()
    auth_handler.add_password(realm="Spring Security Application",
                              uri=base_url,
                              user=user,
                              passwd=pwd)
    opener = urllib2.build_opener(auth_handler)
    response = opener.open(url)
    data = json.loads(response.read())
    return data

def getSensor(wotkit_user, wotkit_password, sensor_name):
    """Proxy API call to the wotkit for a given sensor_name"""
    base_url = _wotkit_url
    url = base_url + "/api/sensors/" + sensor_name
    log.debug("Wotkit URL: " + url + ", User: " + wotkit_user + ", Pass: " + wotkit_password)
    
    try:
        data = getBasicAuthenticationResponse(url, wotkit_user, wotkit_password)
    except Exception as e:
        msg = "Failed to open Wotkit url. Message: " + e.msg
        data = {"Error": msg}
        log.error(msg)
    
    return data