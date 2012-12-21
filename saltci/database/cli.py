# -*- coding: utf-8 -*-
'''
    saltci.database.cli
    ~~~~~~~~~~~~~~~~~~~

    Shell front-end to the Salt-CI database migrations

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

import os
import sys
import logging
from flask import Flask
from migrate.versioning.shell import main
from migrate.versioning.api import downgrade, script, upgrade
from migrate.versioning.repository import Repository


from saltci.database import db, models
from saltci.exceptions import SaltCIStartupException
from saltci.utils.parsers import SaltCIMigrateParser


log = logging.getLogger(__name__)


class SaltCIMigrate(SaltCIMigrateParser):

    __repository_id = 'Salt-CI DB Schema'
    __repository_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'upgrades'))
    __repository_script_templates = os.path.join(__repository_path, 'templates')

    def run(self):
        self.parse_args()
        self.setup_logfile_logger()

        try:
            self._run()
        except SaltCIStartupException, err:
            self.error(err)
        except KeyboardInterrupt(self):
            self.exit(0)

    def _run(self):
        # Create a fake flask app so that all the database related setup is done for us
        app = Flask(__name__)
        app.config.update(self.config)
        db.init_app(app)

        # Run the appropriate command
        getattr(self, 'run_{0}'.format(self.migrate_command))()

    def run_upgrade(self):
        log.info("Checking if a database upgrade is required")
        if not db.engine.has_table(models.SchemaVersion.__tablename__):
            log.info("Creating schema version control table")
            try:
                models.SchemaVersion.__table__.create(db.engine)
            except Exception, err:
                log.exception(err)
                raise RuntimeError(err)

        log.info("Checking for required database upgrade")
        repository = Repository(self.__repository_path)
        if not db.session.query(models.SchemaVersion).get(self.__repository_id):
            log.info("Adding our upgrades repository to the schemas table")
            db.session.add(models.SchemaVersion(
                self.__repository_id,
                os.path.abspath(os.path.expanduser(repository.path)), 0)
            )
            db.session.commit()
            db.session.flush()

        desired_version = self.migrate_args or repository.latest
        schema_version = db.session.query(models.SchemaVersion).get(self.__repository_id)
        if schema_version.version < desired_version:
            log.warn("Upgrading database (from -> to...)")
            try:
                upgrade(db.engine, repository, version=desired_version)
            except Exception, err:
                log.exception(err)
            log.warn("Database Upgrade complete")
        else:
            log.debug("No database upgrades required")
        log.debug("Upgrades complete.")

    def run_downgrade(self):
        if not db.engine.has_table(models.SchemaVersion.__tablename__):
            log.warning('Database is not under migrations support.')
            return
        if not db.session.query(models.SchemaVersion).get(self.__repository_id):
            log.warning('Migrations repository not managed. Not downgrading.')
            return

        repository = Repository(self.__repository_path)
        desired_version = self.migrate_args or (repository.latest - 1)
        schema_version = db.session.query(models.SchemaVersion).get(self.__repository_id)
        if schema_version.version > desired_version:
            log.warn("Downgrading database (from -> to...)")
            try:
                downgrade(db.engine, repository, version=desired_version)
            except Exception, err:
                log.exception(err)
            log.warn("Database Downgrade Complete")
        else:
            log.debug("No database downgrade required")
        log.debug("Downgrade complete.")

    def run_script(self):
        repository = Repository(self.__repository_path)
        script(
            self.migrate_args, repository.path,
            templates_path=self.__repository_script_templates
        )
