import logging
from saltci.database import db
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import create_session
from migrate import *

# No need to change logger name bellow, unless you're after something specific
log = logging.getLogger('saltci.database.upgrades.{0}'.format(__name__.split('_', 1).pop(0)))

# Local declarative base
Model = declarative_base(name='Model')
metadata = Model.metadata


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

    if 'locale' in table.columns and 'timezone' in table.columns:
        log.info('No need to add locale and timezone to the accounts table')
        return

    log.info('Adding the \'locale\' column to the accounts table')
    locale = db.Column('locale', db.String(10), default=lambda: 'en')
    locale.create(table)
    session.commit()

    log.info('Adding the \'timezone\' column to the accounts table')
    timezone = db.Column('timezone', db.String(25), default=lambda: 'UTC')
    timezone.create(table)
    session.commit()

    for account in session.query(table):
        if not account.timezone:
            log.info(
                'Setting timezone to the default \'UTC\' for user id {0}'.format(
                    account.gh_login
                )
            )
            account.timezone = 'UTC'
        if not account.locale:
            log.info(
                'Setting locale to the default \'en\' for user id {0}'.format(
                    account.gh_login
                )
            )
            account.locale = 'en'
    session.commit()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.

    # Bind the metadata to the migrate engine
    metadata.bind = migrate_engine
