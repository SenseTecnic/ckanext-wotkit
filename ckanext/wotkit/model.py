import datetime
import re
import os
from hashlib import sha1, md5

from sqlalchemy.sql.expression import or_
from sqlalchemy.orm import synonym
from sqlalchemy import types, Column, Table, ForeignKey

import ckan.model.meta as meta
import ckan.model.types as _types
import ckan.model.domain_object as domain_object

import pprint

# DB schema for wotkit_user, will be automatically created upon initialization by SQLAlchemy
wotkit_user_table = Table('wotkit_user', meta.metadata,
        Column('id', types.UnicodeText, primary_key=True, 
                default=_types.make_uuid),
        Column('ckan_id', types.UnicodeText, ForeignKey("user.id") ),
        Column('wotkit_id', types.UnicodeText),
        Column('wotkit_password', types.UnicodeText),
        )

class WotkitUser(domain_object.DomainObject):
    """ORM Model for storing Wotkit credentials linked with ckan. 
    """        
        
    @classmethod
    def get(cls, ckan_id):
        '''Get wotkit user credentials using the user ID stored by ckan'''

        obj = meta.Session.query(cls).autoflush(False)
        return obj.filter_by(ckan_id=ckan_id).first()
    
    @classmethod
    def initDB(cls):
        """Create wotkit_user table in database. Must be called after ckan initializes its model"""
        meta.metadata.create_all()

# SQLAlchemy ORM map to WotkitUser
meta.mapper(WotkitUser, wotkit_user_table,
    order_by=wotkit_user_table.c.id)
