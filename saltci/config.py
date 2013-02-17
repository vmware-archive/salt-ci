# -*- coding: utf-8 -*-
'''
    saltci.config
    ~~~~~~~~~~~~~

    Salt-CI Configuration Handling.

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2013 by the SaltStack Team, see AUTHORS for more details.
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


def saltci_master_config(path):
    '''
    Load `salt-ci-master` configuration from the provided path.
    '''
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
        log_file='/var/log/salt/salt-ci-master',
        pidfile='/var/run/salt-ci-master.pid',
        # <---- Primary Configuration Settings ---------------------------------------------------
    )
    # Return final and parsed options
    return saltconfig.master_config(path, 'SALT_CI_MASTER_CONFIG', opts)


def saltci_notif_config(path, check_dns=True, env_var='SALT_CI_NOTIF_CONFIG'):
    '''
    Load `salt-ci-notif` configuration from the provided path.
    '''
    # Get salt's minion default options
    defaults = saltconfig.DEFAULT_MINION_OPTS.copy()
    # override with our own defaults
    defaults.update(_COMMON_CONFIG.copy())
    # Tweak our defaults
    defaults.update(
        # ----- Primary Configuration Settings -------------------------------------------------->
        root_dir='/',
        verify_env=True,
        default_include='salt-ci-notif.d/*.conf',
        log_file='/var/log/salt/salt-ci-notif',
        pidfile='/var/run/salt-ci-notif.pid',
        # <---- Primary Configuration Settings ---------------------------------------------------

        # ----- Include salt-ci-notif modules  -------------------------------------------------->
        module_dirs=saltconfig.DEFAULT_MINION_OPTS['module_dirs'] + [
            os.path.join(os.path.dirname(__file__), 'notif', 'modules')
        ],
        # <---- Include salt-ci-notif modules  ---------------------------------------------------

        # ----- Sendmail Settings --------------------------------------------------------------->
        sendmail=dict(
            smtp_server=None,
            smtp_username=None,
            smtp_password=None,
            smtp_port=25,
            use_ssl=False,
            use_tls=False,
            sender=None,
            reply_to=None
        )
        # <---- Sendmail Settings ----------------------------------------------------------------
    )
    return saltconfig.minion_config(path, check_dns=check_dns, env_var=env_var, defaults=defaults)
