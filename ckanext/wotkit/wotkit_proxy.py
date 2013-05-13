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

log = getLogger(__name__)

_wotkit_url = "http://localhost:8080"

def initWotkitUrl(wotkit_url):
    global _wotkit_url 
    if not wotkit_url:
        raise Exception("No wotkit_url found in *.ini config file!")
    _wotkit_url = wotkit_url

def getBasicAuthenticationResponse(url, user, pwd, http_method = "GET", data = None):
    """Connect to wotkit api with basic authentication given by user, pwd"""
    
    content_type = {'content-type': 'application/json'}
    if not http_method:
        http_method = "GET"    
    
    json_data = json.dumps(data)
    
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
    data = json.loads(request.text)
    return data



def proxyParameters(wotkit_user, wotkit_password, api_path, http_method, data):
    """Proxy API call to the wotkit for everything after the 'api' path of the wotkit api.
    Example api_path= sensors/sensetecnic.mule1
    """

    url = _wotkit_url + "/api/" + api_path
        
    try:
        data = getBasicAuthenticationResponse(url, wotkit_user, wotkit_password, http_method, data)
    except Exception as e:
        msg = "Failed to open wotkit url. Message: " + e.message
        data = {"Error": msg}
        log.error(msg)
    return data

def getSensor(wotkit_user, wotkit_password, sensor_name):
    """Proxy API call to the wotkit for a given sensor_name"""
    
    url = _wotkit_url + "/api/sensors/" + sensor_name
    log.debug("Wotkit URL: " + url + ", User: " + wotkit_user + ", Pass: " + wotkit_password)
    
    try:
        data = getBasicAuthenticationResponse(url, wotkit_user, wotkit_password)
    except Exception as e:
        msg = "Failed to open Wotkit url. Message: " + e.message
        data = {"Error": msg}
        log.error(msg)
    
    return data