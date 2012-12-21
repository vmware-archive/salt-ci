# -*- coding: utf-8 -*-
"""
    saltci.database.models
    ~~~~~~~~~~~~~~~~~~~~~~

    Salt-CI database models

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
"""


from uuid import uuid4
from saltci.database import db


class SchemaVersion(db.Model):
    """SQLAlchemy-Migrate schema version control table."""

    __tablename__   = 'migrate_version'

    repository_id   = db.Column(db.String(250), primary_key=True)
    repository_path = db.Column(db.Text)
    version         = db.Column(db.Integer)

    def __init__(self, repository_id, repository_path, version):
        self.repository_id = repository_id
        self.repository_path = repository_path
        self.version = version


class Accounts(db.Model):
    __tablename__   = 'accounts'

    id              = db.Column(db.Integer, primary_key=True)
    username        = db.Column(db.String(100))
    github_token    = db.Column(db.String(100))
    hooks_token     = db.Column(db.String(32), index=True, default=lambda: uuid4().hex)
