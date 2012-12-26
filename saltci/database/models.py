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
from datetime import datetime
from saltci.database import db, orm


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

    def from_hooks_token(self, token):
        return self.filter(Account.hooks_token == token).first()


class Account(db.Model):
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

    # Relations
    privileges      = db.relation('Privilege', secondary="account_privileges",
                                  backref='privileged_accounts', lazy=True, collection_class=set,
                                  cascade='all, delete')
    groups          = None  # Defined on Group

    query_class     = AccountQuery

    def __init__(self, github_id, github_login, github_token, gravatar_id):
        self.gh_id = github_id
        self.gh_login = github_login
        self.gh_token = github_token
        self.gravatar_id = gravatar_id

    def update_last_login(self):
        self.last_login = datetime.utcnow()


class PrivilegeQuery(orm.Query):
    def get(self, privilege):
        if not isinstance(privilege, basestring):
            try:
                privilege = privilege.name
            except AttributeError:
                # It's a Need
                try:
                    privilege = privilege.value
                except AttributeError:
                    raise
        return self.filter(Privilege.name == privilege).first()


class Privilege(db.Model):
    __tablename__   = 'privileges'

    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(50), unique=True)

    query_class     = PrivilegeQuery

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


# Association table
account_privileges = db.Table(
    'account_privileges', db.metadata,
    db.Column('account_github_id', db.Integer, db.ForeignKey('accounts.github_id')),
    db.Column('privilege_id', db.Integer, db.ForeignKey('privileges.id'))
)


class GroupQuery(db.Query):

    def get(self, privilege):
        if isinstance(privilege, basestring):
            return self.filter(Group.name == privilege).first()
        return BaseQuery.get(self, privilege)


class Group(db.Model):
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

    query_class   = GroupQuery

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return u'<{0} {1!r}:{2!r}>'.format(self.__class__.__name__, self.id, self.name)


group_accounts = db.Table(
    'group_accounts', db.metadata,
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id')),
    db.Column('account_github_id', db.Integer, db.ForeignKey('accounts.github_id'))
)


group_privileges = db.Table(
    'group_privileges', db.metadata,
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id')),
    db.Column('privilege_id', db.Integer, db.ForeignKey('privileges.id'))
)
