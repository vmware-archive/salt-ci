# -*- coding: utf-8 -*-
'''
    saltci.utils.parsers
    ~~~~~~~~~~~~~~~~~~~~

    Salt-CI console parsers.

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

import optparse
from saltci.web.config import saltci_web_config
from salt.utils import parsers as saltparsers


class SaltCIWebParser(saltparsers.OptionParser,
                      saltparsers.ConfigDirMixIn,
                      saltparsers.LogLevelMixIn,
                      saltparsers.PidfileMixin,
                      saltparsers.DaemonMixIn,
                      saltparsers.RunUserMixin):
    __metaclass__ = saltparsers.OptionParserMeta

    # ConfigDirMixIn methods
    def setup_config(self):
        return saltci_web_config(self.get_config_file_path('salt-ci-web'))

    def _mixin_setup(self):
        self.serve_options_group = optparse.OptionGroup(
            self, "WebServer Options"
        )
        self.serve_options_group.add_option(
            '-H', '--serve-host',
            default='localhost',
            help='Webserver serving hostname'
        )
        self.serve_options_group.add_option(
            '-P', '--serve-port',
            type='int',
            default=5123,
            help='Webserver serving port'
        )
        self.add_option_group(self.serve_options_group)

