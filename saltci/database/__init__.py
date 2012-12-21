# -*- coding: utf-8 -*-
'''
    saltci.database
    ~~~~~~~~~~~~~~~

    Salt-CI Database

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

import logging
import migrate
from os import path
from migrate.versioning.api import upgrade
from migrate.versioning.repository import Repository
from sqlalchemy import orm
from flask.ext.sqlalchemy import SQLAlchemy as SQLAlchemyBase
from saltci.exceptions import SaltCIStartupException


log = logging.getLogger(__name__)


class SQLAlchemy(SQLAlchemyBase):

    repository_id   = 'Salt-CI DB Schema'
    repository_path = path.join(path.dirname(__file__), 'upgrades')

    def init_app(self, app):
        log.debug("Initializing Flask-SQLAlchemy")
        if app.config.get('SQLALCHEMY_DATABASE_URI', None) is None:
            raise SaltCIStartupException(
                'Please configure the database settings in the configuration file'
            )

        super(SQLAlchemy, self).init_app(app)
        self.app = app

    def update_dbentry_from_form(self, dbentry, form):
        for name in form._fields.keys():
            column_value = getattr(dbentry, name, None)
            form_value = form._fields[name].data
            if isinstance(column_value, orm.collections.InstrumentedSet):
                form_value = orm.collections.InstrumentedSet(form_value)
#            if column_value and form_value != column_value:
#                setattr(dbentry, name, form._fields[name].data)
            if form_value != column_value:
                setattr(dbentry, name, form._fields[name].data)

    def upgrade_database_required(self):
        log.info("Checking if a database upgrade is required")
        from .models import SchemaVersion
        if not self.engine.has_table(SchemaVersion.__tablename__):
            raise SaltCIStartupException(
                'Please run `salt-ci-migrate upgrade` to upgrade the database'
            )

            log.info("Creating schema version control table")
            try:
                SchemaVersion.__table__.create(self.engine)
            except Exception, err:
                log.exception(err)
                raise RuntimeError(err)

        log.info("Checking for required database upgrade")
        repository = Repository(self.repository_path)
        if not self.session.query(SchemaVersion).get(self.repository_id):
            raise SaltCIStartupException(
                'Please run `salt-ci-migrate upgrade` to upgrade the database'
            )

            log.info("Adding our upgrades repository to the schemas table")
            self.session.add(SchemaVersion(
                self.repository_id,
                path.abspath(path.expanduser(repository.path)), 0)
            )
            self.session.commit()
            self.session.flush()

        schema_version = self.session.query(SchemaVersion).get(self.repository_id)
        if schema_version.version < repository.latest:
            raise SaltCIStartupException(
                'Please run `salt-ci-migrate upgrade` to upgrade the database'
            )

            log.warn("Upgrading database (from -> to...)")
            try:
                upgrade(self.engine, repository)
            except Exception, err:
                log.exception(err)
            log.warn("Database Upgrade complete")
        else:
            log.debug("No database upgrades required")
        log.debug("Upgrades complete.")

db = SQLAlchemy()
