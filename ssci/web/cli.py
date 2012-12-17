# -*- coding: utf-8 -*-
'''
    ssci.web.cli
    ~~~~~~~~~~~~

    SaltStack Continuous Integration shell bootstrap.

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

from ssci.utils.parsers import SaltStackCIWebParser


class SaltStackCIWeb(SaltStackCIWebParser):
    def run(self):
        self.parse_args()

def run_saltstack_ci_web():
    parser = SaltStackCIWeb()

