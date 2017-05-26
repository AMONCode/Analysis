# setup.py

from distutils.core import setup

setup(name = "AmonPy",
      version = "1.4",
      description='AMON Analysis Code',
      author='Miles Smith, Gordana Tesic',
      author_email='mus44@psu.edu, gut10@psu.edu',
      packages = ['amonpy',
                  'amonpy/anal',
                  'amonpy/dbase',
                  'amonpy/sim',
                  'amonpy/tools',
                  'amonpy/ops',
                  'amonpy/ops/analyser',
                  'amonpy/ops/network/',
                  'amonpy/ops/network/scripts'
                 ],
      scripts = ['amonpy/ops/run_archival.py', 'amonpy/ops/run_basic_sim.py'],
      )
