# -*- coding: utf-8 -*-
'''
    ssci.utils.parsers
    ~~~~~~~~~~~~~~~~~~

    SaltStack-CI console parsers.

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

from ssci.web.config import ssci_web_config
from salt.utils import parsers as saltparsers


class SaltStackCIWebParser(saltparsers.OptionParser,
                           saltparsers.ConfigDirMixIn,
                           saltparsers.LogLevelMixIn,
                           saltparsers.PidfileMixin,
                           saltparsers.DaemonMixIn):
    __metaclass__ = saltparsers.OptionParserMeta

    # ConfigDirMixIn methods
    def setup_config(self):
        return ssci_web_config(self.get_config_file_path('ci-web'))
