# -*- coding: utf-8 -*-
'''
    saltci.scripts
    ~~~~~~~~~~~~~~

    This module contains the function calls to execute command line scripts.

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''


def run_saltstack_ci_web():
    from saltci.web.cli import SaltCIWeb
    saltciweb = SaltCIWeb()
    saltciweb.run()
