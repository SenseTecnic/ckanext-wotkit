import ckanext.wotkit.wotkit_proxy as wotkit_proxy
import urlparse
import routes
import wotkitpy

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
    
    wotkit_admin_id = get_required_config(config, "wotkit.admin_id")
    wotkit_admin_key = get_required_config(config, "wotkit.admin_key")  

    billing_directory = get_required_config(config, "billing.directory")
    
    global wotkit_proxy    
    wotkit_proxy = wotkitpy.WotkitProxy(**{"api_url": wotkit_api_url, "username": wotkit_admin_id, "password": wotkit_admin_key})

def get_wotkit_proxy():
    """ get main proxy """
    return wotkit_proxy 

""" The URL functions below are meant to be used from HTML templates as well as places where URL's are needed such as unified login.
Template helpers are configured in plugins.py, and essentially links to these functions when used in HTML templates.

The url's are changed dynamically to handle http and https automatically based on the accessed URL.

The problem is ckan URL functionality such as url_for assumes the /data path and appends it automatically.
When we want to redirect to wotkit this is problematic.
"""

def get_ckan_url():
    return routes.url_for(strip_domain_url(ckan_url), qualified=True)

def get_wotkit_url(): 
    return routes.url_for(strip_domain_url(wotkit_url), qualified=True).replace("/data", "")
    
def get_wotkit_api_url():
    return routes.url_for(strip_domain_url(wotkit_api_url), qualified=True).replace("/data", "")

def get_logout_success_url():
    full_url = routes.url_for(strip_domain_url(logout_success_url), qualified=True)
    return full_url.replace("/data/data", "/data")

def strip_domain_url(url):
    split_url = urlparse.urlsplit(url)
    stripped_url = split_url.path
    if split_url.query:
        stripped_url += "?" + split_url.query
    return stripped_url
    
def get_logout_all_url():
    """ Logout URL that triggers the redirects done to logout of all wotkit, ckan sites. """
    wotkit_logout_url = get_wotkit_url() + "/logout/bridge"
    return strip_domain_url(ckan_url) + "/user/_logout?came_from=" + wotkit_logout_url + "," + get_logout_success_url()
    
def get_smartstreets_base_url():
    return routes.url_for(strip_domain_url(smarstreets_base_url), qualified=True).replace("/data", "")
    
def get_smartstreets_about_url():
    return routes.url_for(strip_domain_url(smartstreets_about_url), qualified=True).replace("/data", "")

def get_required_config(config, name):
    """ Extract name from config, and throws if it doesn't exist """
    value = config.get(name)
    if not value:
        raise Exception("No %s in configuration .ini file" % name)
    return value

def get_billing_directory():
    return billing_directory