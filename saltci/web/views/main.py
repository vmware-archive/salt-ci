# -*- coding: utf-8 -*-
'''
    saltci.web.views.main
    ~~~~~~~~~~~~~~~~~~~~~

    Main view of Salt-CI

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

from saltci.web.application import *


# ----- Blueprint & Menu Entries ---------------------------------------------------------------->
main = Blueprint('main', __name__)
# <---- Blueprint & Menu Entries -----------------------------------------------------------------


# ----- Views ----------------------------------------------------------------------------------->
@main.route('/', methods=('GET',))
def index():
    return render_template('index.html')
# <---- Views ------------------------------------------------------------------------------------
