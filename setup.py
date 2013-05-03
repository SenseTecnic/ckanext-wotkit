from setuptools import setup, find_packages
import sys, os

version = '0.0'

setup(
	name='ckanext-wotkit',
	version=version,
	description="proxy to wotkit",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='Mark Duppenthaler',
	author_email='mduppes@gmail.com',
	url='',
	license='',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.wotkit'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		# -*- Extra requirements: -*-
	],
	entry_points=\
	"""
        [ckan.plugins]
	# Add plugins here, eg
	wotkit=ckanext.wotkit.plugin:WotkitPlugin
	""",
)
