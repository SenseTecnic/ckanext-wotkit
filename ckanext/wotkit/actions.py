import sys
from ckan.lib.base import request
from ckan.lib.base import c, g, h
from ckan.lib.base import model
from ckan.lib.base import render
from ckan.lib.base import _

from ckan.lib.navl.validators import not_empty

from logging import getLogger

import ckan.logic as logic

import ckan.lib.dictization.model_dictize as model_dictize
import ckan.lib.dictization 
import wotkit_proxy
from model import WotkitUser


log = getLogger(__name__)
_get_or_bust = logic.get_or_bust
_get_action = logic.get_action
_check_access = logic.check_access


"""
Functions in here are mostly accessible via ckan's action API:
By convention, whenever ckan needs to update the model, it goes through an action of the form:
result = logic.get_action("FUNCTION_NAME")(context, data_dict)

So rather than modifying the model directly, create new actions that wrap it in here, and hook it up via plugin.py

Perhaps clean up this file and separate authorization and also get, update, create, delete actions for maintainability 
"""

def ckanAuthorization(context, data_dict):
    """The authorization function linked with wotkit action api calls. 
    For now it checks ckan and wotkit credentials.
    """
    
    #Simply check if user is logged in, and also has a wotkit account mapping
    user = context['user']
    
    if user:
        return {'success': True}
    else:    
        return {'success': False, 'msg': _('Not authorized')}
    
    #authorized_user = model.User.get(context.get('user'))

    # Any user is authorized to see what she herself is following.
    #requested_user = model.User.get(data_dict.get('id'))

@logic.side_effect_free
def user_show(context, data_dict):
    """Override default user_show action to also include wotkit credentials"""
    # Call default user_show, which handles authorization
    user_dict = logic.action.get.user_show(context, data_dict)
    wotkit_dict = _get_action("user_wotkit_credentials")(context, data_dict)
    user_dict["wotkit_id"] = wotkit_dict.get("wotkit_id", None)
    user_dict["wotkit_password"] = wotkit_dict.get("wotkit_password", None)
    return user_dict

def user_create(context, data_dict):
    """Override default user_create action to also include wotkit credentials"""
    
    # Call parent method, this should handle authorization and rollback on error
    user_dict = logic.action.create.user_create(context, data_dict)

    user_model = context["user_obj"]
    
    wotkit_create_dict = {"ckan_id": user_model.id, 
                          "wotkit_id": data_dict["wotkit_id"], 
                          "wotkit_password": data_dict["wotkit_password"]}
    ckan.lib.dictization.table_dict_save(wotkit_create_dict, WotkitUser, context)
    
    if not context.get('defer_commit'):
        model.repo.commit()

    return user_dict.update(wotkit_create_dict);
    
    
def user_update(context, data_dict):
    """Override default user_update action to also include wotkit credentials"""
    #Get current user ID
    user_model = model.User.get(context["user"])

    if user_model is None:
        raise NotFound('User was not found.')
    
        
    # Populate database row to update
    wotkit_update_dict = {"ckan_id": user_model.id, 
                          "wotkit_id": data_dict["wotkit_id"], 
                          "wotkit_password": data_dict["wotkit_password"]}    
    
    # Check if this is an update or a new row in wotkit_user table
    wotkit_credentials = _get_action("user_wotkit_credentials")(context, data_dict)
    if "id" in wotkit_credentials:
        wotkit_update_dict["id"] = wotkit_credentials["id"]
        
    # Update
    ckan.lib.dictization.table_dict_save(wotkit_update_dict, WotkitUser, context) 
    
    # For now, authorization and validity is checked in the parent function. 
    # This should be ok since the above database update will rollback if there is an error
    updated_user = logic.action.update.user_update(context, data_dict)
    return updated_user
    
@logic.side_effect_free
def user_wotkit_credentials(context, data_dict):
    """Return dictionary of wotkit credentials of current user.
    :rtype: dictionary
    """
    _check_access("user_wotkit_credentials", context, data_dict)
    user = context['user']
    user_model = model.User.get(user)
    result = WotkitUser.get(user_model.id)
    
    if result:
        return_dict = {"id": result.id, "wotkit_id": result.wotkit_id, "wotkit_password": result.wotkit_password}
    else:
        return_dict = {};
    return return_dict

@logic.side_effect_free
def wotkit(context, data_dict):
    """Proxy API to Wotkit
    """
    
    _check_access("wotkit", context, data_dict)
    
    #get username for logged in user
    user = context['user']

    wotkit_credentials = None
    if user:
        wotkit_credentials = _get_action("user_wotkit_credentials")(context, data_dict)
        if not wotkit_credentials or not wotkit_credentials["wotkit_id"] or not wotkit_credentials["wotkit_password"]:
            raise logic.NotFound("Wotkit credentials not found for ckan user")
    
    sensor_name = data_dict.get("sensor", None)
    if sensor_name:
        result = wotkit_proxy.getSensor(wotkit_credentials["wotkit_id"], wotkit_credentials["wotkit_password"], sensor_name)
    else:
        
        # this is api proxy with everything after the api path specified
        url_path = _get_or_bust(data_dict, "url")
        method = data_dict.get("method", None)
        data = data_dict.get("data", None)
        
        if url_path:
            result = wotkit_proxy.proxyParameters(wotkit_credentials["wotkit_id"], wotkit_credentials["wotkit_password"], url_path, method, data)
                
        
    returnJson = {"Ckan User": user, "Wotkit User": wotkit_credentials, "Response": result}
    return returnJson
