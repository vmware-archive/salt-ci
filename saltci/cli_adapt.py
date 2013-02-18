# -*- coding: utf-8 -*-
'''
    saltci.cli_adapt
    ~~~~~~~~~~~~~~~~

    Some needed salt shell binary adaptations.

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2013 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

# Import python libs
import os

# Import salt libs
from salt import Master
from salt.cli import SaltKey, SaltCMD


class SaltCIMaster(Master):

    # ConfigDirMixIn configuration filename attribute
    _config_filename_ = 'salt-ci-master'


class SaltCIKey(SaltKey):

    # ConfigDirMixIn configuration filename attribute
    _config_filename_ = 'salt-ci-master'


class SaltCICMD(SaltCMD):

    # ConfigDirMixIn configuration filename attribute
    _config_filename_ = 'salt-ci-master'
