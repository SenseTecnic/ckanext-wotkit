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
_get_action = logic.get_action
_check_access = logic.check_access

from ckan.controllers.user import UserController
from ckan.lib.navl.validators import not_empty
from ckan.lib.navl.validators import ignore_missing

class WotkitUserController(UserController):
    """Override default user controller to add Wotkit credentials
    """
    #new_user_form = 'user/register.html'

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
