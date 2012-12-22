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
    Flask, flash, g, redirect, url_for, request, session, Markup, abort, Blueprint, json,
    render_template
)
from werkzeug.contrib.fixers import ProxyFix
from saltci.web.signals import configuration_loaded


# ----- Setup The Flask application ------------------------------------------------------------->
# First we instantiate the application object
app = Flask(__name__)


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

app.register_blueprint(main)
app.register_blueprint(account)
# <---- Setup Application Views ------------------------------------------------------------------


# ----- Setup Request Decorators ---------------------------------------------------------------->
@app.before_request
def before_request():
    from saltci.database import models
    g.account = None
    if 'ght' in session:
        g.account = models.Account.query.from_github_token(session['ght'])
# <---- Setup Request Decorators -----------------------------------------------------------------

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
    'render_template',
]
# <---- Simplify * Imports -----------------------------------------------------------------------
