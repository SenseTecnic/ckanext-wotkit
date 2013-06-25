import ckanext.wotkit.wotkit_proxy as wotkit_proxy

'''

This file contains all configuration globals used in ckan-wotkit hub.

Additional important functions include storing all connections to wotkit instances.
When a wotkit-harvester update is run, data is sent to all wotkit proxies defined.

init should be called on initialization
'''

# globals for now, access these through getter functions implemented in this file
wotkit_proxies = []

wotkit_url = None
wotkit_api_url = None
ckan_url = None
smarstreets_base_url = None
smartstreets_about_url = None
logout_success_url = None

# wotkit admin credentials used for managing users
wotkit_admin_id = None
wotkit_admin_key = None

def init(config):
    """
    Initializes global URL's used. Input config is supplied from plugin.py and is read from the configuration .ini file
    """
    global wotkit_url, wotkit_api_url, ckan_url, smarstreets_base_url, smartstreets_about_url, logout_success_url
    global wotkit_admin_id, wotkit_admin_key
    
    wotkit_url = get_required_config(config, "wotkit.wotkit_url")
    wotkit_api_url = get_required_config(config, "wotkit.api_url")
    
    ckan_url = get_required_config(config, "ckan.site_url")
    smarstreets_base_url = get_required_config(config, "smartstreets.base_url")
    smartstreets_about_url = get_required_config(config, "smartstreets.about_url")
    logout_success_url = get_required_config(config, "ckan.logout_success_url")
    
    wotkit_admin_id = get_required_config(config, "wotkit.admin_id")
    wotkit_admin_key = get_required_config(config, "wotkit.admin_key")  

    
    global wotkit_proxies    
    wotkit_proxy_config = wotkit_proxy.WotkitConfig(wotkit_url, wotkit_api_url, "", wotkit_admin_id, wotkit_admin_key)
    wotkit_proxies.append(wotkit_proxy.WotkitProxy(wotkit_proxy_config))
    
    # TODO: for now we run harvester on one machine, and copy the wotkit data to production 
    wotkit_second_api_url = config.get("wotkit.api_url_copy")
    # Assumes same username
    if wotkit_second_api_url:
        wotkit_proxy_config2 = wotkit_proxy.WotkitConfig("", wotkit_second_api_url, "", wotkit_admin_id, wotkit_admin_key)
        wotkit_proxies.append(wotkit_proxy.WotkitProxy(wotkit_proxy_config2))
                              

def get_wotkit_proxy():
    """ get main proxy """
    return wotkit_proxies[0]    

def get_wotkit_proxies():
    """ get all proxies """
    return wotkit_proxies

def get_wotkit_admin_credentials():
    return (wotkit_admin_id, wotkit_admin_key)
    
def get_wotkit_url():
    return wotkit_url
    
def get_wotkit_api_url():
    return wotkit_api_url

def get_logout_success_url():
    return logout_success_url

def get_logout_all_url():
    """ Logout URL that triggers the redirects done to logout of all wotkit, ckan sites. """
    wotkit_logout_url = wotkit_url + "/logout/bridge"
    return ckan_url + "/user/_logout?came_from=" + wotkit_logout_url + "," + logout_success_url
    
def get_smartstreets_base_url():
    return smarstreets_base_url
    
def get_smartstreets_about_url():
    return smartstreets_about_url

def get_required_config(config, name):
    """ Extract name from config, and throws if it doesn't exist """
    value = config.get(name)
    if not value:
        raise Exception("No %s in configuration .ini file" % name)
    return value
