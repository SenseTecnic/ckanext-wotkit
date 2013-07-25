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
import ckan.lib.dictization.model_save as model_save
import ckan.lib.dictization 

from model import WotkitUser

from ckan.plugins import toolkit
import json
import ckan.lib.search as search

log = getLogger(__name__)
_get_or_bust = logic.get_or_bust
_get_action = logic.get_action
_check_access = logic.check_access

import importlib
from pylons import config
import config_globals

import ckan.lib.navl.dictization_functions

_validate = ckan.lib.navl.dictization_functions.validate
ValidationError = logic.ValidationError
NotFound = logic.NotFound

    
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
def tag_counts(context, data_dict):
    """Get the most popular tag counts. (Not all tags)"""
    from ckan.lib.search.common import make_connection, SearchError, SearchQueryError

    query = {
        'rows': 0,
        'q': '*:*',
        'wt': 'json',
        'fq': 'site_id:"%s"' % config.get('ckan.site_id'),
        'facet': 'true',
        'facet.field': 'tags'}

    try:
        conn = make_connection()
        solr_response = conn.raw_query(**query)
        data = json.loads(solr_response)
        
        results = []
        solr_tags = data["facet_counts"]["facet_fields"]["tags"]
        for index in range(0,len(solr_tags),2):
            results.append([solr_tags[index], solr_tags[index+1]])

    except Exception as e:
        raise SearchError("Failed to obtain and parse tag counts. " + str(e))
    
    return results

@logic.side_effect_free
def user_show(context, data_dict):
    """Override default user_show action to also include wotkit credentials"""
    # Call default user_show, which handles authorization
    user_dict = logic.action.get.user_show(context, data_dict)
    
    # only check wotkit account if we need to
    if data_dict.get("link_wotkit", False):
        wotkit_proxy = config_globals.get_wotkit_proxy()
        wotkit_account = wotkit_proxy.get_wotkit_user(data_dict["id"])
        if not wotkit_account:
            raise logic.NotAuthorized("Failed to query wotkit account for user: %s" % data_dict["id"])
        user_dict["timezone"] = wotkit_account["timeZone"]

        #raise logic.ValidationError({"Failed to query wotkit account for user": " "})
    #wotkit_dict = _get_action("user_wotkit_credentials")(context, data_dict)
    #user_dict["wotkit_id"] = wotkit_dict.get("wotkit_id", None)
    #user_dict["wotkit_password"] = wotkit_dict.get("wotkit_password", None)
    return user_dict

def user_create(context, data_dict):
    """Override default user_create action to also include wotkit credentials"""
    
    # Temporarily defer commits so we can reuse code and rollback if wotkit problems
    prev_defer_commit = context.get("defer_commit")
    context["defer_commit"] = True
    
    session = context['session']
    # Call parent method, this should handle authorization and rollback on error    
    model = context['model']
    schema = context.get('schema') or ckan.logic.schema.default_user_schema()

    _check_access('user_create', context, data_dict)

    data, errors = _validate(data_dict, schema, context)

    if errors:
        session.rollback()
        raise ValidationError(errors)

    user = model_save.user_dict_save(data, context)
    
    wotkit_proxy = config_globals.get_wotkit_proxy()
    if wotkit_proxy.get_wotkit_user(user.name):
        session.rollback()
        raise logic.ValidationError({"User already exists in wotkit": " "})
    
 
    data = {"username": user.name,
            "password": user.password1,
            "email": user.email,
            "firstname": user.fullname,
            "lastname": " ",
            "timeZone": data_dict["timezone"]}
    
    try:
        wotkit_proxy.create_wotkit_user(data)
        log.debug("Success creating wotkit account")
    except Exception as e:
        log.debug("Failed creating wotkit account")
        session.rollback()
        raise logic.ValidationError({"Failed user creation in wotkit": " "})
    
    # Flush the session to cause user.id to be initialised, because
    # activity_create() (below) needs it.
    session.flush()

    activity_create_context = {
        'model': model,
        'user': context['user'],
        'defer_commit': True,
        'session': session
    }
    activity_dict = {
            'user_id': user.id,
            'object_id': user.id,
            'activity_type': 'new user',
            }
    logic.get_action('activity_create')(activity_create_context,
            activity_dict, ignore_auth=True)

    if not context.get('defer_commit'):
        model.repo.commit()

    # A new context is required for dictizing the newly constructed user in
    # order that all the new user's data is returned, in particular, the
    # api_key.
    #
    # The context is copied so as not to clobber the caller's context dict.
    user_dictize_context = context.copy()
    user_dictize_context['keep_sensitive_data'] = True
    user_dict = model_dictize.user_dictize(user, user_dictize_context)

    context['user_obj'] = user
    context['id'] = user.id

    model.Dashboard.get(user.id) #  Create dashboard for user.

    log.debug('Created user {name}'.format(name=user.name))
    

    #wotkit_create_dict = {"ckan_id": user_model.id, 
    #                      "wotkit_id": data_dict["wotkit_id"], 
    #                      "wotkit_password": data_dict["wotkit_password"]}
    #ckan.lib.dictization.table_dict_save(wotkit_create_dict, WotkitUser, context)
    
    if not prev_defer_commit:
        model.repo.commit()

    context["defer_commit"] = prev_defer_commit
    return user_dict
    
    
def user_update(context, data_dict):
    """Override default user_update action to also include wotkit credentials"""

    #Get current user ID
    id = _get_or_bust(data_dict, 'id')

    user_model = model.User.get(id)
    session = context['session']

    if user_model is None:
        raise logic.ValidationError({'User was not found in ckan model.': " "})
    
    wotkit_proxy = config_globals.get_wotkit_proxy()
    wotkit_account = wotkit_proxy.get_wotkit_user(user_model.name)
    if not wotkit_account:
        raise logic.ValidationError({'User was not found in the Wotkit, make sure username %s exists in Wotkit' % user_model.name: " "})
    
    
    if user_model.name != data_dict["name"]:
        raise logic.ValidationError({"username is unchangeable since ckan account is linked with wotkit account by name": " "})
    
    # Temporarily defer commits so we can reuse code and rollback if wotkit problems
    prev_defer_commit = context.get("defer_commit")
    context["defer_commit"] = True
    
    # For now, authorization and validity is checked in the parent function. 
    # This should be ok since the above database update will rollback if there is an error
    try:
        updated_user = logic.action.update.user_update(context, data_dict)
                
        wotkit_update_data = {"email": updated_user["email"],
                              "firstname": updated_user["fullname"],
                              "lastname": " "}
        
        if "timezone" in data_dict:
            wotkit_update_data["timeZone"] = data_dict["timezone"]
        
        if "password1" in data_dict and data_dict["password1"]:
            wotkit_update_data["password"] = data_dict["password1"]
        elif "password" in data_dict and data_dict["password"]:
            wotkit_update_data["password"] = data_dict["password"]
    
        # need to update by id, not by name here
        wotkit_proxy.update_wotkit_user(str(wotkit_account["id"]), wotkit_update_data)
        
    except Exception as e:
        session.rollback()
        raise logic.ValidationError({"Error in user update: " + str(e): " "})
    
    if not prev_defer_commit:
        model.repo.commit()
        
    context["defer_commit"] = prev_defer_commit
    return updated_user

@logic.side_effect_free
def user_get(context, data_dict):
    """Returns the username of the currently logged in user"""
    user_name = context.get("user")
    
    if not user_name:
        raise logic.NotFound
    
    return {"username": user_name}    

    
'''
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

def _getWotkitCredentials(context, data_dict):
    """ Handles extraction of wotkit credentials """
    #get username for logged in user
    user = context['user']

    wotkit_credentials = {}
    if all(key in data_dict for key in ("wotkit_id", "wotkit_password")):
        wotkit_credentials["wotkit_id"] = data_dict["wotkit_id"]
        wotkit_credentials["wotkit_password"] = data_dict["wotkit_password"]
        
    if not wotkit_credentials and user:
        wotkit_credentials = _get_action("user_wotkit_credentials")(context, data_dict)
        if not wotkit_credentials or not wotkit_credentials["wotkit_id"] or not wotkit_credentials["wotkit_password"]:
            raise logic.NotFound("Wotkit credentials not found for ckan user")
    return wotkit_credentials

@logic.side_effect_free
def wotkit(context, data_dict):
    """Proxy API to Wotkit
    """
    
    _check_access("wotkit", context, data_dict)
    
    wotkit_credentials = _getWotkitCredentials(context, data_dict)
    
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
                
        
    returnJson = {"Response": result}
    return returnJson
'''

def wotkit_harvest_module(context, data_dict):
    """ Harvests sensor data and pushes it into wotkit and creates a package in ckan.
    The Harvesting mechanism searches for a module that matches the "module" field provided in data_dict in ./sensors/
    The modules must have a method called "updateWotkit()" defined, which must return a list of sensor names that were updated
    """

    # Only the harvest user can load modules for now, module must be supplied in data_dict
    module = _get_action("wotkit_get_sensor_module_import")(context, data_dict)
    
    # All wotkit modules defined with updateWotkit function (ducktyping)
    # Must return list of sensor names that corresponds to {WOTKIT_API_URL}/sensors/{SENSOR_NAME_HERE} for wotkit api access
    updated_sensors = []
    try:
        updated_sensors = module.updateWotkit()
    except Exception as e:
        log.error("Failed to get and update wotkit for module " + data_dict["module"] + ". " + e.message)
        raise e
    
    package_dict = {
                    'resources': []
    }


def wotkit_get_sensor_module_import(context, data_dict):
    user = context["user"]
    if not user == "harvest":
        raise Exception("Only harvest user can call harvest modules")
    
    if not "module" in data_dict:
        raise Exception("No module defined for harvesting wotkit sensor data.")
    
    module = importlib.import_module("ckanext.wotkit.sensors." + data_dict["module"], "ckanext")
    return module