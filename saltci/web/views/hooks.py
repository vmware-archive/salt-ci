# -*- coding: utf-8 -*-
'''
    saltci.web.views.hooks
    ~~~~~~~~~~~~~~~~~~~~~~

    This is the hooks module. It will get hit by github at every push once setup.

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

import json
import pprint
import logging
from saltci.web.application import *
from saltci.database.models import Account, Repository

log = logging.getLogger(__name__)

# http://developer.github.com/v3/repos/statuses/

# ----- Blueprint ------------------------------------------------------------------------------->
hooks = Blueprint('hooks', __name__, url_prefix='/hooks')
# <---- Blueprint --------------------------------------------------------------------------------


# ----- Views ----------------------------------------------------------------------------------->
@hooks.route('/push/<login>/<reponame>', methods=('POST',), defaults={'organization': None})
@hooks.route('/push/<login>/<organization>/<reponame>', methods=('POST',))
def push(login=None, organization=None, reponame=None):
    try:
        payload = request.json
        if payload is None:
            log.warning(
                'Got a malformed request from {0!r}. Request arguments: {1!r}  Request Values: '
                '{2!r}'.format(
                    request.remote_addr, request.args, request.values
                )
            )
            return abort(404)
    except Exception, err:
        log.warning(
            'Got a malformed request from {0!r} which threw an exeption. Exception: {1!r}'.format(
                request.remote_addr, err
            )
        )
        return abort(404)

    if request.remote_addr not in app.config.get('GITHUB_PAYLOAD_IPS', ()):
        log.warning(
            'Got a hooks push request from an invalid address({0}). Payload: {1}'.format(
                request.remote_addr, pprint.pformat(payload, indent=2)
            )
        )
        return abort(404)

    account = Account.query.get(login)
    if account is None:
        log.warning(
            'Got a hooks push request from {0} with an invalid login({1}). '
            'Request Values: {2}'.format(
                request.remote_addr, login, pprint.pformat(payload, indent=2)
            )
        )
        return abort(401)

    if organization is not None:
        org = Organization.query.get(organization)
        if org is None:
            log.warning(
                'Got a hooks push request from {0} with an invalid organization({1}). '
                'Payload: {2}'.format(
                    request.remote_addr, organization, pprint.pformat(payload, indent=2)
                )
            )
            return abort(404)
        elif org not in account.organizations:
            log.warning(
                'Got a hooks push request from {0} with an organization the user does not '
                'belong to({1}). Payload: {2}'.format(
                    request.remote_addr, organization, pprint.pformat(payload, indent=2)
                )
            )
            return abort(404)

    repository = account.managed_repositories.filter(Repository.name == reponame).first()
    if repository is None:
        log.warning(
            'Got a hooks push request from {0} with an invalid repository({1}). '
            'Payload: {2}'.format(
                request.remote_addr, reponame, pprint.pformat(payload, indent=2)
            )
        )
        return abort(404)

    # Just log the payload information
    log.debug(
        'Incoming GitHub Push payload:\n{0}'.format(
            pprint.pformat(payload, indent=2)
        )
    )

    return jsonify({'result': 'OK'})


@hooks.route('/pull/<login>/<reponame>', methods=('POST',), defaults={'organization': None})
@hooks.route('/pull/<login>/<organization>/<reponame>', methods=('POST',))
def pull(login=None, organization=None, reponame=None):
    try:
        payload = request.json
        if payload is None:
            log.warning(
                'Got a malformed request from {0!r}. Request arguments: {1!r}  Request Values: '
                '{2!r}'.format(
                    request.remote_addr, request.args, request.values
                )
            )
            abort(404)
    except Exception, err:
        log.warning(
            'Got a malformed request from {0!r} which threw an exeption. Exception: {1!r}'.format(
                request.remote_addr, err
            )
        )
        abort(404)

    if request.remote_addr not in app.config.get('GITHUB_PAYLOAD_IPS', ()):
        log.warning(
            'Got a hooks pull request from an invalid address({0}). Payload: {1}'.format(
                request.remote_addr, pprint.pformat(payload, indent=2)
            )
        )
        abort(404)

    account = Account.query.get(login)
    if account is None:
        log.warning(
            'Got a hooks pull request from {0} with an invalid login({1}). '
            'Request Values: {2}'.format(
                request.remote_addr, login, pprint.pformat(payload, indent=2)
            )
        )
        abort(401)

    if organization is not None:
        org = Organization.query.get(organization)
        if org is None:
            log.warning(
                'Got a hooks pull request from {0} with an invalid organization({1}). '
                'Payload: {2}'.format(
                    request.remote_addr, organization, pprint.pformat(payload, indent=2)
                )
            )
            abort(404)
        elif org not in account.organizations:
            log.warning(
                'Got a hooks pull request from {0} with an organization the user does not '
                'belong to({1}). Payload: {2}'.format(
                    request.remote_addr, organization, pprint.pformat(payload, indent=2)
                )
            )
            abort(404)

    repository = account.managed_repositories.filter(Repository.name == reponame).first()
    if repository is None:
        log.warning(
            'Got a hooks pull request from {0} with an invalid repository({1}). '
            'Payload: {2}'.format(
                request.remote_addr, reponame, pprint.pformat(payload, indent=2)
            )
        )
        abort(404)

    # Just log the payload information
    log.debug(
        'Incoming GitHub Pull payload:\n{0}'.format(
            pprint.pformat(payload, indent=2)
        )
    )

    return jsonify({'result': 'OK'})
# <---- Views ------------------------------------------------------------------------------------
