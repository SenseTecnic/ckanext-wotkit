import ckanext.wotkit.wotkit_proxy as wotkit_proxy
import ckanext.wotkit.config_globals as config_globals
import traceback
import logging
log = logging.getLogger(__name__)
''' This file is an intermediate layer, eventually think of cleaning this up.
Sends data to all wotkit proxies defined in config_globals'''

def checkAndRegisterSensor(sensor_registration_schema):
    proxies = config_globals.get_wotkit_proxies()
    for proxy in proxies:
        try:
            proxy.check_and_register_sensor(sensor_registration_schema)
        except Exception:
            log.error(traceback.format_exc())
        
        
def getWotkitTimeStamp():
    return wotkit_proxy.get_wotkit_timestamp()

def sendBulkData(sensor_name, data):
    proxies = config_globals.get_wotkit_proxies()
    for proxy in proxies:
        try:
            proxy.send_bulk_data_put_by_name(sensor_name, data)
        except Exception:
            log.error(traceback.format_exc())