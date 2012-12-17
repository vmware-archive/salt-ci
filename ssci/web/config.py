# -*- coding: utf-8 -*-
'''
    ssci.web.config
    ~~~~~~~~~~~~~~~

    SaltStack-CI Web Configuration Handling.

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

from salt import config as saltconfig

def ssci_web_config(path):
    opts = dict(
        # ----- Regular Settings ---------------------------------------------------------------->
        serve_host='localhost',
        serve_port=5123,
        log_file='/var/log/salt/ssci-web',
        log_level=None,
        log_level_logfile=None,
        log_datefmt=saltconfig._dflt_log_datefmt,
        log_fmt_console=saltconfig._dflt_log_fmt_console,
        log_fmt_logfile=saltconfig._dflt_log_fmt_logfile,
        log_granular_levels={},
        pidfile='/var/run/ssci-web.pid',
        default_include='ci-web.d/*.conf',
        # <---- Regular Settings -----------------------------------------------------------------

        # ----- Flask Related Settings ---------------------------------------------------------->
        # All uppercased settings will be made available on the Flask's configuration object

        # ----- Flask Application Settings ------------------------------------------------------>
        DEBUG=False,
        TESTING=False,
        SECRET_KEY='not_so_secret_and_should_be_changed',   # HINT: import os; os.urandom(24)
        PERMANENT_SESSION_LIFETIME=timedelta(days=30),
        LOGGER_NAME='ssci.web.server',
        # <---- Flask Application Settings -------------------------------------------------------

        # ----- Flask SQLAlchemy Settings ------------------------------------------------------->
        SQLALCHEMY_DATABASE_URI=None,
        SQLALCHEMY_RECORD_QUERIES=False,
        SQLALCHEMY_NATIVE_UNICODE=True,
        SQLALCHEMY_POOL_SIZE=None,
        SQLALCHEMY_POOL_TIMEOUT=None,
        SQLALCHEMY_POOL_RECYCLE=None,
        # <---- Flask SQLAlchemy Settings --------------------------------------------------------

        # <---- Flask Related Settings -----------------------------------------------------------
    )
    saltconfig.load_config(opts, path, 'SSCI_WEB_CONFIG')
    default_include = opts.get('default_include', [])
    include = opts.get('include', [])

    opts = saltconfig.include_config(default_include, opts, path, verbose=False)
    opts = saltconfig.include_config(include, opts, path, verbose=True)
    return opts
