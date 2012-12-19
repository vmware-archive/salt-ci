# -*- coding: utf-8 -*-
'''
    saltci.web.signals
    ~~~~~~~~~~~~~~~~~~

    Signal handling

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

from blinker import Namespace


signal = Namespace().signal

configuration_loaded = signal(
    'configuration-loaded',
    'Emitted once the configuration has been loaded.'
)
