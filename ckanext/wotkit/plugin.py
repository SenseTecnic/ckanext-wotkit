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
log = getLogger(__name__)

import pprint

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
        

    def configure(self, config):
        """Implements IConfigurable plugin that initializes db tables.
        This gets called after the SQLAlchemy engine is initialized"""
        from model import WotkitUser
        WotkitUser.initDB()
        
    def get_actions(self):
        """Configure ckan action string -> function mapping for this extension"""
        log.debug("Initializing Wotkit Plugin Actions")
        return {"user_show": ckanext.wotkit.actions.user_show,
                "user_update": ckanext.wotkit.actions.user_update,
                "user_create": ckanext.wotkit.actions.user_create,
                "wotkit": ckanext.wotkit.actions.wotkit,
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
    