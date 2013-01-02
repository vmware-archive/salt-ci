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
from flask.ext.wtf import *
from saltci.web.application import *
from saltci.web.forms import *
from saltci.database import db
from saltci.database.models import Account


log = logging.getLogger(__name__)


# ----- Blueprints & Menu Entries -------------------------------------------------------------->
account = Blueprint('account', __name__, url_prefix='/account')
# <---- Blueprints & Menu Entries ---------------------------------------------------------------


# ----- Forms ----------------------------------------------------------------------------------->
class ProfileForm(DBBoundForm):

    title       = _('My Account')

    gh_login    = TextField(_('Username'), validators=[Required()])
    timezone    = SelectField(_('Timezone'))
    locale      = SelectField(_('Locale'),
                              description=_('This will be the language Salt-CI will use to you.'))
    hooks_token = HiddenField(_('Hooks Token'))

    # Actions
    update      = PrimarySubmitField(_('Update Details'))
    gen_token   = SubmitField(_('Generate Hooks Token'))

    def __init__(self, db_entry=None, formdata=None, *args, **kwargs):
        super(ProfileForm, self).__init__(db_entry, formdata, *args, **kwargs)
        self.timezone.choices = build_timezones(get_locale())
        self.locale.choices = [
            (l.language, l.display_name) for l in babel.list_translations()
        ]

    def validate_locale(self, field):
        if field.data is None:
            # In case there's only one locale, then the field is not
            # rendered. Re-set the default.
            field.data = self.db_entry.locale

#    def validate(self):
#
#        if self.locale.data is None:
#            # In case there's only one locale, then the field is not
#            # rendered. Re-set the default.
#            self.locale.data = self.db_entry.locale
#        return super(ProfileForm, self).validate()
# <---- Forms ------------------------------------------------------------------------------------


# ----- Views ----------------------------------------------------------------------------------->
@account.route('/signin', methods=('GET',))
def signin():
    github_token = session.get('ght', None)
    if github_token is not None and g.identity.account is not None:
        # This user is already authenticated and is valid user(it's present in our database)
        flash(_('You\'re already authenticated!'))
        return redirect(url_for('main.index'))
    elif github_token is not None and g.identity.account is None:
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
    log.debug('New signin request. Redirect args: {0}'.format(urlargs))
    return redirect(
        'https://github.com/login/oauth/authorize?{0}'.format(
            urllib.urlencode(urlargs)
        )
    )


@account.route('/signin/callback', methods=('GET',))
def callback():
    github_state = request.args.get('state', None)
    if github_state is None or github_state != session.pop('github_state', None):
        flash(_('This authentication has been tampered with! Aborting!!!'), 'error')

    code = request.args.get('code')

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

        identity_changed.send(app, identity=Identity(token, 'dbm'))
        flash(_('You are now signed in.'), 'success')
    return redirect(url_for('main.index'))


@account.route('/signout', methods=('GET',))
@authenticated_permission.require(403)
def signout():
    if session.get('ght', None) is not None:
        session.pop('ght')
        identity_changed.send(app, identity=AnonymousIdentity())
        flash(_('You are now signed out.'), 'success')
    else:
        flash(_('You\'re not authenticated!'))
    return redirect(url_for('main.index'))


@account.route('/preferences', methods=('GET', 'POST'))
@authenticated_permission.require(403)
def prefs():
    form = ProfileForm(db_entry=g.identity.account, formdata=request.values.copy())
    if form.validate_on_submit():
        if 'gen-token' in request.values:
            g.identity.account.generate_hooks_token()
            db.session.commit()
            flash('New token generated', 'success')
            return redirect_to('account.prefs')
        db.update_dbentry_from_form(g.identity.account, form)
        db.session.commit()
        flash(_('Account details updated.'), 'success')
        return redirect_to('account.prefs')
    return render_template('account/prefs.html', form=form)
# <---- Views ------------------------------------------------------------------------------------
