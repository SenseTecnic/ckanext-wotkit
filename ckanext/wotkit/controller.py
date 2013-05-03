import sys
from ckan.lib.base import request
from ckan.lib.base import c, g, h
from ckan.lib.base import model
from ckan.lib.base import render
from ckan.lib.base import _

from ckan.lib.navl.validators import not_empty

from logging import getLogger

import ckan.logic as logic

log = getLogger(__name__)
_get_or_bust = logic.get_or_bust
_check_access = logic.check_access

import wotkit_proxy

_ckan_user_to_wotkit = {"admin":("root", "aMUSEment2")}
#_ckan_user_to_wotkit = {"nooo":("yes", "badpasswd")}
                        
#_ckan_user_to_wotkit = {}

def ckanAuthorization(context, data_dict):
    #Simply check if user is logged in, and also has a wotkit account mapping
    user = context['user']
    
    if user:
        wotkit_account = _ckan_user_to_wotkit.get(user, None)
        if wotkit_account:
            return {'success': True}
        else:
            #return {'success': True}
            return {'success': False, 'msg': _('Not authorized')}
    else:    
        return {'success': False, 'msg': _('Not authorized')}
    
    #authorized_user = model.User.get(context.get('user'))

    # Any user is authorized to see what she herself is following.
    #requested_user = model.User.get(data_dict.get('id'))

@logic.side_effect_free
def search(context, data_dict):
    """Proxy API to Wotkit
    """
    
    _check_access("wotkit", context, data_dict)
    
    #get username for logged in user
    user = context['user']
    
    sensor_name = _get_or_bust(data_dict, "sensor")
    
    wotkit_credentials = None
    if user:
        wotkit_credentials = _ckan_user_to_wotkit.get(user, None)
        if not wotkit_credentials:
            raise logic.NotFound("Wotkit credentials not found for ckan user")
    
            
    result = wotkit_proxy.getSensor(wotkit_credentials[0], wotkit_credentials[1], sensor_name)
    returnJson = {"Ckan User": user, "Wotkit User": wotkit_credentials, "Response": result}
    return returnJson
    
'''
class WotkitController(ApiController):
    """Controller that defines actions for the Wotkit
    """
        
    def __call__(self, environ, start_response):
        params=dict(request.params)
        
        function = logic.get_or_bust(params, "action")
        
        
        
        log.debug(params)
        log.debug(function)
        return ApiController.__call__(self, environ, start_response)
'''                