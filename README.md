ckanext-wotkit
==============

Extensions to the CKAN open data portal for WoTKit integration 


Installation
============

To install this package, from your CKAN virtualenv, run the following from your CKAN base folder (e.g. ``pyenv/``)::

``pip install -e git+https://github.com/SenseTecnic/ckanext-wotkit#egg=ckanext-wotkit``

``pip install -r src/ckanext-wotkit/pip-requirements.txt``

Then activate it by setting ``ckan.plugins = wotkit`` in your main ``ini``-file.


Changelog
===========================
Release 1.2:
* Billing logs implemented. The log directory is configured in the .ini file.

Release 1.4:
* Added support for the option to set datasets to invisible. Only the dataset's creator may perform this change. Invisible datasets can only be viewed by the creator.
* Made editing datasets only available to the dataset's creator.
