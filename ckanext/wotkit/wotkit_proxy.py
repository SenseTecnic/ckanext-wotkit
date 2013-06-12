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

import requests

import sensors.sensetecnic as sensetecnic

log = getLogger(__name__)

_wotkit_url = ""
_api_url = ""
_processor_url = ""
_admin_id = ""
_admin_key = ""

def getWotkitAccount(username):
    url = _api_url + "/users/" + username
    response = requests.get(url, auth = (_admin_id, _admin_key))
    
    if response.status_code == 401 or response.status_code == 404:
        log.info("Wotkit account username %s not found." % username)
        return None
    else:
        return json.loads(response.text)

def createWotkitAccount(data):
    url = _api_url + "/users"
    response = getBasicAuthenticationResponse(url, _admin_id, _admin_key, "POST", data)
    if response.ok:
        log.info("Created wotkit account: " + str(data))
        return True
    else:
        log.warning("Failed to create wotkit account: " + str(data) + ", code: " + str(response.status_code))
        log.warning(response.text)
        return False

def updateWotkitAccount(username, data):
    url = _api_url + "/users/" + username
    response = getBasicAuthenticationResponse(url, _admin_id, _admin_key, "POST", data)
    if response.ok:
        log.info("Updated wotkit account: " + str(data))
        return True
    else:
        log.warning("Failed to create wotkit account: " + str(data) + ", code: " + str(response.status_code))
        log.warning(response.text)
        raise logic.ValidationError(response.text)
    
def deleteWotkitAccount(user):
    pass

def initWotkitUrls(wotkit_url, api_url, processor_url, admin_id, admin_key):
    global _wotkit_url 
    global _api_url
    global _processor_url
    global _admin_id
    global _admin_key
    
    if not wotkit_url:
        raise Exception("No wotkit_url found in *.ini config file!")
    _wotkit_url = wotkit_url
    _api_url = api_url
    _processor_url = processor_url
    _admin_id = admin_id
    _admin_key = admin_key

def getBasicAuthenticationResponse(url, user, pwd, http_method = "GET", data = None):
    """Connect to wotkit api with basic authentication given by user, pwd"""
    log.debug("URL: " + url + ", params: " + str(data))
    content_type = {'content-type': 'application/json'}
    if not http_method:
        http_method = "GET"    
    
    json_data = json.dumps(data)
    
    request = None
    if http_method == "GET":
        request = requests.get(url, auth=(user, pwd), data=json_data, headers=content_type)
    elif http_method == "POST":
        request = requests.post(url, auth=(user, pwd), data=json_data, headers=content_type)
    elif http_method == "PUT":
        request = requests.put(url, auth=(user, pwd), data=json_data, headers=content_type)
    elif http_method == "DELETE":
        request = requests.delete(url, auth=(user, pwd), data=json_data, headers=content_type)
    else:
        raise ValueError("Invalid HTTP request")
    
    return request



def proxyParameters(wotkit_user, wotkit_password, api_path, http_method, data):
    """Proxy API call to the wotkit for everything after the 'api' path of the wotkit api.
    Example api_path= sensors/sensetecnic.mule1
    """

    url = _api_url + "/" + api_path
        
    try:
        response = getBasicAuthenticationResponse(url, wotkit_user, wotkit_password, http_method, data)
        data = json.loads(response.text)
    except Exception as e:
        msg = "Failed to open wotkit url. Message: " + e.message
        data = {"Error": msg}
        log.error(msg)
    return data

def getSensor(wotkit_user, wotkit_password, sensor_name):
    """Proxy API call to the wotkit for a given sensor_name"""
    
    url = _api_url + "/sensors/" + sensor_name
    log.debug("Wotkit URL: " + url + ", User: " + wotkit_user + ", Pass: " + wotkit_password)
    
    try:
        response = getBasicAuthenticationResponse(url, wotkit_user, wotkit_password)
        data = json.loads(response.text)
    except Exception as e:
        msg = "Failed to open Wotkit url. Message: " + e.message
        data = {"Error": msg}
        log.error(msg)

    
    return data