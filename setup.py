#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 ft=python cc=100 tw=99 et
'''
    setup.py
    ~~~~~~~~

    SaltStack Continuous Integration Package Setup

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2012 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

import os
import subprocess
from setuptools import setup
from distutils import log
from distutils.command import clean, build
from distutils.extension import Extension

import ssci as package


REQUIREMENTS = ['Distribute']
with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as f:
    REQUIREMENTS.extend(
        [line for line in f.read().split('\n') if line]
    )


class CustomBuild(build.build):
    user_options = build.build.user_options + [
        ('sass=', None, "Path to the sass binary")
    ]

    def initialize_options(self):
        build.build.initialize_options(self)
        self.sass = None

    def finalize_options(self):
        build.build.finalize_options(self)
        if self.sass is not None:
            self.sass = os.path.abspath(os.path.expanduser(self.sass))

    def run(self):
        build.build.run(self)
        # Compile SASS files
        static_path = os.path.join(os.path.dirname(package.__file__), 'web', 'static')
        for (dirpath, dirnames, filenames) in os.walk(static_path):
            for filename in filenames:
                if not filename.endswith('.scss'):
                    continue
                scss = os.path.join(static_path, dirpath, filename)
                css = scss.replace('.scss', '.css')
                log.info("Converting from %s to %s" % (scss, css))
                subprocess.check_output([self.sass, '--unix-newlines', scss, css])


setup(name=package.__package_name__,
      version=package.__version__,
      author=package.__author__,
      author_email=package.__email__,
      url=package.__url__,
      description=package.__summary__,
      long_description=package.__description__,
      license=package.__license__,
      platforms="Linux",
      keywords="SaltStack Continuous Integration",
      packages=['ssci'],
      package_data={
          'ssci.': [
              '**.css',
              '**.js',
              '**.png',
              '**.cfg',
              'web/translations/*/LC_MESSAGES/sass.mo'
          ]
      },
      install_requires=REQUIREMENTS,
      cmdclass={
          'build': CustomBuild
      },
      message_extractors={
          'ssci.web': [
              ('**.py', 'python', None),
              ('**.pyx', 'python', None),
              ('templates/**.html', 'jinja2', None),
              ('templates/**.txt', 'jinja2', None)
          ],
      },
      entry_points="""
      [console_scripts]
      saltstack-ci-web = ssci.scripts:run_saltstack_ci_web

      [distutils.commands]
      compile = babel.messages.frontend:compile_catalog
      extract = babel.messages.frontend:extract_messages
         init = babel.messages.frontend:init_catalog
       update = babel.messages.frontend:update_catalog

      """,
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Web Environment',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: Apache 2.0 License',
          'Operating System :: Linux',
          'Programming Language :: Python',
          'Topic :: Utilities',
      ]
)
