import ckanext.wotkit.wotkit_proxy as wotkit_proxy
import urlparse
import routes
import wotkitpy
from ckan.common import c

'''

This file contains all configuration globals used in ckan-wotkit hub.

Additional important functions include storing all connections to wotkit instances.
When a wotkit-harvester update is run, data is sent to all wotkit proxies defined.

init should be called on initialization
'''

# globals for now, access these through getter functions implemented in this file
wotkit_proxy = None

wotkit_url = None
wotkit_api_url = None
ckan_url = None
smarstreets_base_url = None
smartstreets_about_url = None
logout_success_url = None

# wotkit admin credentials used for managing users
wotkit_admin_id = None
wotkit_admin_key = None

billing_directory = None

def init(config):
    """
    Initializes global URL's used. Input config is supplied from plugin.py and is read from the configuration .ini file
    """
    global wotkit_url, wotkit_api_url, ckan_url, smarstreets_base_url, smartstreets_about_url, logout_success_url
    global wotkit_admin_id, wotkit_admin_key
    global billing_directory
    
    wotkit_url = get_required_config(config, "wotkit.wotkit_url")
    wotkit_api_url = get_required_config(config, "wotkit.api_url")
    
    ckan_url = get_required_config(config, "ckan.site_url")
    smarstreets_base_url = get_required_config(config, "smartstreets.base_url")
    smartstreets_about_url = get_required_config(config, "smartstreets.about_url")
    logout_success_url = get_required_config(config, "ckan.logout_success_url")
    
    check_url_starts_with_http(wotkit_url)
    check_url_starts_with_http(wotkit_api_url)
    check_url_starts_with_http(ckan_url)
    check_url_starts_with_http(smarstreets_base_url)
    check_url_starts_with_http(smartstreets_about_url)
    check_url_starts_with_http(logout_success_url)
    
    wotkit_admin_id = get_required_config(config, "wotkit.admin_id")
    wotkit_admin_key = get_required_config(config, "wotkit.admin_key")  

    billing_directory = get_required_config(config, "billing.directory")
    
    global wotkit_proxy    
    wotkit_proxy = wotkitpy.WotkitProxy(**{"api_url": wotkit_api_url, "username": wotkit_admin_id, "password": wotkit_admin_key})

def get_wotkit_proxy():
    """ get main proxy """
    return wotkit_proxy 

""" The URL functions below modify the URL's given in development.ini file to dynamically respond to HTTP and HTTPS.

"""

def modify_protocol(url):
    """Given a url that starts with http or https, returns the url with appropriate protocol HTTP or HTTPS"""
    protocol = c.environ["routes.cached_hostinfo"]["protocol"]
    return url.replace("http", protocol, 1)

def get_ckan_url():
    return modify_protocol(ckan_url)

def get_wotkit_url(): 
    return modify_protocol(wotkit_url)
    
def get_wotkit_api_url():
    return modify_protocol(wotkit_api_url)

def get_logout_success_url():
    return modify_protocol(logout_success_url)
    
def get_logout_all_url():
    """ Logout URL that triggers the redirects done to logout of all wotkit, ckan sites. """
    wotkit_logout_url = get_wotkit_url() + "/logout/bridge"
    return get_ckan_url() + "/user/_logout?came_from=" + wotkit_logout_url + "," + get_logout_success_url()
    
def get_smartstreets_base_url():
    return modify_protocol(smarstreets_base_url)
    
def get_smartstreets_about_url():
    return modify_protocol(smartstreets_about_url)

def get_required_config(config, name):
    """ Extract name from config, and throws if it doesn't exist """
    value = config.get(name)
    if not value:
        raise Exception("No %s in configuration .ini file" % name)
    return value

def check_url_starts_with_http(url):
    if url.startswith("https"):
        raise Exception("URL's must start with http, not https")
    if not url.startswith("http"):
        raise Exception("URL's must start with http. They are dynamically changed depending on user request to http, https")
        
def get_billing_directory():
    return billing_directory