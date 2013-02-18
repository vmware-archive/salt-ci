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

# Import salt-ci libs
from saltci import config


class SaltCIMaster(Master):

    # ConfigDirMixIn configuration filename attribute
    _config_filename_ = 'salt-ci-master'

    def setup_config(self):
        return config.saltci_master_config(self.get_config_file_path())


class SaltCIKey(SaltKey):

    # ConfigDirMixIn configuration filename attribute
    _config_filename_ = 'salt-ci-master'

    def setup_config(self):
        return config.saltci_master_config(self.get_config_file_path())


class SaltCICMD(SaltCMD):

    # ConfigDirMixIn configuration filename attribute
    _config_filename_ = 'salt-ci-master'

    def setup_config(self):
        return config.saltci_master_config(self.get_config_file_path())
