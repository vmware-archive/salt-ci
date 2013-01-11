# -*- coding: utf-8 -*-
'''
    saltci.web.permissions
    ~~~~~~~~~~~~~~~~~~~~~~

    Salt-CI permissions system.

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

import logging
import github
from functools import wraps
from flask import abort, g, session
from flask.ext.principal import (
    AnonymousIdentity, Identity, Permission, Principal, RoleNeed, TypeNeed, identity_loaded,
    identity_changed, ActionNeed, PermissionDenied
)
from flask.ext.wtf import Form, ValidationError
from sqlalchemy.exc import OperationalError
from saltci.database import db, models
from saltci.web.signals import after_identity_account_loaded, application_configured

log = logging.getLogger(__name__)

# ----- Simplify * Imports ---------------------------------------------------------------------->
ALL_PERMISSIONS_IMPORTS = [
    'admin_permission',
    'manager_permission',
    'admin_or_manager_permission',
    'anonymous_permission',
    'authenticated_permission',
    'require_permissions',
    'identity_changed',
    'Identity',
    'AnonymousIdentity',
]
__all__ = ALL_PERMISSIONS_IMPORTS + ['ALL_PERMISSIONS_IMPORTS']
# <---- Simplify * Imports -----------------------------------------------------------------------

# Main permissions instance
principal = Principal(use_sessions=True, skip_static=True)

# Let's define some default roles/permissions
admin_role = RoleNeed('administrator')
admin_permission = Permission(admin_role)

manager_role = RoleNeed('manager')
manager_permission = Permission(manager_role)

admin_or_manager_permission = Permission(admin_role, manager_role)

anonymous_permission = Permission()
authenticated_permission = Permission(TypeNeed('authenticated'))


@application_configured.connect
def on_application_configured(app):
    # Finalize principal configuration
    principal.init_app(app)

    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        log.trace('Identity loaded: {0}'.format(identity))

        if identity.auth_type == '':
            identity.account = None
            return

        try:
            identity.account = account = models.Account.query.get(int(identity.name))
            if account is not None:
                log.trace(
                    'User \'{0}\' loaded from identity {1}'.format(
                        account.gh_login, identity
                    )
                )
                account.update_last_login()
                identity.provides.add(TypeNeed('authenticated'))
                # Update the privileges that a user has
                for privilege in account.privileges:
                    identity.provides.add(ActionNeed(privilege.name))
                for group in account.groups:
                    # And for each of the groups the user belongs to
                    for privilege in group.privileges:
                        # Add the group privileges to the user
                        identity.provides.add(RoleNeed(privilege.name))
                # Setup this user's github api access
                identity.github = github.Github(
                    account.gh_token,
                    client_id=app.config.get('GITHUB_CLIENT_ID'),
                    client_secret=app.config.get('GITHUB_CLIENT_SECRET')
                )
                after_identity_account_loaded.send(sender, account=identity.account)
        except OperationalError:
            # Database has not yet been setup
            pass


@principal.identity_saver
def save_request_identity(identity):
    log.trace('On save_request_identity: {0}'.format(identity))
    if getattr(identity, 'account', None) is None:
        log.trace('No account associated with identity. Nothing to store.')
        return

    for need in identity.provides:
        log.debug('Identity provides: {0}'.format(need))
        if need.method in ('type', 'role'):
            # We won't store type methods, ie, "authenticated", nor, role
            # methods which are permissions belonging to groups and managed
            # on a future administration panel.
            continue

        privilege = Privilege.query.get(need)
        if not privilege:
            log.debug('Privilege {0!r} does not exist. Creating...'.format(need))
            privilege = Privilege(need)

        if privilege not in identity.account.privileges:
            identity.account.privileges.add(privilege)
    db.session.commit()


def require_permissions(perms, from_keys=(), http_exception=None):
    @wraps(f)
    def decorated(*args, **kwargs):
        if isinstance(from_keys, basestring):
            keys = [from_keys]
        else:
            keys = from_keys

        if not isinstance(perms, (list, tuple)):
            permissions = [perms]
        else:
            permissions = list(perms)

        for key in keys:
            value = kwargs.get(key, None)
            if value:
                permission = Permission(ActionNeed("manage-%s" % value))
                permissions.append(permission)

        denied_permissions = []
        for permission in permissions:
            if not isinstance(permission, Permission):
                permission = Permission(ActionNeed(permission))
            if permission.allows(g.identity):
                return f(*args, **kwargs)

            denied_permissions.append(permission)

        if denied_permissions:
            if args and isinstance(args[0], Form):
                # Some black magic to restore the value to it's original
                field = args[1]
                field_value_from_db = getattr(field, 'value_from_db', None)
                if field_value_from_db and field_value_from_db != field.data:
                    field.data = field_value_from_db
                    raise ValidationError(_(
                        'You\'re not allowed to change this field.'
                    ))
            elif http_exception:
                abort(http_exception, denied_permissions)
            else:
                raise PermissionDenied(denied_permissions)

    return decorated
