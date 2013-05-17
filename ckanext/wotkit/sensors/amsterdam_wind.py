import requests
import sys
import time
import sensetecnic
import logging
import json


log = logging.getLogger(__name__)

DATA_GET_URI = 'http://api.openweathermap.org/data/2.5/weather?lat=52.373056&lon=4.892222'
SENSOR_POST_URI = 'http://127.0.0.1:8080/api/sensors/daniel.amsterdam-wind/data'
SENSOR_TIME_DELAY = 600
WOTKIT_KEY_USER = '9c7158f02d16f68b'
WOTKIT_KEY_PASS = '85e0753e41b709d1'

SENSOR_NAME = "amserdam-wind"

def getSensorSchema():
    schema = [
              {"name":"lat","type":"NUMBER","required":False,"longName":"latitude"},
              {"name":"lng","type":"NUMBER","required":False,"longName":"longitude"},
              {"name":"value","type":"NUMBER","required":False,"longName":"Data"},
              {"name":"direction","type":"NUMBER","required":False,"longName":"Message"},
              ]
    return schema

def getSensorRegistration():
    sensor = {
              "name":SENSOR_NAME,
              "longName":"Amsterdam Wind Data",
              "description":"Sensor taken from openweathermap.org of wind data in Amsterdam",
              "latitude": "52.37305",
              "longitude": "4.8922",
              "private":False,
              "tags":["wind", "Amsterdam"],
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
    
    r = requests.get(DATA_GET_URI)
    j = r.json()
            
    value = j['wind']['speed']
    direction = j['wind']['deg']
    wotkit_data = {"value": value, "direction": direction}
    
    sensetecnic.sendData(SENSOR_NAME, None, None, wotkit_data)    

