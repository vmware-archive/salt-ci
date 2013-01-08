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
from saltci.database.models import Account, Organization, Repository


log = logging.getLogger(__name__)


# ----- Blueprints & Menu Entries -------------------------------------------------------------->
account = Blueprint('account', __name__, url_prefix='/account')

prefs_menu_entry = menus.add_menu_entry(
    "top_account_nav", _("Profile"), 'account.prefs', priority=-1,
    visiblewhen=check_wether_account_is_not_none
)
account_view_nav.add_menu_item(prefs_menu_entry)

repos_menu_entry = menus.add_menu_entry(
    "top_account_nav", _("Repositories"), 'account.repos', priority=-1,
    visiblewhen=check_wether_account_is_not_none
)
account_view_nav.add_menu_item(repos_menu_entry)
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

class RepositoriesForm(DBBoundForm):

    title           = _('Repositories')

    #repositories    = QuerySelectMultipleField(_('Repositories'))

    update          = PrimarySubmitField(_('Update Repositories'))
    sync_repos      = SubmitField(_('Synchronise Repositories'))

    #def __init__(self, db_entry=None, formdata=None, *args, **kwargs):
    #    super(RepositoriesForm, self).__init__(db_entry, formdata, *args, **kwargs)
    #    self.repositories.query = db_entry.repositories
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
        'scopes': 'repo',
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
        'scopes': 'repo',
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
            # We do not know this token.
            gh = github.Github(token)
            gh_user = gh.get_user()
            # Do we know the account?
            account = Account.query.get(gh_user.id)
            if account is None:
                # This is a brand new account
                new_account = Account(
                    gh_id=gh_user.id,
                    gh_login=gh_user.login,
                    gh_token=token,
                    avatar_url=gh_user.avatar_url
                )
                db.session.add(new_account)
            else:
                # We know this account though the access token has changed.
                # Let's update the account details.
                account.gh_id = gh_user.id
                account.gh_login = gh_user.login
                account.gh_token = token
                account.avatar_url=gh_user.avatar_url
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


@account.route('/repositories', methods=('GET', 'POST'))
@authenticated_permission.require(403)
def repos():
    form = RepositoriesForm(db_entry=g.identity.account, formdata=request.form.copy())
    print 123, request.form
    if form.validate_on_submit():
        if 'sync_repos' in request.values:
            current_organizations = set(g.identity.account.organizations)
            current_repositories = set(g.identity.account.repositories.all())
            # Grab all repositories from GitHub and sync our database against them
            gh = github.Github(session['ght'])
            account = gh.get_user()
            for org in account.get_orgs():
                organization = Organization.query.get(org.id)
                if organization is None:
                    # We do not yet know this organization, let's add it to the database
                    organization = Organization(org.id, org.name, org.login, org.avatar_url)
                    # Let's add ourselves to this organization
                    g.identity.account.organizations.add(organization)
                elif organization is not None and organization in current_organizations:
                    # We already know this organization and we're in it, remove from the
                    # check-list.
                    current_organizations.remove(organization)

                org_repositories = set(organization.repositories)
                for repo in org.get_repos():
                    if repo.permissions.admin is False:
                        # Since we can't administrate this repository, skip it
                        continue
                    repository = Repository.query.get(repo.id)
                    if repository is None:
                        repository = Repository(
                            id=repo.id,
                            name=repo.name,
                            url=repo.html_url,
                            description=repo.description,
                            fork=repo.fork,
                            private=repo.private,
                            push_active=False,
                            pull_active=False
                        )
                        organization.repositories.add(repository)
                    else:
                        # Let's update entry
                        repository.name = repo.name
                        repository.url = repo.html_url
                        repository.fork = repo.fork
                        repository.description = repo.description
                        repository.private = repo.private
                        if repository not in organization.repositories:
                            # Although we already know this repository, it's now owned by this
                            # organization.
                            organization.repositories.add(repository)
                        if repository in org_repositories:
                            # remove it from the check-list
                            org_repositories.remove(repository)
                        if repository in current_repositories:
                            # let's remove it from the check-list
                            current_repositories.remove(repository)
                    g.identity.account.managed_repositories.add(repository)
                for org in current_organizations:
                    # We apparently left some organizations:
                    g.identity.account.organizations.remove(org)
                for repository in org_repositories:
                    # The organization is apparently not managing these repositories anymore
                    organization.repositories.remove(repository)
                db.session.commit()
            for repo in account.get_repos():
                if repo.permissions.admin is False:
                    # WTF!?
                    # Since we can't administrate this repository, skip it
                    continue
                repository = Repository.query.get(repo.id)
                if repository is None:
                    repository = Repository(
                        id=repo.id,
                        name=repo.name,
                        url=repo.html_url,
                        description=repo.description,
                        fork=repo.fork,
                        private=repo.private,
                        push_active=False,
                        pull_active=False
                    )
                    g.identity.account.repositories.append(repository)
                else:
                    # Let's update entry
                    repository.name = repo.name
                    repository.url = repo.html_url
                    repository.description = repo.description
                    repository.private = repo.private
                    if repository not in g.identity.account.repositories:
                        g.identity.account.repositories.add(repository)
                    if repository in current_repositories:
                        # let's remove it from the check-list
                        current_repositories.remove(repository)
                g.identity.account.managed_repositories.add(repository)
            for repository in current_repositories:
                # We're apparently not managing these
                g.identity.account.repositories.remove(repository)
                g.identity.account.managed_repositories.remove(repository)
            db.session.commit()
            return redirect_to('account.repos')

        # We're updating, the active status
        push_active = request.form.getlist('push_active', type=int)
        if not push_active and g.identity.account.repositories.filter(Repository.push_active==True).count():
            # Disable all enabled
            #g.identity.account.repositories.filter(Repository.push_active==True).update(
            #    {'push_active': False}, synchronize_session=False
            #)
            for repo in g.identity.account.repositories.filter(Repository.push_active==True):
                repo.push_active = False
        elif push_active and not g.identity.account.repositories.filter(Repository.push_active==True).count():
            # There's none enabled, no enable/disable sync needed. Just enable those from the form
            #g.identity.account.repositories.filter(Repository.id.in_(push_active)).update(
            #    {'push_active': True}, synchronize_session=False
            #)
            # ^^^^ <- ArgumentError: Only update via a single table query is currently supported
            for repo in g.identity.account.repositories.filter(Repository.id.in_(push_active)):
                repo.push_active = True
        else:
            # We need to sync, setting all to disable and then enable those that were passed to the
            # form might become too expensive.
            # Let's do it the proper way.
            #
            # First those enabled on the database and now disabled from the form
            #g.identity.account.repositories.filter(
            #    db.and_(
            #        db.not_(Repository.id.in_(push_active)),
            #        Repository.push_active==True
            #    )
            #).update(
            #    {'push_active': False}, synchronize_session=False
            #)
            db_enabled_not_on_form = g.identity.account.repositories.filter(
                db.and_(
                    db.not_(Repository.id.in_(push_active)),
                    Repository.push_active==True
                )
            )
            for repo in db_enabled_not_on_form:
                repo.push_active = False

            # Then those which are active on the form but not yet active on the database
            #g.identity.account.repositories.filter(
            #    db.and_(
            #        Repository.id.in_(push_active),
            #        Repository.push_active==False
            #    )
            #).update(
            #    {'push_active': True}, synchronize_session=False
            #)

            active_on_form_not_on_db = g.identity.account.repositories.filter(
                db.and_(
                    Repository.id.in_(push_active),
                    Repository.push_active==False
                )
            )
            for repo in active_on_form_not_on_db:
                repo.push_active = True

        pull_active = request.form.getlist('pull_active', type=int)
        if not pull_active and g.identity.account.repositories.filter(Repository.pull_active==True).count():
            # Disable all enabled
            for repo in g.identity.account.repositories.filter(Repository.pull_active==True):
                repo.pull_active = False
        elif pull_active and not g.identity.account.repositories.filter(Repository.pull_active==True).count():
            # There's none enabled, no enable/disable sync needed. Just enable those from the form
            for repo in g.identity.account.repositories.filter(Repository.id.in_(pull_active)):
                repo.pull_active = True
        else:
            # We need to sync, setting all to disable and then enable those that were passed to the
            # form might become too expensive.
            # Let's do it the proper way.
            #
            # First those enabled on the database and now disabled from the form
            db_enabled_not_on_form = g.identity.account.repositories.filter(
                db.and_(
                    db.not_(Repository.id.in_(pull_active)),
                    Repository.pull_active==True
                )
            )
            for repo in db_enabled_not_on_form:
                repo.pull_active = False

            active_on_form_not_on_db = g.identity.account.repositories.filter(
                db.and_(
                    Repository.id.in_(pull_active),
                    Repository.pull_active==False
                )
            )
            for repo in active_on_form_not_on_db:
                repo.pull_active = True

        db.session.commit()
        return redirect_to('account.repos')

    # We're not updating anything, just show them the data
    own_repos = g.identity.account.repositories.filter(Repository.fork == False).all()
    fork_repos = g.identity.account.repositories.filter(Repository.fork == True).all()
    return render_template(
        'account/repos.html', own_repos=own_repos, fork_repos=fork_repos, form=form
    )
# <---- Views ------------------------------------------------------------------------------------
