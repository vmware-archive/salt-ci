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
from saltci.database.models import Account

log = logging.getLogger(__name__)


# ----- Blueprint ------------------------------------------------------------------------------->
hooks = Blueprint('hooks', __name__, url_prefix='/hooks')
# <---- Blueprint --------------------------------------------------------------------------------


# ----- Views ----------------------------------------------------------------------------------->
@hooks.route('/push/<login>/<reponame>', methods=('POST',), defaults={'organization': None})
@hooks.route('/push/<login>/<organization>/<reponame>', methods=('POST',))
def push(login=None, organization=None, reponame=None):
    if request.remote_addr not in app.config.get('GITHUB_PAYLOAD_IPS', ()):
        log.warning(
            'Got a hooks push request from an invalid address({0}). Request Values: {1}'.format(
                request.remote_addr, request.values
            )
        )
        abort(401)

    account = Account.query.get(login)
    if account is None:
        log.warning(
            'Got a hooks push request from {0} with an invalid login({1}). '
            'Request Values: {2}'.format(
                request.remote_addr, login, pprint.pformat(request.values, indent=2)
            )
        )
        abort(401)

    if organization is not None:
        org = Organization.query.get(organization)
        if org is None:
            log.warning(
                'Got a hooks pull request from {0} with an invalid organization({1}). '
                'Request Values: {2}'.format(
                    request.remote_addr, organization, pprint.pformat(request.values, indent=2)
                )
            )
            abort(401)
        elif org not in account.organizations:
            log.warning(
                'Got a hooks pull request from {0} with an organization the user does not '
                'belong to({1}). Request Values: {2}'.format(
                    request.remote_addr, organization, pprint.pformat(request.values, indent=2)
                )
            )
            abort(401)

    repository = account.managed_repositories.filter(models.Repository.name == 'salt').first()
    if repository is None:
        log.warning(
            'Got a hooks push request from {0} with an invalid repository({1}). '
            'Request Values: {2}'.format(
                request.remote_addr, reponame, pprint.pformat(request.values, indent=2)
            )
        )
        abort(401)

    # Just log the payload information
    try:
        log.debug(
            'Incoming GitHub Push payload:\n{0}'.format(
                pprint.pformat(
                    json.loads(request.form.get('payload')),
                    indent=2
                )
            )
        )
    except:
        log.debug('RAW DATA: {0}'.format(request.data))
        log.debug('Args: {0}'.format(request.args))
        log.debug('Values: {0}'.format(request.values))
    return jsonify({'result': 'OK'})


@hooks.route('/pull/<login>/<reponame>', methods=('POST',), defaults={'organization': None})
@hooks.route('/pull/<login>/<organization>/<reponame>', methods=('POST',))
def pull(login=None, organization=None, reponame=None):
    if request.remote_addr not in app.config.get('GITHUB_PAYLOAD_IPS', ()):
        log.warning(
            'Got a hooks pull request from an invalid address({0}). Request Values: {1}'.format(
                request.remote_addr, request.values
            )
        )
        abort(401)

    account = Account.query.get(login)
    if account is None:
        log.warning(
            'Got a hooks pull request from {0} with an invalid login({1}). '
            'Request Values: {2}'.format(
                request.remote_addr, login, pprint.pformat(request.values, indent=2)
            )
        )
        abort(401)

    if organization is not None:
        org = Organization.query.get(organization)
        if org is None:
            log.warning(
                'Got a hooks pull request from {0} with an invalid organization({1}). '
                'Request Values: {2}'.format(
                    request.remote_addr, organization, pprint.pformat(request.values, indent=2)
                )
            )
            abort(401)
        elif org not in account.organizations:
            log.warning(
                'Got a hooks pull request from {0} with an organization the user does not '
                'belong to({1}). Request Values: {2}'.format(
                    request.remote_addr, organization, pprint.pformat(request.values, indent=2)
                )
            )
            abort(401)

    repository = account.managed_repositories.filter(models.Repository.name == 'salt').first()
    if repository is None:
        log.warning(
            'Got a hooks pull request from {0} with an invalid repository({1}). '
            'Request Values: {2}'.format(
                request.remote_addr, reponame, pprint.pformat(request.values, indent=2)
            )
        )
        abort(401)

    # Just log the payload information
    try:
        log.debug(
            'Incoming GitHub Pull payload:\n{0}'.format(
                pprint.pformat(
                    json.loads(request.form.get('payload')),
                    indent=2
                )
            )
        )
    except:
        log.debug('RAW DATA: {0}'.format(request.data))
        log.debug('Args: {0}'.format(request.args))
        log.debug('Values: {0}'.format(request.values))
    return jsonify({'result': 'OK'})
# <---- Views ------------------------------------------------------------------------------------
