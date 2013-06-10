import os
from logging import getLogger

from pylons import request
from genshi.input import HTML
from genshi.filters.transform import Transformer

from ckan.plugins import implements, SingletonPlugin, toolkit

from ckan.plugins import IRoutes
from ckan.plugins import IActions
from ckan.plugins import IAuthFunctions
from ckan.plugins import IConfigurable
from ckan.plugins import IConfigurer
from ckan.plugins import ITemplateHelpers

import ckanext.wotkit.actions
import ckanext.wotkit.wotkit_proxy
log = getLogger(__name__)

import pprint


from routes.mapper import SubMapper

class WotkitPlugin(SingletonPlugin):
    """This plugin contains functions to access Wotkit
    """

    implements(IConfigurable, inherit=True)
    implements(IConfigurer, inherit=True)   
    implements(IRoutes, inherit=True)
    implements(IActions, inherit=True)
    implements(IAuthFunctions, inherit=True)
    
    
    def update_config(self, config):
        """Add template directory of this extension to override the default ckan templates"""
        #Probably have to add directories for css / jscript files later
        toolkit.add_template_directory(config, "theme/templates")
        pass

    def configure(self, config):
        """Implements IConfigurable plugin that initializes db tables.
        This gets called after the SQLAlchemy engine is initialized"""
        
        # Check config file for wotkit related configs and set them
        if not config.get("wotkit.wotkit_url"):
            raise Exception("No wotkit.url in configuration .ini file")
        if not config.get("wotkit.api_url"):
            raise Exception("No wotkit.api_url in configuration .ini file")
        if not config.get("wotkit.processor_url"):
            raise Exception("No wotkit.processor_url in configuration .ini file")
        
        if not config.get("wotkit.admin_id"):
            raise Exception("No wotkit.harvest_id in configuration .ini file")
        if not config.get("wotkit.admin_key"):
            raise Exception("No wotkit.harvest_key in configuration .ini file")

        import sensors.sensetecnic as sensetecnic
        # Somewhat redundant for now.. initializing in both places
        sensetecnic.init(config.get("wotkit.wotkit_url"), config.get("wotkit.api_url"), config.get("wotkit.processor_url"), config.get("wotkit.admin_id"), config.get("wotkit.admin_key"))                
        ckanext.wotkit.wotkit_proxy.initWotkitUrls(config.get("wotkit.wotkit_url"), config.get("wotkit.api_url"), config.get("wotkit.processor_url"), config.get("wotkit.admin_id"), config.get("wotkit.admin_key"))
        
        from model import WotkitUser
        log.debug("Initializing wotkit db")
        WotkitUser.initDB()
        
    def get_actions(self):
        """Configure ckan action string -> function mapping for this extension"""
        #log.debug("Initializing Wotkit Plugin Actions")
        return {"user_update": ckanext.wotkit.actions.user_update,
                "user_create": ckanext.wotkit.actions.user_create,
                "wotkit": ckanext.wotkit.actions.wotkit,
                "wotkit_harvest_module": ckanext.wotkit.actions.wotkit_harvest_module,
                "wotkit_get_sensor_module_import": ckanext.wotkit.actions.wotkit_get_sensor_module_import,
                "user_wotkit_credentials": ckanext.wotkit.actions.user_wotkit_credentials}
    
    def get_auth_functions(self):
        """Configure ckan authorization check functions for actions in this extension."""
        log.debug("Initializing Wotkit Plugin Authorization Function")
        return {"wotkit":ckanext.wotkit.actions.ckanAuthorization,
                "user_wotkit_credentials":ckanext.wotkit.actions.ckanAuthorization}
    
    
    def before_map(self, map):
        """This IRoutes implementation overrides the standard behavior of user information.
        Adds a WotkitUserController that overrides the default, that includes wotkit credentials
        """
        # Hook in our custom user controller at the points of creation
        # and edition.

        map.connect('/user/logged_in',
                    controller="ckanext.wotkit.controller:WotkitUserController",
                    action='logged_in')
        
        map.connect('/user/_logout', 
                    controller="ckanext.wotkit.controller:WotkitUserController", 
                    action='logout')
        map.connect('/user/logged_out', 
                    controller="ckanext.wotkit.controller:WotkitUserController", 
                    action='logged_out')
        
        GET = dict(method=['GET'])
        with SubMapper(map, controller='ckanext.wotkit.controller:HackedStorageAPIController') as m:
            m.connect('storage_api_get_metadata', '/api/storage/metadata/{label:.*}',
                      action='get_metadata', conditions=GET)

        
        map.connect('/user/register',
                    controller="ckanext.wotkit.controller:WotkitUserController",
                    action='register')
        
        map.connect('/user/edit',
                    controller='ckanext.wotkit.controller:WotkitUserController',
                    action='edit')
                
        map.connect('/user/edit/{id:.*}',
                    controller='ckanext.wotkit.controller:WotkitUserController',
                    action='edit')
           
        #map.connect('/package/new', controller='package_formalchemy', action='new')
        #map.connect('/package/edit/{id}', controller='package_formalchemy', action='edit')
        return map
    