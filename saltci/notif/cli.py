# -*- coding: utf-8 -*-
'''
    saltci.notif.cli
    ~~~~~~~~~~~~~~~~

    Salt-CI notifications salt minion.

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2013 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

# Import salt libs
from salt import Minion
from salt.cli import SaltCall

# Import salt-ci libs
from saltci import config



class SaltCINotif(Minion):

    # ConfigDirMixIn configuration filename attribute
    _config_filename_ = 'salt-ci-notif'

    def setup_config(self):
        return config.saltci_notif_config(self.get_config_file_path())


class SaltCINotifCall(SaltCall):
    # ConfigDirMixIn configuration filename attribute
    _config_filename_ = 'salt-ci-notif'

    def setup_config(self):
        return config.saltci_notif_config(self.get_config_file_path())
