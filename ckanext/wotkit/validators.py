###################################################
#
#	Additional validators used by the plugin
#
###################################################
import pprint
import ckan.lib.navl.dictization_functions as df
from ckan.common import OrderedDict, _, json, request, c, g, response

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

def name_validator(val, context):
    # check basic textual rules
    if val in ['new', 'edit', 'search']:
        raise Invalid(_('That name cannot be used'))

    if len(val) < 4:
        raise Invalid(_('Name must be at least %s characters long') % 4)
    if len(val) > PACKAGE_NAME_MAX_LENGTH:
        raise Invalid(_('Name must be a maximum of %i characters long') % \
                      PACKAGE_NAME_MAX_LENGTH)
    if not name_match.match(val):
        raise Invalid(_('Url must be purely lowercase alphanumeric '
                        '(ascii) characters and these symbols: -_'))
    return val