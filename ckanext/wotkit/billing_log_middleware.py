from pylons import c, request, response

import datetime
import os.path
import requests
import json
import logging
import config_globals

logging.basicConfig()

log = logging.getLogger(__name__)
log_name = "ckan.log"
log_format = "{date_time},{host},{url},{method},{status_code},{request_size},{response_size},{request_body},{response_body}\n"

body_size_limit = 1000

class BillingException(Exception):
    pass

def escape(string):
    """ CSV escaping involves using double quotes for commas and newlines RFC4180. Double quotes are then escaped with a doublequote"""
    return '"' + string.replace('"', '""') + '"'

def log(host, user, url, method, status_code, request_size, response_size, request_body, response_body):
    """
    Logs message to billing log directory.
    host = where request came from (IP)
    user = logged in username, else None
    url = current URL
    method = request method, ie GET, POST
    status_code = response status code
    other params are self explanatory
    """
    billing_log_directory = config_globals.get_billing_directory()
    now_datetime = datetime.datetime.utcnow()

    year = str(now_datetime.date().year)
    month = str(now_datetime.date().month)
    
    if not user:
        user = host
        
    user_log_path = os.path.join(billing_log_directory, year, month, user)

    if not os.path.exists(user_log_path):
        os.makedirs(user_log_path)
    
    log_file_path = os.path.join(user_log_path, log_name)
    log_file = open(log_file_path, "a+")
    
    time = now_datetime.isoformat() + 'Z'
    log_line = log_format.format(date_time=time, 
                                 host=host, 
                                 url=escape(url), 
                                 method=method, 
                                 status_code=status_code, 
                                 request_size=request_size,
                                 response_size=response_size,
                                 request_body=escape(request_body[:body_size_limit]),
                                 response_body=escape(response_body[:body_size_limit]))
    log_file.write(log_line)
    log_file.close()
        

class BillingLogMiddleware(object):
    """ Middleware class that will wrap around the pylons application.
    All calls to the pylons application will be routed through here, where we extract relevant parameters for billing log. 
    """

    def __init__(self, app, config):
        self.app = app

    def __call__(self, environ, start_response):        
        response_created = self.app(environ, start_response)

        # If there is some exception in generating response code we will probably never get here for billing logs
        # This is probably ok assuming we only log proper requests.
        url = environ["CKAN_CURRENT_URL"]
        if url.startswith("/api/i18n/"):
            # skip internatinalization api calls which happen on every html page load
            return response_created
        user = c.user
        host = environ["REMOTE_ADDR"]
        
        method = request.method
        request_body = request.body
        request_size = len(request.body)
        status_code = response.status
        # currently observed response is a list, size is usually 1 but can be more
        # it seems like it can be more than 1 when response string is chunked
        # have noticed that this chunking occurs when displaying resource previews
        response_body = "".join(response_created)
        response_size = len(response_body)
        
        
        log(host, user, url, method, status_code, request_size, response_size, request_body, response_body)
        
        return response_created
