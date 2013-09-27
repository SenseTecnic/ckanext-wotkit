import pprint
import os
import ckan.lib.base as base
from logging import getLogger 

import ckan.plugins.toolkit as tk
import ckan.model as model
from ckan.common import OrderedDict, _, json, request, c, g, response

from pylons import request
from genshi.input import HTML
from genshi.filters.transform import Transformer

from ckan.plugins import implements, SingletonPlugin, toolkit
from ckan.plugins import (
                          IRoutes,
                          IActions,
                          IConfigurable,
                          IConfigurer,
                          ITemplateHelpers,
                          IMiddleware,
                          IDatasetForm,
                          IAuthFunctions,
                          IPackageController
                          )

import ckanext.wotkit.actions
import ckanext.wotkit.auth
import ckanext.wotkit.validators

auth = ckanext.wotkit.auth
validators = ckanext.wotkit.validators

log = getLogger(__name__)

import config_globals
from billing_log_middleware import BillingLogMiddleware

from routes.mapper import SubMapper

def get_current_user():
    return c.userobj

class WotkitPlugin(SingletonPlugin,tk.DefaultDatasetForm):
    """This plugin contains functions to access Wotkit
    """
    
    implements(ITemplateHelpers, inherit=True)
    implements(IConfigurable, inherit=True)
    implements(IConfigurer, inherit=True)   
    implements(IRoutes, inherit=True)
    implements(IActions, inherit=True)
    implements(IMiddleware, inherit=True)
    implements(IDatasetForm, inherit=True)
    implements(IPackageController, inherit=True)
    implements(IAuthFunctions, inherit=True)

    #-----------------------------------------#
    """ Sensor visibility extension section """
    #-----------------------------------------#

    """ Search and view filter """

    def before_search(self, search_params):
        if 'q' in search_params and search_params['q'] != '':
            other_params = ' AND ' + search_params['q']
        else:
            other_params = ''

        # Only show datasets that are NOT invisible OR are created by the current user
        if c.userobj is None:
            search_params['q'] = '( *:* NOT extras_pkg_invisible:"True" )' + other_params
        else:
            search_params['q'] = '(( *:* NOT extras_pkg_invisible:"True" ) OR ( +extras_pkg_creator:"'+c.userobj.id+'" ))' + other_params
        
        return search_params

    def get_auth_functions(self):
        return {'invisible_package_search' : auth.invisible_package_search,
                'invisible_package_show' : auth.invisible_package_show,
                'package_update' : auth.require_creator_to_update
                }

    def after_show(self, context, pkg_dict):
        tk.check_access('invisible_package_show', context, pkg_dict)
        return pkg_dict

    """ Dataset schema invisibility field """

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    def create_package_schema(self):
        schema = super(WotkitPlugin, self).create_package_schema()
        schema.update({
            'pkg_invisible': [
                tk.get_validator('ignore_missing'),
                tk.get_converter('convert_to_extras')
                ],
            'pkg_creator' : [
                tk.get_validator('ignore_missing'),
                tk.get_converter('convert_to_extras')
                ],
            'extras' : {
                'id' : [tk.get_validator('ignore')],
                'key' : [
                            tk.get_validator('ignore_missing'),
                            unicode,
                            validators.validate_creator_field,
                            validators.validate_invisible_field
                        ],
                'value' : [ 
                            tk.get_validator('ignore_missing'), 
                          ],
                'state' : [tk.get_validator('ignore')],
                'deleted' : [tk.get_validator('ignore_missing')],
                'revision_timestamp' : [tk.get_validator('ignore')]
            }
        })

        return schema

    def update_package_schema(self):
        schema = super(WotkitPlugin, self).update_package_schema()
        schema.update({
            'pkg_invisible': [
                tk.get_validator('ignore_missing'),
                tk.get_converter('convert_to_extras')
                ],
            'pkg_creator' : [
                tk.get_validator('ignore_missing'),
                tk.get_converter('convert_to_extras')
                ],
            'extras' : {
                'id' : [tk.get_validator('ignore')],
                'key' : [
                            tk.get_validator('ignore_missing'),
                            unicode,
                            validators.validate_creator_field,
                            validators.validate_invisible_field
                        ],
                'value' : [ 
                            tk.get_validator('ignore_missing')
                          ],
                'state' : [tk.get_validator('ignore')],
                'deleted' : [tk.get_validator('ignore_missing')],
                'revision_timestamp' : [tk.get_validator('ignore')]
            }
        })

        return schema

    def show_package_schema(self):
        schema = super(WotkitPlugin, self).show_package_schema()
        schema.update({
            'pkg_invisible': [
                tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')
                ],
            'pkg_creator' : [
                tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')
                ]
            })
        return schema

    """ End of dataset visibility section
    """

    def make_middleware(self, app, config):
        """IMiddleware extension. This essentially plugs in before the application starts (where we intercept request/response for billing)"""
        app = BillingLogMiddleware(app, config)
        return app
        
    
    # Additional template helper functions this plugin provides
    def get_helpers(self):
        """ From html templates, we can access these functions through h: 
        example: h.wotkit_url(), h.logout_all_url()
        """
        
        return {'get_current_user' : get_current_user,
        		'ckan_url': config_globals.get_ckan_url,
                'wotkit_url': config_globals.get_wotkit_url,
                'wotkit_api_url': config_globals.get_wotkit_api_url,
                'logout_all_url': config_globals.get_logout_all_url,
                'logout_success_url:': config_globals.get_logout_success_url,
                'smartstreets_base_url': config_globals.get_smartstreets_base_url,
                'smartstreets_about_url': config_globals.get_smartstreets_about_url}
    
    def update_config(self, config):
        """Add template directory of this extension to override the default ckan templates with IConfigurer plugin."""
        #Probably have to add directories for css / jscript files later
        toolkit.add_template_directory(config, "theme/templates")

    def configure(self, config):
        """Implements IConfigurable plugin that initializes db tables.
        This gets called after the SQLAlchemy engine is initialized"""
        
        # Check config file for wotkit related configs and set them
        config_globals.init(config)
        
    def get_actions(self):
        """Configure ckan action string -> function mapping for this extension with IActions plugin"""
        #log.debug("Initializing Wotkit Plugin Actions")
        return {"user_update": ckanext.wotkit.actions.user_update,
                "user_create": ckanext.wotkit.actions.user_create,
                "user_show": ckanext.wotkit.actions.user_show,
                "tag_counts": ckanext.wotkit.actions.tag_counts,
                "user_get": ckanext.wotkit.actions.user_get}
    
    def before_map(self, map):
        """This IRoutes implementation overrides the standard behavior of user information to make unified login work.
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
        
        # The storage API controller was modified to make proper urls. In our case, we had issues when running under /data which appended urls to be /data/data so I had to change it.
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


