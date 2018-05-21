# setup.py

#from distutils.core import setup

"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""
from setuptools import setup, find_packages
from setuptools.command.install import install
from os import path
from ConfigParser import ConfigParser
import uuid
import socket
import subprocess

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.txt')) as f:
      long_description = f.read()

class AMONInstall(install):
      def run(self):
            cp = ConfigParser()
            cp.add_section("database")
            cp.add_section("dirs")
            cp.add_section("machine")
            cp.add_section("mailing_list")
            cp.add_section("rabbitmq")
            # users can change these
            cp.set("database", "archive_dbname", "AMON_test1")#str(uuid.uuid5(uuid.NAMESPACE_URL ,"%s://%s/archive" % (socket.gethostname(), self.prefix))))
            cp.set("database", "realtime_dbname", "AMON_test2")#str(uuid.uuid5(uuid.NAMESPACE_URL ,"%s://%s/realtime" % (socket.gethostname(), self.prefix))))
            cp.set("database", "host_name", "localhost")
            cp.set("database", "username", "root")
            cp.set("database", "password", "apasswordword")
            #cp.set("dirs", "alertdir", "%s/amon_alerts" % self.prefix)
            cp.set("dirs", "alertdir", "/path/to/amon_alerts")
            cp.set("dirs", "amonpydir","/path/to/amonpy")
            cp.set("dirs", "serverdir","/path/to/server")
            cp.set("machine", "prod", False)
            cp.set("mailing_list", "sub_cut_ehe_hese", "fixme@notreal.org")
            cp.set("mailing_list", "sub_ehe_hese", "fixme@notreal.org")
            cp.set("mailing_list", "ehe_hese", "fixme@notreal.org")
            cp.set("rabbitmq","name","a_name")
            cp.set("rabbitmq","password","a_passwd")
            cp.set("rabbitmq","vhost","test")

            if raw_input("Do you wish to setup the amon server configuration? (Y/N): ").upper() == "Y":
                  for section in cp.sections():
                        for k,v in cp.items(section):
                              answer = raw_input("%s : %s = [%s]" % (section, k, v)).strip()
                              if answer != "":
                                    cp.set(section, k, answer)
            if raw_input("Do you wish to setup the database? (Y/N): ").upper() == "Y":
                  print "root login for the mysql server..."
                  u,h,p = cp.get("database", "username"), cp.get("database", "host_name"), cp.get("database", "password")
                  d1, d2 = cp.get("database", "archive_dbname"), cp.get("database", "realtime_dbname")
                  # Create the dbs
                  subprocess.check_call(["mysql", "-u", "root", "-p", "-h", h, "-e", "CREATE DATABASE `%s`; CREATE DATABASE `%s`" %(d1, d2)])
                  # Make a user and give them permissions
                  subprocess.check_call(["mysql", "-u", "root", "-p", "-h", h, "-e", "use mysql; CREATE USER IF NOT EXISTS '%s'@'%s' IDENTIFIED BY '%s'; GRANT ALL PRIVILEGES ON `%s` . * TO '%s'@'%s'; GRANT ALL PRIVILEGES ON `%s` . * TO '%s'@'%s';" % (u,h,p,d1,u,h,d2,u,h) ])
            # these are tied to the code install
            #cp.set("dirs", "amonpydir", "fixme")
            with open("amonpy/amon.ini", "w") as f:
                  cp.write(f)
            install.run(self)

setup(name = "AmonPy",
      version = "1.4.0",
      description='AMON Analysis Code',
      long_description=long_description,
      author='Miles Smith, Gordana Tesic',
      author_email='mus44@psu.edu, gut10@psu.edu',

      license='FIXME',
      cmdclass = {'install': AMONInstall},
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=['Development Status :: 3 - Alpha',
                   'Intended Audience :: Science/Research',
                   'Natural Language :: English',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python :: 2.7',
                   'Topic :: Scientific/Engineering :: Astronomy',
                   'Topic :: Scientific/Engineering :: Physics',
                   'License :: Other/Proprietary License',
                   'Framework :: Twisted'
                  ],
      #packages = find_packages(exclude=['test','detector-specific','dev'],include=['twisted']),
      packages = ['amonpy',
                   'amonpy/anal',
                   'amonpy/analyses',
                   'amonpy/dbase',
                   'amonpy/sim',
                   'amonpy/tools',
                   'amonpy/ops',
                   'amonpy/ops/analyser',
                   'amonpy/ops/network/',
                   'amonpy/ops/server/',
                   'twisted'
                  ],
      scripts = ['amonpy/ops/run_archival.py',
                 'amonpy/ops/run_basic_sim.py',
                 'bin/amon_test_db_write',
                 'bin/amon_create_db'
                ],
      package_data = {'twisted': ['plugins/amon_server_plugin.py',
                                  'plugins/amon_client_post_plugin.py',
                                  'plugins/amon_client_post_ssl_plugin.py'
                                  ]},
      include_package_data = True,
      )
