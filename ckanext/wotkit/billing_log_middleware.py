from pylons import c

import datetime
import os.path
import requests
import json
import logging
import config_globals

logging.basicConfig()

log = logging.getLogger(__name__)
log_name = "ckan.log"
log_format = "{time},{host},{url},{size}\n"

class BillingException(Exception):
    pass

def log(host, user, url, size):
    """
    Logs message to billing log directory.
    host = where request came from (IP)
    user = logged in username, else None
    url = current URL
    size = length of response body
    """
    billing_log_directory = config_globals.get_billing_directory()
    now_datetime = datetime.datetime.now()

    year = str(now_datetime.date().year)
    month = str(now_datetime.date().month)
    
    if not user:
        user = host
        
    user_log_path = os.path.join(billing_log_directory, year, month, user)

    if not os.path.exists(user_log_path):
        os.makedirs(user_log_path)
    
    log_file_path = os.path.join(user_log_path, log_name)
    log_file = open(log_file_path, "a+")
    
    time = str(now_datetime.time())
    log_line = log_format.format(time=time, host=host, url=url, size=size)
    log_file.write(log_line)
    log_file.close()
        

class BillingLogMiddleware(object):
    """ Middleware class that will wrap around the pylons application.
    All calls to the pylons application will be routed through here, where we extract relevant parameters for billing log. 
    """

    def __init__(self, app, config):
        self.app = app

    def __call__(self, environ, start_response):        
        response = self.app(environ, start_response)

        # If there is some exception in generating response code we will probably never get here for billing logs
        # This is probably ok assuming we only log proper requests.
        
        url = environ["CKAN_CURRENT_URL"]
        if url.startswith("/api/i18n/"):
            # skip internatinalization api calls which happen on every html page load
            return response
        user = c.user
        host = environ["REMOTE_ADDR"]
        
        # currently observed response is a list, size is usually 1 but can be more
        # it seems like it can be more than 1 when response string is chunked
        # have noticed that this chunking occurs when displaying resource previews
        length = 0
        for response_string in response:
            length += len(response_string)
        
        log(host, user, url, length)
        
        return response
