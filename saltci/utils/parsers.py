# -*- coding: utf-8 -*-
'''
    saltci.utils.parsers
    ~~~~~~~~~~~~~~~~~~~~

    Salt-CI console parsers.

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

import os
import optparse
from salt.utils import parsers as saltparsers
from saltci import config


class SaltCIWebParser(saltparsers.OptionParser,
                      saltparsers.ConfigDirMixIn,
                      saltparsers.LogLevelMixIn,
                      saltparsers.PidfileMixin,
                      saltparsers.DaemonMixIn,
                      saltparsers.RunUserMixin):
    __metaclass__ = saltparsers.OptionParserMeta

    epilog = None

    # ConfigDirMixIn methods
    def setup_config(self):
        return config.saltci_web_config(self.get_config_file_path('salt-ci-web'))

    def _mixin_setup(self):
        self.shell_options_group = optparse.OptionGroup(
            self, 'Interactive Shell'
        )
        self.shell_options_group.add_option(
            '-S', '--shell',
            default=False,
            action='store_true',
            help='Run web application in an interactive shell'
        )
        self.add_option_group(self.shell_options_group)

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


class SaltCIMigrateParser(saltparsers.OptionParser,
                          saltparsers.ConfigDirMixIn,
                          saltparsers.LogLevelMixIn):
    __metaclass__ = saltparsers.OptionParserMeta

    usage = "%prog [options] <migrate-command>"
    epilog = None
    migrate_command = None
    migrate_args = None

    # OptionParser Override to add additional help method
    def _add_help_option(self):
        super(SaltCIMigrateParser, self)._add_help_option()
        self.add_option(
            '--help-migrate',
            default=False,
            action='store_true',
            help='Show available migrate commands'
        )

    # ConfigDirMixIn methods
    def setup_config(self):
        migrate_config_file = self.get_config_file_path('salt-ci-migrate')
        if not os.path.exists(migrate_config_file):
            web_config_file = self.get_config_file_path('salt-ci-web')
            if os.path.exists(web_config_file):
                migrate_config_file = web_config_file
        return config.saltci_migrate_config(migrate_config_file)

    def _mixin_after_parsed(self):
        if self.args and self.args[0] not in ('downgrade', 'upgrade', 'script'):
            self.error('Migrate command {0} not know/supported.'.format(self.args[0]))

        self.migrate_command = self.args.pop(0)
        if self.migrate_command in ('upgrade', 'downgrade') and self.args:
            self.migrate_args = self.args.pop(0)
            try:
                self.migrate_args = int(self.migrate_args)
            except ValueError:
                self.error('{0} is not a valid migration version.'.format(self.migrate_args))
        elif self.migrate_command == 'script':
            if not self.args:
                self.error('You need to pass a migrate script description')
            self.migrate_args = ' '.join(self.args)
            self.args = None

        if self.args:
            # If there are still arguments, it's an error
            self.error(
                'Too many arguments. Arguments not recognized: {0}'.format(
                    ', '.join(self.args)
                )
            )


class SaltCIMaster(saltparsers.MasterOptionParser):
    # ConfigDirMixIn methods
    def setup_config(self):
        return config.saltci_web_config(self.get_config_file_path('salt-ci-master'))


class SaltWebMinionParser(saltparsers.MinionOptionParser):
    pass
