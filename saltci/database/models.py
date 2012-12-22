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


class AccountQuery(db.Query):

    def from_github_token(self, token):
        return self.filter(Account.gh_token == token).first()


class Account(db.Model):
    __tablename__   = 'accounts'

    gh_id           = db.Column('github_id', db.Integer, primary_key=True)
    gh_login        = db.Column('github_login', db.String(100))
    gh_token        = db.Column('github_access_token', db.String(100), index=True)
    gravatar_id     = db.Column(db.String(32))
    hooks_token     = db.Column(db.String(32), index=True, default=lambda: uuid4().hex)

    query_class     = AccountQuery

    def __init__(self, github_id, github_login, github_token, gravatar_id):
        self.gh_id = github_id
        self.gh_login = github_login
        self.gh_token = github_token
        self.gravatar_id = gravatar_id
