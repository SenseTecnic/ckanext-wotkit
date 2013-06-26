
'''
Version 1.0 - Updated June 25, 2013

'''

import json
import pprint

import requests


import json
import requests

from datetime import datetime
import logging
import traceback

if __name__ == "main":
    logging.basicConfig()
log = logging.getLogger(__name__)
#log.setLevel(logging.DEBUG)


def get_wotkit_timestamp():
    return datetime.utcnow().isoformat() + "Z"

class WotkitException(Exception):
    pass

class WotkitConfig():
    """ Struct that contains wotkit connection information. """
    wotkit_url = None
    api_url = None
    processor_url = None 
    admin_user = None
    admin_password = None
    
    @classmethod
    def get_default_config(cls):
        return WotkitConfig('http://smartstreets.sensetecnic.com/wotkit',
                            'http://smartstreets.sensetecnic.com/wotkit/api',
                            'http://smartstreets.sensetecnic.com/wotkit/processor',
                            'mduppes',
                            'aMUSEment2')
    
    def __init__(self, wotkit_url, api_url, processor_url, admin_user, admin_key):
        """
        Initialize globals of this module. For now only used for harvesting into wotkit
        """
        
        self.wotkit_url = wotkit_url
        self.api_url = api_url
        self.processor_url = processor_url
        self.admin_user = admin_user
        self.admin_password = admin_key

    def get_login_credentials(self):
        return (self.admin_user, self.admin_password)


class WotkitProxy():
    """ Acts as a network proxy to the Wotkit based on the configuration supplied """
    config = None
    
    def __init__(self, config):
        """ Pass in a WotkitConfig on construction """
        self.config = config
    
    def get_sensor_by_name(self, sensor_name):
        '''Sensor names need the user name added onto it'''
        user, password = self.config.get_login_credentials()
        return self.get_sensor_by_id(user + "." + sensor_name)

    def get_sensor_by_id(self, sensor_id):
        # send authorization headers preemptively otherwise we get redirected to a login page
        sensor_id = str(sensor_id)
        user, password = self.config.get_login_credentials()
 
        
        url = self.config.api_url+'/sensors/'+sensor_id
        req = requests.get(url, auth = (user, password))

        if req.status_code == 200:
            log.debug("Success getting sensor " + sensor_id)
            return json.loads(req.text) 
        elif req.status_code == 404:
            log.debug("Sensor doesn't exist " + sensor_id)
            return None      
        else:
            raise WotkitException("Error in getting sensor url %s, code: " % url + str(req.status_code))

    def send_data_post_by_name(self, sensor_name, params):
        user, password = self.config.get_login_credentials()
        return send_data_post(user + "." + sensor_name, params)

    def send_data_post(self, sensor_id, params):
        #use SenseTecnic
        #log.info("Sending data to wotkit for sensor " + sensor + ": " + str(attributes))
        sensor_id = str(sensor_id)
        user, password = self.config.get_login_credentials()
        url = self.config.api_url+'/sensors/'+sensor_id+'/data'
    
        response = requests.post(url = url, auth=(user, password), data = params)
        if response.status_code == 201:
            log.debug("Success sending POST sensor data to url: " + url)
            return True
        else:
            raise WotkitException("Not successful in sending POST sensor data to url %s: error code " % url + str(response.status_code))            

    def send_bulk_data_put_by_name(self, sensor_name, data):
        user, password = self.config.get_login_credentials()
        self.send_bulk_data_put(user + "." + sensor_name, data)
        

    def send_bulk_data_put(self, sensor_id, data):
        sensor_id = str(sensor_id)
        json_data = json.dumps(data)
        
        user, password = self.config.get_login_credentials()
        url = self.config.api_url+'/sensors/'+sensor_id+'/data'

        response = requests.put(url = url, auth=(user, password), data = json_data, headers = {"content-type": "application/json"})
        if response.status_code == 204:
            log.debug("Success sending bulk PUT data to sensor url: " + url)
            return True
        else:
            raise WotkitException("Not successful in sending bulk PUT data to sensor url %s: error code " % url + str(response.status_code))


    def search_all_sensors(self):
        """ Gets all sensors in the wotkit and returns it as a dictionary """
        sensors = {}
        offset = 0
        while True:
            existing_sensors = self.search_sensors_paging(offset)
            if not existing_sensors:
                break
            log.debug("Searching.. found %d sensors.." % len(existing_sensors))
            for existing_sensor in existing_sensors:
                sensors[existing_sensor['id']] = existing_sensor
            offset += len(existing_sensors)
        return sensors

    def search_sensors_paging(self, offset):
        user, password = self.config.get_login_credentials()
        response = requests.get(self.config.api_url + "/sensors?offset=" + str(offset), auth=(user, password))
        if not response.ok:
            msg = "Failed to search sensors: code: %d. Message: %s" % (response.status_code, response.text)
            raise Exception(msg)
        sensors = json.loads(response.text)
        return sensors

    def update_sensor(self, sensor_id, sensor_data):
        sensor_id = str(sensor_id)
        user, password = self.config.get_login_credentials()
        url = self.config.api_url + "/sensors/" + sensor_id
        json_data = json.dumps(sensor_data)
        headers = {"content-type": "application/json"}
        response = requests.put(url = url, auth=(user, password), data = json_data, headers = headers)
        
        if response.ok:
            log.debug("Success updating sensor schema for url " + url)
            return True
        else:
            raise WotkitException("Error while registering/updating sensor %s to url: %s  " % (sensor_id, url))
        
    def register_sensor(self, sensor_data):
        user, password = self.config.get_login_credentials()
        url = self.config.api_url+'/sensors'
        json_data = json.dumps(sensor_data)
        headers = {"content-type": "application/json"}
        response = requests.post(url = url, auth=(user, password), data = json_data, headers = headers)

        if response.ok:
            log.debug("Success registering sensor for url " + url + " sensor: " + str(sensor_data["name"]))
            return True
        else:
            raise WotkitException("Error while registering sensor %s to url: %s  " % (str(sensor_data["name"]), url))
        
    def check_and_register_sensor(self, register_data):
        '''Updates or Registers sensor_data dictionary depending on whether sensor already exists'''
        sensor_data = self.get_sensor_by_name(str(register_data["name"]))

        if sensor_data:

            log.debug("Sensor %s already exists updating sensor schema" % str(register_data["name"]))
            self.update_sensor(str(sensor_data["id"]), sensor_data)
        else:
            log.debug("Sensor %s probably doesn't exist, creating new sensor" % str(register_data["name"]))
            self.register_sensor(register_data)

    def delete_sensor(self, sensor_id):
        sensor_id = str(sensor_id)
        url = self.config.api_url + "/sensors/" + sensor_id
        user, password = self.config.get_login_credentials()
        delete_response = requests.delete(url, auth = (user, password))
        
        if delete_response.ok:
            log.debug("Deleted sensor %s" % sensor_id)
        else:
            msg = "Failed to delete sensor %s: code: %d. Message: %s" % (sensor_id, delete_response.status_code, delete_response.text)
            raise WotkitException(msg)

    def get_wotkit_user(self, user_id):
        '''Get wotkit user with user_id. Requires admin credentials in WotkitConfig'''
        user_id = str(user_id)
        url = self.config.api_url + "/users/" + user_id
        user, password = self.config.get_login_credentials()
        response = requests.get(url, auth = (user, password))
        
        if not response.ok:
            log.info("Wotkit account username %s not found." % user_id)
            return None
        else:
            return json.loads(response.text)
    
    def create_wotkit_user(self, data):
        '''Creates user given in data dictionary. Requires admin credentials in WotkitConfig'''
        url = self.config.api_url + "/users"
        user, password = self.config.get_login_credentials()
        json_data = json.dumps(data)
        headers = {"content-type": "application/json"}
        
        response = requests.post(url, auth = (user, password), data = json_data, headers = headers)
        
        if response.ok:
            log.info("Created wotkit account: " + str(data))
            return True
        else:
            msg = "Failed to create wotkit account: " + str(data) + ", code: " + str(response.status_code) + "message: " + str(response.text)
            log.warning(msg)
            raise WotkitException(msg)
    
    def update_wotkit_user(self, user_id, data):
        '''Updates user user_id with data dictionary. Requires admin credentials in WotkitConfig'''
        user_id = str(user_id)
        url = self.config.api_url + "/users/" + user_id
        user, password = self.config.get_login_credentials()
        json_data = json.dumps(data)
        headers = {"content-type": "application/json"}
        response = requests.put(url, auth = (user, password), data = json_data, headers = headers)
        
        if response.ok:
            log.info("Updated wotkit account: " + str(data))
            return True
        else:
            log.warning("Failed to update wotkit account: " + str(data) + ", code: " + str(response.status_code))
            log.warning(response.text)
            raise WotkitException(response.text)
