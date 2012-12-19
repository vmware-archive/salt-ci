# -*- coding: utf-8 -*-
'''
    saltci.web.cli
    ~~~~~~~~~~~~~~

    Salt Continuous Integration shell bootstrap.

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

import os
import pwd
import logging
from salt.utils.verify import verify_env
from saltci.utils.parsers import SaltCIWebParser
from saltci.web.signals import configuration_loaded


class SaltCIWeb(SaltCIWebParser):
    def run(self):
        self.parse_args()

        # ----- Setup some logging defaults for external python libraries ----------------------->
        logging.getLogger('sqlalchemy').setLevel(logging.INFO)
        logging.getLogger('migrate').setLevel(logging.INFO)
        logging.getLogger('flaskext').setLevel(logging.INFO)
        logging.getLogger('flask.ext').setLevel(logging.INFO)
        logging.getLogger('flask').setLevel(logging.INFO)
        # <---- Setup some logging defaults for external python libraries ------------------------

        verify_dirs = []
        if self.config.get('log_file'):
            verify_dirs.append(
                os.path.dirname(self.config.get('log_file'))
            )

        if verify_dirs and self.config.get('verify_env', True):
            verify_env(
                verify_dirs,
                self.config.get('user', pwd.getpwuid(os.getuid()).pw_name)
            )

        self.setup_logfile_logger()

        from saltci.web.application import app
        configuration_loaded.send(self.config)

        try:
            app.run(
                self.config.get('serve_host'),
                self.config.get('serve_port'),
                debug=app.config.get('DEBUG', False)
            )
        except KeyboardInterrupt:
            sys.exit(0)
