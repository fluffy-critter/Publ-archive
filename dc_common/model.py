# model.py - Peewee database model

from peewee import *
from playhouse.migrate import migrate
from config import database, migrator
from enum import Enum
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

class Asset(BaseModel):
    user = ForeignKeyField(User, related_name='assets')
    content_file = CharField(unique=True)
    content_type = CharField()
    content_hash = CharField(index=True) # SHA-1
    width = IntegerField(null=True)
    height = IntegerField(null=True)

class Theme(BaseModel):
    owner = ForeignKeyField(User, related_name='themes')
    name = CharField()
    css_path = CharField()

class Section(BaseModel):
    owner = ForeignKeyField(User, related_name='series')
    key = CharField(unique=True)
    name = CharField()
    description = TextField()
    parent = ForeignKeyField('self', related_name='children', null=True)
    theme = ForeignKeyField(Theme, null=True)
    splash_image = ForeignKeyField(Asset)

class ContentClass(BaseModel):
    type_name = CharField(unique=True)
    display_name = CharField()
    description = TextField(null=True)

class PublishStatus(Enum):
    draft = 0       # Not yet published
    published = 1   # Visible
    pending = 2     # Will be published when now > pubdate
    queued = 3      # Will be published when the queue gets to it
    static_page = 4 # Statically attached to the section rather than in the archive flow

    @staticmethod
    class Field(IntegerField):
        def db_value(self,ee):
            return ee.value
        def python_value(self,value):
            return PublishStatus(v)

class Page(BaseModel):
    page_id = CharField(unique=True)
    user = ForeignKeyField(User, related_name='pages')
    section = ForeignKeyField(Section, related_name='pages', null=True)
    content_class = ForeignKeyField(ContentClass, related_name='pages')
    title = CharField()
    description = TextField(null=True)
    crate_date = DateField(default=datetime.datetime.utcnow())
    publish_date = DateField(default=datetime.datetime.utcnow(),index=True)
    publish_status = PublishStatus.Field(default=PublishStatus.draft)
    is_visible = BooleanField(default=False)
    notes = TextField(null=True)
    theme = ForeignKeyField(Theme, null=True)
    class Meta:
        indexes = (
            (('user', 'publish_status', 'section', 'publish_date'), False),
        )

    @property
    def archive_order(self):
        return (self.publish_date,self.key)

    @staticmethod
    def visible_pages(section=None):
        q = Page.select().where(Page.publish_status == PublishStatus.published)
        if section:
            q = q.where(Page.section == section)
        return q

    @property
    def next_page(self):
        q = Page.visible_pages(Page.section).where(Page.publish_date >= self.publish_date)

        q = q.order_by(Page.publish_date, Page.key)
        for r in q:
            if (r.archive_order > self.archive_order):
                return r
        return None

    @property
    def previous_page(self):
        q = Page.visible_pages(Page.section).where(Page.publish_date <= self.publish_date)

        q = q.order_by(-Page.publish_date, -Page.key)
        for r in q:
            if (r.archive_order < self.archive_order):
                return r
        return None

class PageContent(BaseModel):
    ''' A content chunk within a page '''
    page = ForeignKeyField(Page, related_name='chunks')
    display_order = IntegerField(default=0)
    content_class = ForeignKeyField(ContentClass, null=True)

    asset = ForeignKeyField(Asset, related_name='chunks', null=True)
    asset_title = TextField(null=True)
    asset_link = TextField(null=True)
    text = TextField(null=True)

    '''
    Custom HTML for this content chunk, to override the default.
    Default is something like:

        <div class="{content_type}">
            <a href="{asset_link}"><img src="{asset_src}" srcset="{asset_srcset}" title="{asset_text}"></a>
            {{text|markdown}}
        </div>
    '''
    custom_html = TextField(null=True)
    class Meta:
        indexes = (
            (('page', 'display_order'), False),
        )

class Tag(BaseModel):
    name = CharField(unique=True)

class TaggedPage(BaseModel):
    tag = ForeignKeyField(Tag, 'pages')
    page = ForeignKeyField(Page, 'tags')

class PageBookmark(BaseModel):
    ''' A 'bookmark' within a section, e.g. chapter indices '''
    section = ForeignKeyField(Section, related_name='bookmarks')
    page = ForeignKeyField(Page)
    name = CharField()

    @staticmethod
    def before(page):
        ''' Get the last bookmark on or before this page '''
        q = PageBookmark.select().join(Page).where(
            (PageBookmark.section == section)
            & (Page.publish_date <= page.publish_date)
            ).order_by(-Page.publish_date)
        for r in q:
            if r.page.archive_order <= page.archive_order:
                return r
        return None

    @staticmethod
    def after(page):
        ''' Get the next bookmark after this page '''
        q = PageBookmark.select().join(Page).where(
            (PageBookmark.section == section)
            & (Page.publish_date <= page.publish_date)
            ).order_by(Page.publish_date)
        for r in q:
            if r.page.archive_order > page.archive_order:
                return r
        return None

    @property
    def previous(self):
        ''' Get the previous bookmark '''
        q = PageBookmark.select().join(Page).where(
            (PageBookmark.section == self.section)
            & (Page.publish_date <= self.page.publish_date)
            ).order_by(-Page.publish_date)
        for r in q:
            if r.page.archive_order < self.page.archive_order:
                return r
        return None

    @property
    def next(self):
        ''' Get the next bookmark '''
        q = PageBookmark.select().join(Page).where(
            (PageBookmark.section == self.section)
            & (Page.publish_date <= self.page.publish_date)
            ).order_by(Page.publish_date)
        for r in q:
            if r.page.archive_order > self.page.archive_order:
                return r
        return None

''' Table management '''

all_types = [
    Global, #MUST come first

    User,
    PasswordIdentity,
    AdminLog,

    Asset,
    Section,
    ContentClass,

    Page,
    PageContent,
    Tag,
    TaggedPage,
    PageBookmark,
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
