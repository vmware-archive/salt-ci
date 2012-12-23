# -*- coding: utf-8 -*-
'''
    saltci.web.application
    ~~~~~~~~~~~~~~~~~~~~~~

    Flask Application

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

from flask import (
    Flask, flash, g, redirect, url_for, request, session, Markup, abort, Blueprint, json, jsonify,
    render_template
)
from flask.ext.babel import Babel, gettext as _
from werkzeug.contrib.fixers import ProxyFix
from saltci.web.signals import configuration_loaded


# ----- Simplify * Imports ---------------------------------------------------------------------->
__all__ = [
    'app',
    'flash',
    'g',
    'redirect',
    'url_for',
    'request',
    'session',
    'Markup',
    'abort',
    'Blueprint',
    'json',
    'jsonify',
    'render_template',
    '_',
]
# <---- Simplify * Imports -----------------------------------------------------------------------


# ----- Setup The Flask application ------------------------------------------------------------->
# First we instantiate the application object
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)  # Fix proxied environment variables

# I18N & L10N support
babel = Babel(app)


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
# <---- Setup The Flask application --------------------------------------------------------------


# ----- Setup Application Views ----------------------------------------------------------------->
from .views.main import main
from .views.account import account
from .views.hooks import hooks

app.register_blueprint(main)
app.register_blueprint(account)
app.register_blueprint(hooks)
# <---- Setup Application Views ------------------------------------------------------------------


# ----- Setup Request Decorators ---------------------------------------------------------------->
@app.before_request
def before_request():
    from saltci.database import models
    g.account = None
    if 'ght' in session:
        g.account = models.Account.query.from_github_token(session['ght'])
# <---- Setup Request Decorators -----------------------------------------------------------------


# ----- Setup Babel Selectors ------------------------------------------------------------------->
@babel.localeselector
def get_locale():
    if g.account is not None:
        # Return the user's preferred locale
        return g.account.locale

    # otherwise try to guess the language from the user accept
    # header the browser transmits. The best match wins.

    # Which translations do we support?
    supported = set(['en'] + [str(l) for l in babel.list_translations()])
    return request.accept_languages.best_match(supported)


@babel.timezoneselector
def get_timezone():
    if g.account is None:
        # No user is logged in, return the app's default timezone
        return app.config.get('BABEL_DEFAULT_LOCALE', 'UTC')
    # Return the user's preferred timezone
    return g.account.timezone
# <---- Setup Babel Selectors --------------------------------------------------------------------
