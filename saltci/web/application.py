# -*- coding: utf-8 -*-
'''
    saltci.web.application
    ~~~~~~~~~~~~~~~~~~~~~~

    Flask Application

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

import sys
from flask import (
    Flask, flash, g, redirect, url_for, request, session, Markup, abort, Blueprint, json, jsonify,
    render_template
)
from flask.signals import request_started, request_finished
from flask.ext.babel import Babel, get_locale, gettext as _
from flask.ext.cache import Cache
from flask.ext.menubuilder import MenuBuilder, MenuItem, MenuItemContent
from flask.ext.principal import Principal
from flask.ext.sqlalchemy import get_debug_queries
from urlparse import urlparse, urljoin
from traceback import format_exception
from werkzeug.contrib.fixers import ProxyFix
from saltci.web.signals import application_configured, configuration_loaded
from saltci.web.permissions import *


# ----- Simplify * Imports ---------------------------------------------------------------------->
__all__ = [
    'app',
    'flash',
    'g',
    'redirect',
    'redirect_to',
    'redirect_back',
    'url_for',
    'request',
    'session',
    'Markup',
    'abort',
    'Blueprint',
    'json',
    'jsonify',
    'render_template',
    'babel',
    '_',
    'get_locale',
    'cache',
    # Navigation Related Items
    'menus',
    'MenuItem',
    'MenuItemContent',
    'top_account_nav',
    'account_view_nav',
    'check_wether_account_is_none',
    'check_wether_account_is_not_none'
] + ALL_PERMISSIONS_IMPORTS
# <---- Simplify * Imports -----------------------------------------------------------------------


# ----- Setup The Flask application ------------------------------------------------------------->
# First we instantiate the application object
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)  # Fix proxied environment variables

# I18N & L10N support
babel = Babel(app)

# Cache support
cache = Cache(app)

# Navigation Menu's Support
menus = MenuBuilder(app)


@configuration_loaded.connect
def on_configuration_loaded(config):
    app.config.update(config)

    # Setup out database support
    from saltci.database import db
    db.init_app(app)
    # Let's check for upgrades
    db.upgrade_database_required()

    if app.debug:
        # LessCSS Support
        from flask.ext.sass import Sass
        sass = Sass(app)

        from werkzeug.debug import DebuggedApplication
        app.wsgi_app = DebuggedApplication(app.wsgi_app, True)

    # Application is configured, signal it
    application_configured.send(app)
# <---- Setup The Flask application --------------------------------------------------------------


# ----- Setup The Web-Application Navigation ---------------------------------------------------->
def check_wether_account_is_none(menu_item):
    return g.identity.account is None


def check_wether_account_is_not_none(menu_item):
    return g.identity.account is not None


top_account_nav = menus.add_menu("top_account_nav", classes="dropdown-menu")
account_view_nav = menus.add_menu("account_view_nav", classes="nav nav-tabs")

menus.add_menu_entry(
    "top_account_nav", _("Sign-Out"), 'account.signout', priority=100,
    visiblewhen=check_wether_account_is_not_none
)
# <---- Setup The Web-Application Navigation -----------------------------------------------------


# ----- Some Useful Helpers --------------------------------------------------------------------->
def redirect_to(*args, **kwargs):
    code = kwargs.pop('code', 302)
    return redirect(url_for(*args, **kwargs), code=code)


def redirect_back(*args, **kwargs):
    """
    Redirect back to the page we are coming from or the URL rule given.
    """
    code = kwargs.pop('code', 302)
    target = get_redirect_target(kwargs.pop('invalid_targets', ()))
    if target is None:
        target = url_for(*args, **kwargs)
    return redirect(target, code=code)


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def get_redirect_target(invalid_targets=()):
    check_target = (request.values.get('_redirect_target') or
                    request.args.get('next') or
                    session.get('_redirect_target', None) or
                    request.environ.get('HTTP_REFERER'))

    # if there is no information in either the form data
    # or the wsgi environment about a jump target we have
    # to use the target url
    if not check_target:
        return

    # otherwise drop the leading slash
    app_url = url_for('main.index', _external=True)
    url_parts = urlparse(app_url)
    check_parts = urlparse(urljoin(app_url, check_target))

    # if the jump target is on a different server we probably have
    # a security problem and better try to use the target url.
    if url_parts[:2] != check_parts[:2]:
        return

    # if the jump url is the same url as the current url we've had
    # a bad redirect before and use the target url to not create a
    # infinite redirect.
    current_parts = urlparse(urljoin(app_url, request.path))
    if check_parts[:5] == current_parts[:5]:
        return

    # if the `check_target` is one of the invalid targets we also fall back.
    if not isinstance(invalid_targets, (tuple, list)):
        invalid_targets = [invalid_targets]
    for invalid in invalid_targets:
        if check_parts[:5] == urlparse(urljoin(app_url, invalid))[:5]:
            return

    if is_safe_url(check_target):
        return check_target
# <---- Some Useful Helpers ----------------------------------------------------------------------


# ----- Setup Application Views ----------------------------------------------------------------->
from .views.main import main
from .views.account import account
from .views.hooks import hooks

app.register_blueprint(main)
app.register_blueprint(account)
app.register_blueprint(hooks)
# <---- Setup Application Views ------------------------------------------------------------------


# ----- Setup Request Decorators ---------------------------------------------------------------->
@request_started.connect_via(app)
def on_request_started(app):
    if request.path.startswith(app.static_url_path):
        # Nothing else needs to be done here, it's a static URL
        return

    redirect_target = get_redirect_target(session.pop('_redirect_target', ()))
    if redirect_target is not None:
        session['_redirect_target'] = redirect_target

    print 123, session


@request_finished.connect_via(app)
def on_request_finished(app, response):

    if request.path.startswith(app.static_url_path):
        return

    if response.status_code == 404:
        session.pop('not_found', None)
        app.save_session(session, response)
# <---- Setup Request Decorators -----------------------------------------------------------------


# ----- Error Handlers -------------------------------------------------------------------------->
@app.errorhandler(401)
def on_401(error):
    flash(_('You have not signed in yet.'), 'error')
    return redirect_to('account.signin', code=307)


@app.errorhandler(403)
def on_403(error):
    flash(_('You don\'t have the required permissions.'), 'error')
    return redirect_to('main.index', code=307)


@app.errorhandler(404)
def on_404(error):
    if request.endpoint and 'static' not in request.endpoint:
        session['not_found'] = True
    return render_template('404.html'), 404

@app.errorhandler(500)
def on_500(error):
    from pprint import pprint
    from StringIO import StringIO
    from .permissions import admin_permission

    user = 'anonymous'

    identity = getattr(g, 'identity', None)

    if identity:
        account = getattr(identity, 'account', None)
        if account:
            user = account.gh_login

    summary=str(error)
    longtext=''.join(format_exception(*sys.exc_info()))
    request_details = StringIO()
    pprint(request.__dict__, request_details)
    request_details.seek(0)

    return render_template(
        '500.html', error=error, user=user, summary=summary,
        longtext=longtext, request_details=request_details.read()
    ), 500
# <---- Error Handlers ---------------------------------------------------------------------------


# ----- Setup Babel Selectors ------------------------------------------------------------------->
@babel.localeselector
def get_locale():
    if hasattr(g.identity, 'account') and g.identity.account is not None:
        # Return the user's preferred locale
        return g.identity.account.locale

    # otherwise try to guess the language from the user accept
    # header the browser transmits. The best match wins.

    # Which translations do we support?
    supported = set(['en'] + [str(l) for l in babel.list_translations()])
    return request.accept_languages.best_match(supported)


@babel.timezoneselector
def get_timezone():
    if not hasattr(g.identity, 'account') or  g.identity.account is None:
        # No user is logged in, return the app's default timezone
        return app.config.get('BABEL_DEFAULT_LOCALE', 'UTC')
    # Return the user's preferred timezone
    return g.identity.account.timezone
# <---- Setup Babel Selectors --------------------------------------------------------------------


# ----- Custom Jinja Template Filters ----------------------------------------------------------->
@app.template_filter('formatseconds')
def seconds_format_filter(seconds):
    if 0 < seconds < 1:
        return '{0:.3f}ms'.format(seconds * 1000.0)
    else:
        return '{0:.3f}s'.format(seconds * 1.0)


@application_configured.connect
def define_highlight(app):
    if app.config.get('DEBUG', False) or app.config.get('SQLALCHEMY_RECORD_QUERIES', False):
        try:
            # This is from the snipped found at http://pastebin.com/7jS9BeAH
            from pygments import highlight
            from pygments.lexers import get_lexer_by_name
            from pygments.formatters import HtmlFormatter

            @app.template_filter('sql_highlight')
            def code_highlight(code):
                lexer = get_lexer_by_name('sql', stripall=False)
                formatter = HtmlFormatter(
                    linenos=False, style='tango', noclasses=True, nobackground=True, nowrap=True
                )
                return Markup(highlight(code, lexer, formatter))
        except ImportError:
            @app.template_filter('sql_highlight')
            def code_highlight(code):
                return Markup(code)
# <---- Custom Jinja Template Filters ------------------------------------------------------------


# ----- Jinja Context Injectors ----------------------------------------------------------------->
@app.context_processor
def inject_in_context():
    return dict(
        get_debug_queries = get_debug_queries,
        account_is_admin = g.identity.can(admin_permission)
    )
# <---- Jinja Context Injectors ------------------------------------------------------------------
