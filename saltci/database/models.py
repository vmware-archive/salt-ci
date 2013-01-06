# -*- coding: utf-8 -*-
"""
    saltci.database.models
    ~~~~~~~~~~~~~~~~~~~~~~

    Salt-CI database models

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
"""

import logging
from uuid import uuid4
from datetime import datetime
from saltci.database import db, orm


log = logging.getLogger(__name__)


# pylint: disable-msg=E1101

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
    repositories    = db.dynamic_loader("Repository", secondary="account_repositories",
                                        backref='owner', lazy=True, collection_class=set,
                                        cascade='all, delete')

    query_class     = AccountQuery

    def __init__(self, github_id, github_login, github_token, gravatar_id):
        self.gh_id = github_id
        self.gh_login = github_login
        self.gh_token = github_token
        self.gravatar_id = gravatar_id

    def update_last_login(self):
        self.last_login = datetime.utcnow()

    def generate_hooks_token(self):
        log.info('Generating hooks token for user id: {0}'.format(self.gh_login))
        self.hooks_token = uuid4().hex


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
# pylint: disable-msg=C0103
account_privileges = db.Table(
    'account_privileges', db.metadata,
    db.Column('account_github_id', db.Integer, db.ForeignKey('accounts.github_id')),
    db.Column('privilege_id', db.Integer, db.ForeignKey('privileges.id'))
)
# pylint: enable-msg=C0103


class GroupQuery(db.Query):

    def get(self, privilege):
        if isinstance(privilege, basestring):
            return self.filter(Group.name == privilege).first()
        return db.Query.get(self, privilege)


class Group(db.Model):
    __tablename__ = 'groups'

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(30))

    accounts      = db.dynamic_loader("Account", secondary="group_accounts",
                                      backref=db.backref(
                                          "groups", lazy=True, collection_class=set
                                      ))
    privileges    = db.relation("Privilege", secondary="group_privileges",
                                backref='privileged_groups', lazy=True, collection_class=set,
                                cascade='all, delete')

    query_class   = GroupQuery

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return u'<{0} {1!r}:{2!r}>'.format(self.__class__.__name__, self.id, self.name)


# pylint: disable-msg=C0103
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
# pylint: enable-msg=C0103


class OrganizationQuery(db.Query):

    def get(self, org):
        if isinstance(org, basestring):
            return self.filter(Organization.login == org).first()
        return db.Query.get(self, org)


class Organization(db.Model):
    __tablename__ = 'organizations'

    id            = db.Column('github_id', db.Integer, primary_key=True)
    name          = db.Column('github_name', db.String)
    login         = db.Column('github_login', db.String, index=True)

    # Relationships
    accounts      = db.relation("Account", secondary="account_organizations",
                                backref=db.backref(
                                    'organizations', lazy=True, collection_class=set
                                ), lazy=True, collection_class=set, cascade='all, delete')

    repositories  = db.relation("Repository", secondary="organization_repositories",
                                backref=db.backref(
                                    'organization', lazy=True, collection_class=set
                                ), lazy=True, collection_class=set, cascade='all, delete')

    query_class   = OrganizationQuery

    def __init__(self, id, name, login):
        self.id = id
        self.name = name
        self.login = login


# pylint: disable-msg=C0103
account_organizations = db.Table(
    'account_organizations', db.metadata,
    db.Column('account_id', db.Integer, db.ForeignKey('accounts.github_id')),
    db.Column('organization_id', db.Integer, db.ForeignKey('organizations.github_id'))
)
# pylint: enable-msg=C0103


class Repository(db.Model):
    __tablename__ = 'repositories'

    id              = db.Column('github_id', db.Integer, primary_key=True)
    name            = db.Column('github_name', db.String, index=True)
    url             = db.Column('github_url', db.String)
    description     = db.Column('github_description', db.String)
    fork            = db.Column('github_fork', db.Boolean, default=False)
    private         = db.Column('github_private', db.Boolean, default=False)
    active          = db.Column(db.Boolean, default=True)

    # Relationships
    owner           = None    # Defined in account
    organization    = None    # Defined in organization

    admins        = db.relation("Account", secondary="repository_administrators",
                                backref=db.backref(
                                    'managed_repositories', lazy=True, collection_class=set
                                ),  lazy=True, collection_class=set, cascade='all, delete')

    def __init__(self, id, name, url, description,
                 fork=False, private=False, active=True):
        '''
        Repository

        :param id: repository id
        :param name: repository name
        :param url: repository url
        :param description: repository description
        :param fork: is this a forked repository
        :param private: is the repository private
        :param active: is the repository active
        :returns: Repository

        '''
        self.id = id
        self.name = name
        self.url = url
        self.description = description
        self.fork = fork
        self.private = private
        self.active = active


# pylint: disable-msg=C0103
account_repositories = db.Table(
    'account_repositories', db.metadata,
    db.Column('account_id', db.Integer, db.ForeignKey('accounts.github_id')),
    db.Column('repository_id', db.Integer, db.ForeignKey('repositories.github_id'))
)


organization_repositories =  db.Table(
    'organization_repositories', db.metadata,
    db.Column('organization_id', db.Integer, db.ForeignKey('organizations.github_id')),
    db.Column('repository_id', db.Integer, db.ForeignKey('repositories.github_id'))
)


repository_administrators =  db.Table(
    'repository_administrators', db.metadata,
    db.Column('repository_id', db.Integer, db.ForeignKey('repositories.github_id')),
    db.Column('account_id', db.Integer, db.ForeignKey('accounts.github_id'))
)
# pylint: enable-msg=C0103


class Commit(db.Model):
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

    def __init__(self, sha, ref, message, url, compare_url, commited_at, commiter_name,
                 commiter_email, author_name, author_email):
        '''
        :param sha: @todo
        :param ref: @todo
        :param message: @todo
        :param url: @todo
        :param compare_url: @todo
        :param commited_at: @todo
        :param commiter_name: @todo
        :param commiter_email: @todo
        :param author_name: @todo
        :param author_email: @todo
        :returns: @todo

        '''
        self.sha = sha
        self.ref = ref
        self.message = message
        self.url = url
        self.compare_url = compare_url
        self.commited_at = commited_at
        self.committer_name = commiter_name
        self.committer_email = commiter_email
        self.author_name = author_name
        self.author_email = author_email

    @property
    def branch(self):
        return self.ref.split('refs/heads/')[-1]
