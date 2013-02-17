# -*- coding: utf-8 -*-
'''
    saltci.master.cli
    ~~~~~~~~~~~~~~~~~

    Salt-CI salt master.

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2013 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

from salt import Master, Minion
from saltci import config


class SaltCIMaster(Master):

    # ConfigDirMixIn
    def setup_config(self):
        return config.saltci_master_config(self.get_config_file_path('salt-ci-master'))

    def prepare(self):
        super(SaltCIMaster, self).prepare()

    def start(self):
        super(SaltCIMaster, self).start()

    def shutdown(self):
        super(SaltCIMaster, self).shutdown()
