###################################################
#
#	Additional validators used by the plugin
#
###################################################
import re
import ckan.lib.navl.dictization_functions as df
import ckan.plugins.toolkit as tk

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
def convert_to_extras_custom(key, data, errors, context):

	# get the current number of extras field
	unflattened = df.unflatten(data)

	if("extras" in unflattened):
		extras_count = len(unflattened['extras'])
	else:
		extras_count = 0

	data.update({
		('extras', (extras_count), 'id') : [tk.get_validator('ignore')],
		('extras', (extras_count), 'revision_timestamp') : [tk.get_validator('ignore')],
		('extras', (extras_count), 'state') : [tk.get_validator('ignore')],
		('extras', (extras_count), 'deleted') : [], # this needs to be blank so the fields won't be deleted
		})

	if key[-1] == "pkg_creator":
		data.update({
			('extras', (extras_count), 'key') : key[-1],
			('extras', (extras_count), 'value') : c.userobj.id
			})
	elif key[-1] == "pkg_invisible":
		if data[key] != ( "True" or "False" ):
			data[key] = "False"
		data.update({
			('extras', (extras_count), 'key') : key[-1],
			('extras', (extras_count), 'value') : data[key]
			})
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