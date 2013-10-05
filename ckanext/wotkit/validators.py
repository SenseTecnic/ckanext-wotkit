###################################################
#
#	Additional validators used by the plugin
#
###################################################
import re
import ckan.lib.navl.dictization_functions as df
from ckan.common import OrderedDict, _, json, request, c, g, response
from ckan.model import (MAX_TAG_LENGTH, MIN_TAG_LENGTH,
                        PACKAGE_NAME_MIN_LENGTH, PACKAGE_NAME_MAX_LENGTH,
                        PACKAGE_VERSION_MAX_LENGTH,
                        VOCABULARY_NAME_MAX_LENGTH,
                        VOCABULARY_NAME_MIN_LENGTH)

Invalid = df.Invalid
StopOnError = df.StopOnError
Missing = df.Missing
missing = df.missing

# Makes sure the pkg_creator key is set to the current user ID
def validate_creator_field(key, data, errors, context):
	if data[key] == 'pkg_creator':
		# Set the value field of the pkg_creator extras data to the current user id
		data[('extras', key[1], 'value')] = c.userobj.id
	pass

def validate_invisible_field(key, data, errors, context):
    if data[key] == 'pkg_invisible':
		if data[('extras', key[1], 'value')] != ( True or False ):
			data[('extras', key[1], 'value')] = False
	pass

name_match = re.compile('[a-z0-9_\-]*$')
def name_validator(val, context):
	WOTKIT_MIN_NAME_LENGTH = 4

	# check basic textual rules
	if val in ['new', 'edit', 'search']:
		raise Invalid(_('That name cannot be used'))

	if len(val) < WOTKIT_MIN_NAME_LENGTH:
		raise Invalid(_('Name must be at least %s characters long') % WOTKIT_MIN_NAME_LENGTH)
	if len(val) > PACKAGE_NAME_MAX_LENGTH:
		raise Invalid(_('Name must be a maximum of %i characters long') % PACKAGE_NAME_MAX_LENGTH)
	if not name_match.match(val):
		raise Invalid(_('Url must be purely lowercase alphanumeric '
                        '(ascii) characters and these symbols: -_'))
	return val