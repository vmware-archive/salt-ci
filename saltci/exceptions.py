# -*- coding: utf-8 -*-
'''
    saltci.exceptions
    ~~~~~~~~~~~~~~~~~

    Salt-CI exceptions

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2013 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''


class SaltCIException(BaseException):
    '''
    Salt-CI base exception. Please subclass this exception if you want to raise some custom
    exceptions within Salt-CI.
    '''


class SaltCIStartupException(SaltCIException):
    '''
    This exception is raised to let the user that something is wrong and Salt-CI could not start
    '''
