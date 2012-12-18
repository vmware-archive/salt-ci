# -*- coding: utf-8 -*-
'''
    Salt Continuous Integration
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~


    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

__version_info__    = (0, 6)
__version__         = '.'.join(map(str, __version_info__))
__package_name__    = 'Salt-CI'
__summary__         = 'Salt Continuous Integration'
__author__          = 'Pedro Algarvio'
__email__           = 'pedro@algarvio.me'
__license__         = 'Apache 2.0'
__url__             = 'https://github.com/saltstack/salt-ci'
__description__     = __doc__


def __get_version_info_from_git():
    '''
    If we have salt and the git binary available, use that version instead
    '''
    try:
        from salt.utils import which
    except ImportError:
        # We don't have salt.utils available, we can leave the function now
        return

    git = which('git')
    if not git:
        # We don't have the git binary available, we can leave the function now
        return

    import os
    import sys
    import subprocess

    process = subprocess.Popen(
        [git, 'describe'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
        cwd=os.path.abspath(os.path.dirname(__file__))
    )
    out, _ = process.communicate()
    if out:
        parsed_version = '{0}'.format(out.strip().lstrip('v'))
        parsed_version_info = tuple(
            [int(i) for i in parsed_version.split('-', 1)[0].split('.')]
        )
        if parsed_version_info != __version_info__:
            from salt import log
            msg = (
                'In order to get the proper {0} version with the git hash you need '
                'to update the package\'s local git tags. Something like: \'git fetch --tags\' '
                'or \'git fetch --tags upstream\' if you followed salt\'s contribute '
                'documentation. The version string WILL NOT include the git hash.'.format(
                    __package_name__
                )
            )
            if log.is_console_configured():
                import logging
                logging.getLogger(__name__).warning(msg)
            else:
                sys.stderr.write('WARNING: {0}\n'.format(msg))
        else:
            __version__ = parsed_version
            __version_info__ = parsed_version_info

__get_version_info_from_git()
del __get_version_info_from_git
