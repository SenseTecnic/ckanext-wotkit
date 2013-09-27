import ckan.plugins as p
from ckan.common import OrderedDict, _, json, request, c, g, response

import pprint

# This is the main auth function that will check if the dataset is invisible to the current user
def _package_invisible_check_auth(context, pkg_dict):
	if not 'id' in pkg_dict:
		pkg_dict['id'] = pkg_dict.get('resource_id')
	
	user = c.userobj

	if 'pkg_invisible' not in pkg_dict or pkg_dict['pkg_invisible'] == 'False':
		return {'success' : True}
	elif user is None:
		return {
				'success': False,
				'msg': p.toolkit._('User not authorized to view or update package')
			}
	else:
		if 'pkg_creator' not in pkg_dict:
			return {
				'success': False,
				'msg': p.toolkit._('User {0} not authorized to view or update package {1}'
						.format(str(user), pkg_dict['id']))
			}
		else:
			if pkg_dict['pkg_creator'] == user.id:
				return {'success' : True}
			else:
				return {
					'success': False,
					'msg': p.toolkit._('User {0} not authorized to view or update package {1}'
							.format(str(user), pkg_dict['id']))
				}

def invisible_package_search(context, pkg_dict):
	return _package_invisible_check_auth(context, pkg_dict)

def invisible_package_show(context, pkg_dict):
	return _package_invisible_check_auth(context, pkg_dict)

def require_creator_to_update(context, pkg_dict):
	user = c.userobj
	
	# If user is not logged in, return false
	if user is None:
		return {'success': False}
	
	# If creator field is not set (legacy data), return true
	if 'pkg_creator' not in c.pkg_dict:
		return {'success' : True}

	# If current user is the creator, return true
	if user.id != c.pkg_dict['pkg_creator']:
		return {'success': False}
	else:
		return {'success' : True}
