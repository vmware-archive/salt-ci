# -*- coding: utf-8 -*-
'''
    saltci.database.upgrades.versions.001_Initial_Schema
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Initial database layout.

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''
import logging
from datetime import datetime
from saltci.database import db, orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import create_session
from migrate import *

# No need to change logger name bellow, unless you're after something specific
log = logging.getLogger('saltci.database.upgrades.{0}'.format(__name__.split('_', 1).pop(0)))

# Local declarative base
Model = declarative_base(name='Model')
metadata = Model.metadata


class SchemaVersion(Model):
    '''SQLAlchemy-Migrate schema version control table.'''

    __tablename__   = 'migrate_version'

    repository_id   = db.Column(db.String(250), primary_key=True)
    repository_path = db.Column(db.Text)
    version         = db.Column(db.Integer)

    def __init__(self, repository_id, repository_path, version):
        self.repository_id = repository_id
        self.repository_path = repository_path
        self.version = version


class Account(Model):
    __tablename__   = 'accounts'

    gh_id           = db.Column('github_id', db.Integer, primary_key=True)
    gh_login        = db.Column('github_login', db.String(100))
    gh_token        = db.Column('github_access_token', db.String(100), index=True)
    gravatar_id     = db.Column(db.String(32))
    hooks_token     = db.Column(db.String(32), index=True, default=lambda: uuid4().hex)
    last_login      = db.Column(db.DateTime, default=datetime.utcnow)
    register_date   = orm.deferred(db.Column(db.DateTime, default=datetime.utcnow))
    locale          = db.Column(db.String(10), default=lambda: 'en')
    timezone        = db.Column(db.String(25), default=lambda: 'UTC')


class Privilege(Model):
    __tablename__   = 'privileges'

    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(50), unique=True)

    def __init__(self, privilege_name):
        if not isinstance(privilege_name, basestring):
            try:
                privilege_name = privilege_name.name
            except AttributeError:
                # It's a Need
                try:
                    privilege_name = privilege_name.need
                except AttributeError:
                    raise
        self.name = privilege_name

    def __repr__(self):
        return '<{0} {1!r}>'.format(self.__class__.__name__, self.name)


account_privileges = db.Table(
    'account_privileges', metadata,
    db.Column('account_github_id', db.Integer, db.ForeignKey('accounts.github_id')),
    db.Column('privilege_id', db.Integer, db.ForeignKey('privileges.id'))
)


class Group(Model):
    __tablename__ = 'groups'

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(30))

    accounts      = db.dynamic_loader("Account", secondary="group_accounts",
                                      backref=db.backref("groups",
                                                         lazy=True,
                                                         collection_class=set))
    privileges    = db.relation("Privilege", secondary="group_privileges",
                                backref='privileged_groups', lazy=True, collection_class=set,
                                cascade='all, delete')

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return u'<{0} {1!r}:{2!r}>'.format(self.__class__.__name__, self.id, self.name)


group_accounts = db.Table(
    'group_accounts', metadata,
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id')),
    db.Column('account_github_id', db.Integer, db.ForeignKey('accounts.github_id'))
)


group_privileges = db.Table(
    'group_privileges', metadata,
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id')),
    db.Column('privilege_id', db.Integer, db.ForeignKey('privileges.id'))
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata

    # Bind the metadata to the migrate engine
    metadata.bind = migrate_engine

    # Let's get a session
    session = create_session(migrate_engine, autoflush=True, autocommit=False)

    # Let's create our tables
    if not migrate_engine.has_table(Account.__tablename__):
        log.info('Creating accounts table')
        Account.__table__.create(migrate_engine)

    if not migrate_engine.has_table(Privilege.__tablename__):
        log.info('Creating Privilege table')
        Privilege.__table__.create(migrate_engine)

    if not migrate_engine.has_table(account_privileges.name):
        log.info('Creating account_privileges table')
        account_privileges.create(migrate_engine)

    if not migrate_engine.has_table(Group.__tablename__):
        log.info('Creating Group table')
        Group.__table__.create(migrate_engine)

    if not migrate_engine.has_table(group_accounts.name):
        log.info("Creating group_accounts table")
        group_accounts.create(migrate_engine)

    if not migrate_engine.has_table(group_privileges.name):
        log.info("Creating group_privileges table")
        group_privileges.create(migrate_engine)

    admins = Group('Administrators')
    admins.privileges.add(Privilege('administrator'))
    session.add(admins)

    managers = Group('Managers')
    managers.privileges.add(Privilege('manager'))
    session.add(managers)


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.

    # Bind the metadata to the migrate engine
    metadata.bind = migrate_engine

    if migrate_engine.has_table(Accounts.__tablename__):
        log.info('Removing the accounts table')
        Account.__table__.drop(migrate_engine)
