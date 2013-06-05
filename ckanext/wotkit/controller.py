import logging
from urllib import quote

from pylons import config

import ckan.lib.i18n as i18n
import ckan.lib.base as base
import ckan.model as model
import ckan.lib.helpers as h
import ckan.new_authz as new_authz
import ckan.logic as logic
import ckan.logic.schema as schema
import ckan.lib.captcha as captcha
import ckan.lib.mailer as mailer
import ckan.lib.navl.dictization_functions as dictization_functions

from ckan.common import _, session, c, g, request

log = logging.getLogger(__name__)

abort = base.abort
render = base.render
validate = base.validate

check_access = logic.check_access
get_action = logic.get_action
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError

DataError = dictization_functions.DataError
unflatten = dictization_functions.unflatten

from ckan.controllers.user import UserController
from ckan.controllers.storage import StorageAPIController

from ckan.lib.jsonp import jsonpify
import json

class HackedStorageAPIController(StorageAPIController):
    """ Dirty hack to deal with the /data URL we use. Ckan has issues with route handling when it doesn't run as route path / """
    
    def get_metadata(self, label):
        metadata_jsonp = super(HackedStorageAPIController, self).get_metadata(label)
        metadata = json.loads(metadata_jsonp)
        metadata["_location"] = metadata["_location"].replace("/data/data", "/data")
        return json.dumps(metadata, sort_keys=True)


class WotkitUserController(UserController):
    """Override default user controller to add Wotkit credentials
    """
    #new_user_form = 'user/register.html'
    def logged_in(self):
        # we need to set the language via a redirect
        lang = session.pop('lang', None)
        session.save()
        came_from = request.params.get('came_from', '')
        log.warning("came from: " + str(came_from))
        # we need to set the language explicitly here or the flash
        # messages will not be translated.
        i18n.set_lang(lang)

        if c.user:
            context = None
            data_dict = {'id': c.user}

            user_dict = get_action('user_show')(context, data_dict)

            h.flash_success(_("%s is now logged in") %
                            user_dict['display_name'])
            if came_from:
                # HACK redirect to ignore the base URL /data
                import routes
                return routes.redirect_to(str(came_from))
            return self.me()
        else:
            err = _('Login failed. Bad username or password.')
            if g.openid_enabled:
                err += _(' (Or if using OpenID, it hasn\'t been associated '
                         'with a user account.)')
            if h.asbool(config.get('ckan.legacy_templates', 'false')):
                h.flash_error(err)
                h.redirect_to(locale=lang, controller='user',
                              action='login', came_from=came_from)
            else:
                return self.login(error=err)

    def _add_wotkit_credentials_to_schema(self, schema):
        schema['wotkit_id'] = [ignore_missing, unicode]
        schema['wotkit_password'] = [ignore_missing, unicode]
        

    def _new_form_to_db_schema(self):
        """
        Defines a custom schema that adds optional wotkit fields to the form.
        """
        schema = super(WotkitUserController, self)._new_form_to_db_schema()
        self._add_wotkit_credentials_to_schema(schema)
        return schema

    def _edit_form_to_db_schema(self):
        """
        Defines a custom schema that adds optional wotkit fields to the form.
        """
        schema = super(WotkitUserController, self)._edit_form_to_db_schema()
        self._add_wotkit_credentials_to_schema(schema)
        return schema
