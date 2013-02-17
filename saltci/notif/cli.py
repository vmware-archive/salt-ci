# -*- coding: utf-8 -*-
'''
    saltci.notif.cli
    ~~~~~~~~~~~~~~~~

    Salt-CI notifications salt minion.

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2013 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

from salt import Minion
from saltci import config


class SaltCINotif(Minion):

    # ConfigDirMixIn
    def setup_config(self):
        return config.saltci_notif_config(self.get_config_file_path('salt-ci-notif'))

    def prepare(self):
        super(SaltCINotif, self).prepare()

    def start(self):
        super(SaltCINotif, self).start()

    def shutdown(self):
        super(SaltCINotif, self).shutdown()
