###################################################
#
#	Additional validators used by the plugin
#
###################################################

import ckan.lib.navl.dictization_functions as df
from ckan.common import OrderedDict, _, json, request, c, g, response

Invalid = df.Invalid
StopOnError = df.StopOnError
Missing = df.Missing
missing = df.missing

def validate_creator_field(key, data, errors, context):
    #Sanitize special keys reserved to specify creator
    if data[key] == 'pkg_creator':
    	# Set the value field of the pkg_creator extras data to the current user id
    	data[('extras', key[1], 'value')] = c.userobj.id
   	pass

def validate_invisible_field(key, data, errors, context):
    if data[key] == 'pkg_invisible':
    	if data[('extras', key[1], 'value')] != ( True or False ):
    		data[('extras', key[1], 'value')] = False
    pass