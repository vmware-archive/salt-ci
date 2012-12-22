# -*- coding: utf-8 -*-
'''
    saltci.config
    ~~~~~~~~~~~~~

    Salt-CI Configuration Handling.

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

from salt import config as saltconfig

_COMMON_CONFIG = dict(
    # ----- Logging Configuration --------------------------------------------------------------->
    log_file=None,
    log_level=None,
    log_level_logfile=None,
    log_datefmt=saltconfig._dflt_log_datefmt,
    log_fmt_console=saltconfig._dflt_log_fmt_console,
    log_fmt_logfile=saltconfig._dflt_log_fmt_logfile,
    log_granular_levels={}
    # <---- Logging Configuration ----------------------------------------------------------------
)

_COMMON_DB_CONFIG = dict(
    # ----- Flask SQLAlchemy Settings ----------------------------------------------------------->
    SQLALCHEMY_DATABASE_URI=None,
    SQLALCHEMY_RECORD_QUERIES=False,
    SQLALCHEMY_NATIVE_UNICODE=True,
    SQLALCHEMY_POOL_SIZE=None,
    SQLALCHEMY_POOL_TIMEOUT=None,
    SQLALCHEMY_POOL_RECYCLE=None,
    # <---- Flask SQLAlchemy Settings ------------------------------------------------------------
)


def saltci_web_config(path):
    opts = _COMMON_CONFIG.copy()
    opts.update(_COMMON_DB_CONFIG.copy())
    opts.update(
        # ----- Primary Configuration Settings -------------------------------------------------->
        root_dir='/',
        verify_env=True,
        default_include='salt-ci-web.d/*.conf',
        # <---- Primary Configuration Settings ---------------------------------------------------

        # ----- Regular Settings ---------------------------------------------------------------->
        serve_host='localhost',
        serve_port=5123,
        log_file='/var/log/salt/salt-ci-web',
        #log_level=None,
        #log_level_logfile=None,
        #log_datefmt=saltconfig._dflt_log_datefmt,
        #log_fmt_console=saltconfig._dflt_log_fmt_console,
        #log_fmt_logfile=saltconfig._dflt_log_fmt_logfile,
        #log_granular_levels={},
        pidfile='/var/run/salt-ci-web.pid',
        # <---- Regular Settings -----------------------------------------------------------------

        # ----- Flask Related Settings ---------------------------------------------------------->
        # All uppercased settings will be made available on the Flask's configuration object

        # ----- Flask Application Settings ------------------------------------------------------>
        DEBUG=False,
        TESTING=False,
        SECRET_KEY='not_so_secret_and_should_be_changed',   # HINT: import os; os.urandom(24)
        PERMANENT_SESSION_LIFETIME=1600,
        LOGGER_NAME='saltci.web.server',
        # <---- Flask Application Settings -------------------------------------------------------

        # ----- GitHub Secrets ------------------------------------------------------------------>
        GITHUB_CLIENT_ID='',
        GITHUB_CLIENT_SECRET='',
        # <---- GitHub Secrets -------------------------------------------------------------------

        # <---- Flask Related Settings -----------------------------------------------------------
    )
    saltconfig.load_config(opts, path, 'SALT_CI_WEB_CONFIG')
    default_include = opts.get('default_include', [])
    include = opts.get('include', [])

    opts = saltconfig.include_config(default_include, opts, path, verbose=False)
    opts = saltconfig.include_config(include, opts, path, verbose=True)
    saltconfig.prepend_root_dir(opts, ['log_file'])
    return opts


def saltci_migrate_config(path):
    opts = _COMMON_CONFIG.copy()
    opts.update(_COMMON_DB_CONFIG.copy())
    opts.update(
        log_file='/var/log/salt/salt-ci-migrate'
    )
    saltconfig.load_config(opts, path, 'SALT_CI_MIGRATE_CONFIG')
    default_include = opts.get('default_include', [])
    include = opts.get('include', [])

    opts = saltconfig.include_config(default_include, opts, path, verbose=False)
    opts = saltconfig.include_config(include, opts, path, verbose=True)
    saltconfig.prepend_root_dir(opts, ['log_file'])
    return opts
