import os
from logging import getLogger

from pylons import request
from genshi.input import HTML
from genshi.filters.transform import Transformer

from ckan.plugins import implements, SingletonPlugin


from ckan.plugins import IRoutes
from ckan.plugins import IActions
from ckan.plugins import IAuthFunctions

log = getLogger(__name__)

import pprint
import ckanext.wotkit.controller            


class WotkitPlugin(SingletonPlugin):
    """This plugin contains functions to access Wotkit
    """

    #implements(IRoutes, inherit=True)
    implements(IActions, inherit=True)
    implements(IAuthFunctions, inherit=True)

        
    def get_actions(self):
        log.debug("Initializing Wotkit Plugin Actions")
        return {"wotkit":ckanext.wotkit.controller.search}
    
    def get_auth_functions(self):
        log.debug("Initializing Wotkit Plugin Authorization Function")
        return {"wotkit":ckanext.wotkit.controller.ckanAuthorization}
    
    '''
    def before_map(self, map):
        """This IRoutes implementation overrides the standard
        ``/user/register`` behaviour with a custom controller.  You
        might instead use it to provide a completely new page, for
        example.

        Note that we have also provided a custom register form
        template at ``theme/templates/user/register.html``.
        """
        log.debug(pprint.pformat(map))

        # Hook in our custom user controller at the points of creation
        # and edition.
        map.connect('/api/wotkit',
                        
                    controller='ckanext.wotkit.controller:CustomUserController',
                    action='register')

        #map.connect('/package/new', controller='package_formalchemy', action='new')
        #map.connect('/package/edit/{id}', controller='package_formalchemy', action='edit')
        return map
    '''