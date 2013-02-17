# -*- coding: utf-8 -*-
'''
    saltci.master.cli
    ~~~~~~~~~~~~~~~~~

    Salt-CI salt master.

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2013 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

# Import python libs
import os

# Import salt libs
from salt import Master
from salt.cli import SaltKey

# Import Salt-CI libs
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


class SaltCIKey(SaltKey):
    # ConfigDirMixIn
    def setup_config(self):
        keys_config = config.saltci_master_config(self.get_config_file_path('salt-ci-master'))
        if self.options.gen_keys:
            # Since we're generating the keys, some defaults can be assumed
            # or tweaked
            keys_config['key_logfile'] = os.devnull
            keys_config['pki_dir'] = self.options.gen_keys_dir
        return keys_config
