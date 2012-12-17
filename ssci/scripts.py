# -*- coding: utf-8 -*-
'''
    ssci.scripts
    ~~~~~~~~~~~~

    This module contains the function calls to execute command line scripts.

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''


def run_saltstack_ci_web():
    from ssci.web.cli import SaltStackCIWeb
    ssciweb = SaltStackCIWeb()
    ssciweb.run()
