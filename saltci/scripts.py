# -*- coding: utf-8 -*-
'''
    saltci.scripts
    ~~~~~~~~~~~~~~

    This module contains the function calls to execute command line scripts.

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2013 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''


def run_salt_ci_master():
    from saltci.cli_adapt import SaltCIMaster
    saltcimaster = SaltCIMaster()
    saltcimaster.start()


def run_salt_ci_key():
    from saltci.cli_adapt import SaltCIKey
    saltcikey = SaltCIKey()
    saltcikey.run()


def run_salt_ci():
    from saltci.cli_adapt import SaltCICMD
    saltcicmd = SaltCICMD()
    saltcicmd.run()


def run_salt_ci_notif():
    from saltci.notif.cli import SaltCINotif
    saltcinotif = SaltCINotif()
    saltcinotif.start()


def run_salt_ci_notif_call():
    from saltci.notif.cli import SaltCINotifCall
    saltcinotifcall = SaltCINotifCall()
    saltcinotifcall.run()
