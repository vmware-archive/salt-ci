import logging
from datetime import datetime
from saltci.database import db
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import create_session
from migrate import *

# No need to change logger name bellow, unless you're after something specific
log = logging.getLogger('saltci.database.upgrades.{0}'.format(__name__.split('_', 1).pop(0)))

# Local declarative base
Model = declarative_base(name='Model')
metadata = Model.metadata


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

    #accounts      = db.dynamic_loader("Account", secondary="group_accounts",
    #                                  backref=db.backref("groups",
    #                                                     lazy=True,
    #                                                     collection_class=set))
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

    # If this migration is being executed on a clean database, the changes done by this script
    # won't be needed. This is until we actually release the application on the WWW and is to be
    # able to maintain and migrate developments versions.
    session = create_session(migrate_engine, autoflush=True, autocommit=False)

    table = db.Table('accounts', metadata, autoload=True)

    if 'last_login' not in table.columns:
        log.info('Adding the \'last_login\' column to the accounts table')
        column = db.Column('last_login', db.DateTime, default=datetime.utcnow)
        column.create(table)
        session.commit()
        for entry in session.query(table):
            if not entry.last_login:
                log.info(
                    'Setting last_login to the current date for user id {0}'.format(
                        entry.gh_login
                    )
                )
                entry.last_login = datetime.utcnow()
        session.commit()

    if 'register_date' not in table.columns:
        log.info('Adding the \'register_date\' column to the accounts table')
        column = db.Column('register_date', db.DateTime, default=datetime.utcnow)
        column.create(table)
        session.commit()
        for entry in session.query(table):
            if not entry.register_date:
                log.info(
                    'Setting register_date to the current date for user id {0}'.format(
                        entry.gh_login
                    )
                )
                entry.register_date = datetime.utcnow()
        session.commit()

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
