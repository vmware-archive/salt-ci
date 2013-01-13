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

    id              = db.Column('github_id', db.Integer, primary_key=True)
    login           = db.Column('github_login', db.String(100))
    name            = db.Column('github_name', db.String(100))
    email           = db.Column('github_email', db.String(254))
    token           = db.Column('github_access_token', db.String(100), index=True)
    avatar_url      = db.Column(db.String(2000))
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


class Organization(Model):
    __tablename__ = 'organizations'

    id            = db.Column('github_id', db.Integer, primary_key=True)
    name          = db.Column('github_name', db.String)
    login         = db.Column('github_login', db.String, index=True)
    avatar_url    = db.Column(db.String(2000))

    # Relationships
    accounts      = db.relation("Account", secondary="account_organizations",
                                backref='organizations', lazy=True, collection_class=set,
                                cascade='all, delete')

    repositories  = db.relation("Repository", secondary="organization_repositories",
                                backref='organization', lazy=True, cascade='all, delete')


account_organizations = db.Table(
    'account_organizations', metadata,
    db.Column('account_id', db.Integer, db.ForeignKey('accounts.github_id')),
    db.Column('organization_id', db.Integer, db.ForeignKey('organizations.github_id'))
)


class Repository(Model):
    __tablename__ = 'repositories'

    id            = db.Column('github_id', db.Integer, primary_key=True)
    name          = db.Column('github_name', db.String, index=True)
    full_name     = db.Column('github_full_name', db.String)
    url           = db.Column('github_url', db.String)
    description   = db.Column('github_description', db.String)
    fork          = db.Column('github_fork', db.Boolean, default=False)
    private       = db.Column('github_private', db.Boolean, default=False)
    push_active   = db.Column(db.Boolean, default=True)
    pull_active   = db.Column(db.Boolean, default=True)


account_repositories = db.Table(
    'account_repositories', metadata,
    db.Column('account_id', db.Integer, db.ForeignKey('accounts.github_id')),
    db.Column('repository_id', db.Integer, db.ForeignKey('repositories.github_id'))
)


organization_repositories =  db.Table(
    'organization_repositories', metadata,
    db.Column('organization_id', db.Integer, db.ForeignKey('organizations.github_id')),
    db.Column('repository_id', db.Integer, db.ForeignKey('repositories.github_id'))
)


repository_administrators =  db.Table(
    'repository_administrators', metadata,
    db.Column('repository_id', db.Integer, db.ForeignKey('repositories.github_id')),
    db.Column('account_id', db.Integer, db.ForeignKey('accounts.github_id'))
)


class Commit(Model):
    __tablename__   = 'commits'
    sha             = db.Column(db.String(40), primary_key=True)
    ref             = db.Column(db.String)
    message         = db.Column(db.String)
    url             = db.Column(db.String(2000))
    compare_url     = db.Column(db.String(2000))
    commited_at     = db.Column(db.UTCDatetime)
    committer_name  = db.Column(db.String)
    committer_email = db.Column(db.String(254))
    author_name     = db.Column(db.String)
    author_email    = db.Column(db.String(254))
    repository_id   = db.Column(db.Integer, db.ForeignKey('repositories.github_id'))


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

    if not migrate_engine.has_table(Organization.__tablename__):
        log.info('Creating organizations table')
        Organization.__table__.create(migrate_engine)

    if not migrate_engine.has_table(account_organizations.name):
        log.info('Creating account_organizations table')
        account_organizations.create(migrate_engine)

    if not migrate_engine.has_table(Repository.__tablename__):
        log.info('Creating repositories table')
        Repository.__table__.create(migrate_engine)

    if not migrate_engine.has_table(account_repositories.name):
        log.info('Creating account_repositories table')
        account_repositories.create(migrate_engine)

    if not migrate_engine.has_table(organization_repositories.name):
        log.info('Creating organization_repositories table')
        organization_repositories.create(migrate_engine)

    if not migrate_engine.has_table(repository_administrators.name):
        log.info('Creating repository_administrators table')
        repository_administrators.create(migrate_engine)

    if not migrate_engine.has_table(Commit.__tablename__):
        log.info('Creating commits table')
        Commit.__table__.create(migrate_engine)

    log.info('Adding the Administrators group')
    admins = Group('Administrators')
    admins.privileges.add(Privilege('administrator'))
    session.add(admins)
    session.commit()

    SALTSTACK_CORE_TEAM = (
        (   4603,  u'SEJeff'     ),
        (  89334,  u'herlo'      ),
        (  91293,  u'whiteinge'  ),
        ( 287147,  u'techhat'    ),
        ( 300048,  u's0undt3ch'  ),
        ( 306240,  u'UtahDave'   ),
        ( 328598,  u'archtaku'   ),
        ( 507599,  u'thatch45'   ),
        ( 733988,  u'akoumjian'  ),
        (1074925,  u'seanchannel'),
    )
    log.info('Adding SaltStack Core Team to the Administrators group')
    for ctid, login in SALTSTACK_CORE_TEAM:
        log.info('  * Adding {0}'.format(login))
        migrate_engine.execute(
            group_accounts.insert().values(
                group_id=admins.id, account_github_id=ctid
            )
        )

    log.info('Adding the Managers group')
    managers = Group('Managers')
    managers.privileges.add(Privilege('manager'))
    session.add(managers)
    session.commit()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.

    # Bind the metadata to the migrate engine
    metadata.bind = migrate_engine

    if migrate_engine.has_table(Accounts.__tablename__):
        log.info('Removing the accounts table')
        Account.__table__.drop(migrate_engine)
