# model.py - Peewee database model

from peewee import *
from playhouse.migrate import migrate
from config import database, migrator
import datetime

database.connect()

def atomic():
    ''' To run a bunch of stuff within a transaction; e.g.:

    with model.atomic() as xact:
        foo
        bar
        baz
        if error:
            xact.rollback()

    '''
    return database.atomic()

class BaseModel(Model):
    class Meta:
        database = database

    @staticmethod
    def update_schema(check_update,from_version):
        ''' Implement this to migrate a database from an older version, and return the current version of this table.

        Only process updates if check_update is true. Example:

            if check_update and from_version < 1:
                migrator.migrate(
                    migrator.add_column('BlahTable', 'foo', BlahTable.foo),
                    migrator.add_column('BlahTable', 'bar', BlahTable.baz), # changed from 'bar' to 'baz' in verison 2
                )
            if check_update and from_version < 2:
                migrator.migrate(
                    migrator.rename_column('BlahTable', 'bar', 'baz'),
                )
            return 2
        '''
        return 0

''' Site-level stuff '''

class Global(BaseModel):
    ''' Settings for the site itself (schema version, generic global config, etc.) '''
    key = CharField(unique=True)
    int_value = IntegerField(null=True)
    string_value = CharField(null=True)

    @staticmethod
    def update_schema(check_update,from_version):
        ''' Hook for migrating schemata, e.g. table names '''
        return 0

''' Some sample tables to get you started '''

class User(BaseModel):
    ''' A user in the system '''
    username = CharField(unique=True)
    pwhash = CharField() # We're going to use bcrypt. Right? Right.
    email = CharField()
    is_admin = BooleanField(default=False)
    reset_key = CharField(null=True)

class Session(BaseModel):
    session_id = CharField(unique=True)
    user = ForeignKeyField(User, related_name='sessions', null=True)
    last_ip = CharField()
    last_seen = DateTimeField()

class AdminLog(BaseModel):
    ''' Administrative action log '''
    timestamp = DateTimeField(default=datetime.datetime.now)
    user = ForeignKeyField(User, related_name='actions')
    ip = CharField()
    url = CharField()
    description = TextField()
    session_id = CharField()
    class Meta:
        indexes = (
            (('user', 'timestamp'), False),
        )

''' Table management '''

all_types = [
    Global, #MUST come first
    User,
    Session,
    AdminLog,
]

def create_tables():
    with database.atomic():
        database.create_tables(all_types, safe=True)
        for table in all_types:
            schemaVersion, created = Global.get_or_create(key='schemaVersion.' + table.__name__)
            schemaVersion.int_value = table.update_schema(not created, schemaVersion.int_value)
            schemaVersion.save()

def drop_all_tables(i_am_really_sure=False):
    ''' Call this if you need to nuke everything and restart. Only for development purposes, hopefully. '''
    if not i_am_really_sure:
        raise "You are not really sure. Call with i_am_really_sure=True to proceed."
    with database.atomic():
        for table in all_types:
            database.drop_table(table)
