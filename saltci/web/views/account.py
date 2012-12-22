# -*- coding: utf-8 -*-
'''
    saltci.web.views.account
    ~~~~~~~~~~~~~~~~~~~~~~~~

    The user's account view.

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

import logging
import urllib
import httplib
import github
from uuid import uuid4
from saltci.web.application import *
from saltci.database import db
from saltci.database.models import Account

log = logging.getLogger(__name__)


# ----- Blueprints & Menu Entries -------------------------------------------------------------->
account = Blueprint('account', __name__, url_prefix='/account')
# <---- Blueprints & Menu Entries ---------------------------------------------------------------


# ----- Views ----------------------------------------------------------------------------------->
@account.route('/signin', methods=('GET',))
def signin():
    github_token = session.get('ght', None)
    if github_token is not None and g.account is not None:
        # This user is already authenticated and is valid user(it's present in our database)
        return redirect(url_for('main.index'))
    elif github_token is not None and g.account is None:
        # If we reached this point, the github token is not in our database
        session.pop('ght')

    # Let's login the user using github's oauth

    # GitHub Access Scopes:
    #   http://developer.github.com/v3/oauth/#scopes
    github_state = uuid4().hex
    session['github_state'] = github_state

    urlargs = {
        'state': github_state,
        # 'scopes': 'repo:status', # for let's only get the basic scope
        'client_id': app.config.get('GITHUB_CLIENT_ID'),
        'redirect_uri': url_for('account.callback', _external=True)
    }
    return redirect(
        'https://github.com/login/oauth/authorize?{0}'.format(
            urllib.urlencode(urlargs)
        )
    )


@account.route('/signin/callback', methods=('GET',))
def callback():
    code = request.args.get('code')
    github_state = request.args.get('state')
    if github_state != session.pop('github_state', None):
        abort("This authentication has been tampered with! Aborting!!!")

    urlargs = {
        'code': code,
        'state': github_state,
        'client_id': app.config.get('GITHUB_CLIENT_ID'),
        'client_secret': app.config.get('GITHUB_CLIENT_SECRET'),
    }

    # let's get some json back
    headers = {'Accept': 'application/json'}

    conn = httplib.HTTPSConnection('github.com')
    conn.request(
        'POST',
        '/login/oauth/access_token?{0}'.format(urllib.urlencode(urlargs)),
        headers=headers
    )
    resp = conn.getresponse()
    data = resp.read()
    if resp.status == 200:
        data = json.loads(data)
        token = data['access_token']
        session['ght'] = token

        account = Account.query.from_github_token(token)
        if account is None:
            gh = github.Github(token)
            gh_user = gh.get_user()
            new_account = Account(
                github_id=gh_user.id,
                github_login=gh_user.login,
                github_token=token,
                gravatar_id=gh_user.gravatar_id
            )
            db.session.add(new_account)
            db.session.commit()

    return redirect(url_for('main.index'))


@account.route('/signout', methods=('GET',))
def signout():
    if session.get('ght', None) is None:
        # Not logged in
        pass
    session.pop('ght')
    return redirect(url_for('main.index'))


@account.route('/preferences', methods=('GET', 'POST'))
def prefs():
    pass
# <---- Views ------------------------------------------------------------------------------------
