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
Functions in here are accessible via ckan's action API:

New Implemented functions include:
tag_counts,
user_get

Overriden function include (unified login):
user_show,
user_create,
user_update

For guiness, an example could be http://guiness.magic.ubc.ca/data/api/action/tag_counts
tag_counts corresponds to the action defined in this file.

By convention, whenever ckan needs to update the model, it goes through an action of the form:
result = logic.get_action("FUNCTION_NAME")(context, data_dict)

So rather than modifying the model directly, create new actions that wrap it in here, and hook it up via get_actions() in plugin.py.

Perhaps clean up this file and separate authorization and also get, update, create, delete actions for maintainability 
"""


@logic.side_effect_free
def tag_counts(context, data_dict):
    """Get the most popular tag counts (Not all tags). This is a much faster implementation that the current ckan tag counts by directly going into Solr and doing a facet search on tags """
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
def user_get(context, data_dict):
    """Returns the username of the currently logged in user. If not found, raise a not found error. 
    The intended use of this function is to be called by the wotkit with the auth_tkt cookie set. If it is a valid auth_tkt cookie this call returns the username"""
    user_name = context.get("user")
    
    if not user_name:
        raise logic.NotFound
    
    return {"username": user_name}    

@logic.side_effect_free
def user_show(context, data_dict):
    """Override default user_show action to also include wotkit credentials for unified login."""
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
    """Override default user_create action to also include wotkit credentials for unified login."""
    
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
    """Override default user_update action to also include wotkit credentials for unified login."""

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

