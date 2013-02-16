# -*- coding: utf-8 -*-
'''
    saltci.config
    ~~~~~~~~~~~~~

    Salt-CI Configuration Handling.

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

import os
import urlparse
from salt import config as saltconfig

_COMMON_CONFIG = dict(
    # ----- Logging Configuration --------------------------------------------------------------->
    log_file=None,
    log_level=None,
    log_level_logfile=None,
    log_datefmt=saltconfig._DFLT_LOG_DATEFMT,
    log_fmt_console=saltconfig._DFLT_LOG_FMT_CONSOLE,
    log_fmt_logfile=saltconfig._DFLT_LOG_FMT_LOGFILE,
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


def filter_options(opts, keys):
    '''
    Remove the provided keys from the configuration dictionary.
    '''
    if not keys:
        return opts
    for key in keys:
        if key in opts:
            opts.pop(key)
    return opts


def saltci_web_config(path):
    defaults = _COMMON_CONFIG.copy()
    defaults.update(_COMMON_DB_CONFIG.copy())
    defaults.update(
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
        SALT_CLIENT_CONFIG=os.path.join(os.path.dirname(path), 'salt-ci-client'),

        # ----- Flask Application Settings ------------------------------------------------------>
        DEBUG=False,
        TESTING=False,
        SECRET_KEY='not_so_secret_and_should_be_changed',   # HINT: import os; os.urandom(24)
        PERMANENT_SESSION_LIFETIME=1600,
        LOGGER_NAME='saltci.web.server',
        # <---- Flask Application Settings -------------------------------------------------------

        # ----- Flask Babel(I18N & L10N) Settings ----------------------------------------------->
        BABEL_DEFAULT_LOCALE='en',
        BABEL_DEFAULT_TIMEZONE='UTC',
        # <---- Flask Babel(I18N & L10N) Settings ------------------------------------------------

        # ----- Flask Cache Settings ------------------------------------------------------------>
        # All settings, please check http://packages.python.org/Flask-Cache/
        CACHE_TYPE=None,
        # <---- Flask Cache Settings -------------------------------------------------------------

        # ----- GitHub Secrets ------------------------------------------------------------------>
        GITHUB_CLIENT_ID='',
        GITHUB_CLIENT_SECRET='',
        GITHUB_PAYLOAD_IPS=('207.97.227.253', '50.57.128.197', '108.171.174.178', '50.57.231.61'),
        # <---- GitHub Secrets -------------------------------------------------------------------

        # <---- Flask Related Settings -----------------------------------------------------------
    )

    overrides = saltconfig.load_config(path, 'SALT_CI_WEB_CONFIG')
    default_include = overrides.get('default_include', defaults['default_include'])
    include = overrides.get('include', [])

    overrides.update(saltconfig.include_config(default_include, path, verbose=False))
    overrides.update(saltconfig.include_config(include, path, verbose=True))

    return apply_ci_config(overrides, defaults)


def saltci_migrate_config(path):
    defaults = _COMMON_CONFIG.copy()
    defaults.update(_COMMON_DB_CONFIG.copy())
    defaults.update(
        log_file='/var/log/salt/salt-ci-migrate'
    )
    overrides = saltconfig.load_config(path, 'SALT_CI_MIGRATE_CONFIG')

    default_include = overrides.get('default_include', defaults['default_include'])
    include = overrides.get('include', [])

    overrides.update(saltconfig.include_config(default_include, path, verbose=False))
    overrides.update(saltconfig.include_config(include, path, verbose=True))

    return apply_ci_config(overrides, defaults)


def apply_ci_config(overrides, defaults):
    opts = defaults.copy()
    opts.update(overrides)
    prepend_root_dirs = []
    # These can be set to syslog, so, not actual paths on the system
    for config_key in ('log_file',):
        log_setting = opts.get(config_key, '')
        if log_setting is None:
            continue

        if urlparse.urlparse(log_setting).scheme == '':
            prepend_root_dirs.append(config_key)

    if prepend_root_dirs:
        saltconfig.prepend_root_dir(opts, prepend_root_dirs)
    return opts


def saltci_master_config(path):
    # Get salt's master default options
    opts = saltconfig.DEFAULT_MASTER_OPTS.copy()
    # override with our own defaults
    opts.update(_COMMON_CONFIG.copy())
    # Tweak our defaults
    opts.update(
        # ----- Primary Configuration Settings -------------------------------------------------->
        root_dir='/',
        verify_env=True,
        default_include='salt-ci-master.d/*.conf',
        # <---- Primary Configuration Settings ---------------------------------------------------

        # ----- Regular Settings ---------------------------------------------------------------->
        log_file='/var/log/salt/salt-ci-master',
        log_level=None,
        #log_level_logfile=None,
        #log_datefmt=saltconfig._dflt_log_datefmt,
        #log_fmt_console=saltconfig._dflt_log_fmt_console,
        #log_fmt_logfile=saltconfig._dflt_log_fmt_logfile,
        #log_granular_levels={},
        pidfile='/var/run/salt-ci-master.pid',
        # <---- Regular Settings -----------------------------------------------------------------
    )
    # Return final and parsed options
    return saltconfig.master_config(path, 'SALT_CI_MASTER_CONFIG', opts)


def salt_client_config(path):
    # Get salt's master default options
    opts = saltconfig.DEFAULT_MASTER_OPTS.copy()
    # override with our own defaults
    opts.update(_COMMON_CONFIG.copy())
    # Tweak our defaults
    opts.update(
        # ----- Primary Configuration Settings -------------------------------------------------->
        root_dir='/',
        verify_env=True,
        default_include='salt-ci-client.d/*.conf',
        # <---- Primary Configuration Settings ---------------------------------------------------

        # ----- Access Token Path --------------------------------------------------------------->
        token_file='.salt-token',
        # <---- Access Token Path ----------------------------------------------------------------

        # ----- Regular Settings ---------------------------------------------------------------->
        log_file='/var/log/salt/salt-ci-client',
        log_level=None,
        #log_level_logfile=None,
        #log_datefmt=saltconfig._dflt_log_datefmt,
        #log_fmt_console=saltconfig._dflt_log_fmt_console,
        #log_fmt_logfile=saltconfig._dflt_log_fmt_logfile,
        #log_granular_levels={},
        pidfile='/var/run/salt-ci-client.pid',
        # <---- Regular Settings -----------------------------------------------------------------
    )
    # Return final and parsed options
    opts = saltconfig.client_config(path, 'SALT_CI_CLIENT_CONFIG', opts)
    # Prepend root directory
    saltconfig.prepend_root_dir(opts, ['token_file'])
    return opts
