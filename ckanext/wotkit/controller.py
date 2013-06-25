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
from ckan.logic.schema import ignore_missing
import ckan.lib.captcha as captcha
import ckan.lib.mailer as mailer
import ckan.lib.navl.dictization_functions as dictization_functions

from ckan.common import _, session, c, g, request, response

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

from pytz import common_timezones

from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin
import config_globals
import routes

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
        #log.warning("came from: " + str(came_from))
        # we need to set the language explicitly here or the flash
        # messages will not be translated.
        i18n.set_lang(lang)

        if c.user:
            context = None
            data_dict = {'id': c.user, 'link_wotkit': True}
            try:
                user_dict = get_action('user_show')(context, data_dict)
            except logic.NotAuthorized as e:
                return self.login(error=str(e))

            h.flash_success(_("%s is now logged in") %
                            user_dict['display_name'])
            if came_from:
                # HACK redirect to ignore the base URL /data
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

    def logout(self):
        """
        When user logs out, this is the first function that is hit when the URL is .../_logout
        came_from parameter is a comma separated list of logout redirects that are redirected in order.        
        """
        # save our language in the session so we don't lose it
        session['lang'] = request.environ.get('CKAN_LANG')
        
        # Save in session HACK
        came_from = request.params.get('came_from', '')
        session['logout_came_from'] = came_from
        session.save()
        
        h.redirect_to(self._get_repoze_handler('logout_handler_path'))

    def logged_out(self):
        """
        Accounts came_from. If specified, logs out of ckan only. If not specified, logs out of both ckan and wotkit.
        """
        # we need to get our language info back and the show the correct page
        lang = session.get('lang')
        came_from = session.get('logout_came_from')
        log.debug("came from: " + str(came_from))
        c.user = None
        session.delete()
        if came_from:
            # extract came_from

            (next_redirect_url, comma, remaining_came_from) = came_from.partition(',')
            if remaining_came_from:
                redirect_url = next_redirect_url + "?came_from=" + remaining_came_from
            else:
                redirect_url = next_redirect_url
            log.debug("redirecting logout to: " + redirect_url)
            routes.redirect_to(str(redirect_url))
        else:
            # redirect user to logout url
            url = config_globals.get_logout_success_url()
            routes.redirect_to(str(url))

    def _add_wotkit_credentials_to_schema(self, schema):
        schema['timezone'] = [ignore_missing, unicode]

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

    def edit(self, id=None, data=None, errors=None, error_summary=None):
        context = {'save': 'save' in request.params,
                   'schema': self._edit_form_to_db_schema(),
                   }
        if id is None:
            if c.userobj:
                id = c.userobj.id
            else:
                abort(400, _('No user specified'))
        data_dict = {'id': id, "link_wotkit": True}

        if (context['save']) and not data:
            return self._save_edit(id, context)

        try:
            old_data = get_action('user_show')(context, data_dict)

            schema = self._db_to_edit_form_schema()
            if schema:
                old_data, errors = validate(old_data, schema)

            c.display_name = old_data.get('display_name')
            c.user_name = old_data.get('name')

            data = data or old_data

        except NotAuthorized:
            abort(401, _('Unauthorized to edit user %s') % '')
        except NotFound:
            abort(404, _('User not found'))

        user_obj = context.get('user_obj')

        if not (new_authz.is_sysadmin(c.user)
                or c.user == user_obj.name):
            abort(401, _('User %s not authorized to edit %s') %
                  (str(c.user), id))

        errors = errors or {}
        data["timezones"] = common_timezones
        vars = {'data': data, 'errors': errors, 'error_summary': error_summary}
        self._setup_template_variables({'model': model,
                                        'session': model.Session,
                                        'user': c.user or c.author},
                                        data_dict)

        c.is_myself = True
        c.show_email_notifications = h.asbool(
            config.get('ckan.activity_streams_email_notifications'))
        c.form = render(self.edit_user_form, extra_vars=vars)

        return render('user/edit.html')

    def new(self, data=None, errors=None, error_summary=None):
        '''GET to display a form for registering a new user.
           or POST the form data to actually do the user registration.
        '''
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'schema': self._new_form_to_db_schema(),
                   'save': 'save' in request.params}

        try:
            check_access('user_create', context)
        except NotAuthorized:
            abort(401, _('Unauthorized to create a user'))

        if context['save'] and not data:
            return self._save_new(context)

        if c.user and not data:
            # #1799 Don't offer the registration form if already logged in
            return render('user/logout_first.html')

        data = data or {}
        errors = errors or {}
        error_summary = error_summary or {}
        data["timezones"] = common_timezones
        vars = {'data': data, 'errors': errors, 'error_summary': error_summary}

        c.is_sysadmin = new_authz.is_sysadmin(c.user)
        c.form = render(self.new_user_form, extra_vars=vars)
        return render('user/new.html')

