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


class SaltCINotif(Minion):

    # ConfigDirMixIn configuration filename attribute
    _config_filename_ = 'salt-ci-notif'


class SaltCINotifCall(SaltCall):
    # ConfigDirMixIn configuration filename attribute
    _config_filename_ = 'salt-ci-notif'
