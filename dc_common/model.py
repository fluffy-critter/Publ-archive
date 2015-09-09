# model.py - Peewee database model

from peewee import *
from playhouse.migrate import migrate
from config import database, migrator
from enum import Enum

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

class User(BaseModel):
    display_name = CharField(unique=True)
    is_admin = BooleanField(default=False)

class PasswordIdentity(BaseModel):
    ''' Standard signin identity: username/password (TODO: OAuth, OpenID) '''
    user = ForeignKeyField(User, 'password')
    username = CharField(unique=True)
    pwhash = CharField() # We're going to use bcrypt. Right? Right.
    email = CharField(unique=True)
    reset_key = CharField(null=True)

class AdminLog(BaseModel):
    ''' Administrative action log '''
    timestamp = DateTimeField()
    user = ForeignKeyField(User, related_name='actions')
    ip = CharField()
    request_path = CharField()
    description = TextField()
    session_id = CharField()
    class Meta:
        indexes = (
            (('user', 'timestamp'), False),
        )

class UserLinks(BaseModel):
    user = ForeignKeyField(User, related_name='links')
    title = CharField()
    url = CharField()
    description = CharField(null=True)

class Section(BaseModel):
    owner = ForeignKeyField(User, related_name='series')
    key = CharField(unique=True)
    title = CharField()
    description = TextField()
    parent = ForeignKeyField(Section, related_name='children', null=True)
    continue_within_parent = BooleanField()

class PageType(Enum):
    serial = 0
    static = 1
    @staticmethod
    class Field(IntegerField):
        def db_value(self,value):
            return value.value
        def python_value(self,value):
            return PageType(value)

class ContentType(BaseModel):
    type_name = CharField(unique=True)
    display_name = CharField()
    description = TextField(null=True)

class Page(BaseModel):
    page_id = CharField(unique=True)
    section = ForeignKeyField(Section, related_name='pages', null=True)
    page_type = PageType.Field()
    content_type = ForeignKeyField(ContentType, related_name='pages')
    title = CharField()
    description = TextField(null=True)
    publish_date = DateField(index=True)
    is_visible = BooleanField(default=False)
    notes = TextField(null=True)
    theme = ForeignKeyField(Theme, null=True)
    class Meta:
        indexes = (
            (('page_type', 'series', 'chapter', 'publish_date'), False),
        )

    @property
    def archive_order(self):
        return (self.publish_date,self.key)

    @staticmethod
    def visible_pages(now,section=None):
        q = Page.select().where((Page.is_visible == True) & (Page.publish_date < now))
        if section:
            w = (Page.section == section)
            while section.continue_within_parent:
                w = w | (Page.section == section.parent)
                section = section.parent
            q = q.where(w)
        return q

    @property
    def next_page(self,now,same_section=False):
        q = Page.visible_pages(
            now,
            same_section and Page.section
            ).where(Page.publish_date >= self.publish_date)

        q = q.order_by(Page.publish_date, Page.key)
        for r in q:
            if (r.archive_order > self.archive_order):
                return r
        return None

    @property
    def previous_page(self,now,same_section=False):
        q = Page.visible_pages(
            now,
            same_series and Page.series,
            same_chapter and Page.chapter
            ).where(Page.publish_date <= self.publish_date)

        q = q.order_by(-Page.publish_date, -Page.key)
        for r in q:
            if (r.archive_order < self.archive_order):
                return r
        return None

class Asset(BaseModel):
    user = ForeignKeyField(User, related_name='assets')
    content_file = CharField()
    content_type = CharField()
    width = IntegerField()
    height = IntegerField()

class PageContent(BaseModel):
    ''' A content chunk within a page '''
    page = ForeignKeyField(Page, related_name='assets')
    display_order = IntegerField(default=0)
    content_type = CharField(null=True)
    asset = ForeignKeyField(Asset, related_name='pages', null=True)
    asset_text = TextField(null=True)
    asset_link = TextField(null=True)
    # Custom HTML for this content chunk, to override the default.
    # Default is something like:
    #  <div class="{content_type}"><a href="{asset_link}"><img src="{asset_src}" srcset="{asset_srcset}" title="{asset_text}"></a></div>
    custom_html = TextField(null=True)
    class Meta:
        indexes = (
            (('page', 'display_order'), False),
        )

class Transcript(BaseModel):
    page = ForeignKeyField(Page, related_name='transcripts')
    text = TextField()
    accepted = BooleanField(default=False)

class Tag(BaseModel):
    name = CharField(unique=True)

class TaggedPage(BaseModel):
    tag = ForeignKeyField(Tag, 'pages')
    page = ForeignKeyField(Page, 'tags')

''' Table management '''

all_types = [
    Global, #MUST come first
    User,
    AdminLog,

    UserLinks,

    RenderSpec,
    RenderQuality,
    Theme,

    Series,
    Story,
    Chapter,
    Page,

    Asset,
    RenderedAsset,
    PageContent,
    Transcript,
    NewsPost,
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
