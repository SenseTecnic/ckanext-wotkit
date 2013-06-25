import ckanext.wotkit.wotkit_proxy as wotkit_proxy
import ckanext.wotkit.config_globals as config_globals


''' This file is an intermediate layer, eventually think of cleaning this up.
Sends data to all wotkit proxies defined in config_globals'''

def checkAndRegisterSensor(sensor_registration_schema):
    proxies = config_globals.get_wotkit_proxies()
    for proxy in proxies:
        proxy.check_and_register_sensor(sensor_registration_schema)
        
        
def getWotkitTimeStamp():
    return wotkit_proxy.get_wotkit_timestamp()

def sendBulkData(sensor_name, data):
    proxies = config_globals.get_wotkit_proxies()
    for proxy in proxies:
        proxy.send_bulk_data_put(sensor_name, data)