ckanext-wotkit
==============

Extensions to the CKAN open data portal for WoTKit integration 


Installation
============

To install this package, from your CKAN virtualenv, run the following from your CKAN base folder (e.g. ``pyenv/``)::

``pip install -e git+https://github.com/SenseTecnic/ckanext-wotkit#egg=ckanext-wotkit``

Then activate it by setting ``ckan.plugins = wotkit`` in your main ``ini``-file.


Deploy to test server
============

Mainly follows this guide on setting up git hooks: http://danbarber.me/using-git-for-deployment/

The test server guiness.magic.ubc.ca is set up with 2 git repositories. There is a git --bare repository at /opt/ckanext-wotkit.git, and the git repository that contains the source code at /opt/pyenv/src/ckanext-wotkit. The source code repository only has one remote which is the bare repository. The bare repository is configured with a post-update hook, which will do whatever is needed upon an update of the source code. Both repositories are owned by the user git who has write permissions.

From your local development git repository, add the remote called guiness that links to the bare repository on the test server:

``git remote add guiness git@guiness.magic.ubc.ca:/opt/ckanext-wotkit.git``

Then, whenever we want to push to the test server, we can do 

``git push guiness master`` 
