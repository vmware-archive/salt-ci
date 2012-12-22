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

log = logging.getLogger(__name__)


# ----- Blueprint ------------------------------------------------------------------------------->
hooks = Blueprint('hooks', __name__, url_prefix='/hooks')
# <---- Blueprint --------------------------------------------------------------------------------


# ----- Views ----------------------------------------------------------------------------------->
@hooks.route('/push/<string(length=32):token>', methods=('POST',))
def push(token):
    if request.remote_addr not in app.config.get('GITHUB_PAYLOAD_IPS', ()):
        log.warning(
            'Got a hooks push request from an invalid address({0}). Request Values: {1}'.format(
                request.remote_addr, request.values
            )
        )
        abort(401)

    # Just log the payload information
    try:
        log.debug(
            'Incoming GitHub payload:\n{0}'.format(
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
