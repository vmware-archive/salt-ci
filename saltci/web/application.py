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
    Flask, flash, g, redirect, url_for, request, session, Markup, abort, Blueprint, render_template
)
from werkzeug.contrib.fixers import ProxyFix

# ----- Setup The Flask application ------------------------------------------------------------->
# First we instantiate the application object
app = Flask(__name__)

if app.debug:
    # LessCSS Support
    from flask.ext.sass import Sass
    sass = Sass(app)

    from werkzeug.debug import DebuggedApplication
    app.wsgi_app = DebuggedApplication(app.wsgi_app, True)
# <---- Setup The Flask application --------------------------------------------------------------
