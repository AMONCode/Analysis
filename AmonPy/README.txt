======
AmonPy
======

AmonPy provides the software for operating AMON, including transmitting, 
managing, and analyzing data from multiple high-energy observatories
   

Dependencies
============


Python
------
The following python packages are required:

* NumPy

* SciPy

* MySQLdb

* VOEventLib

* wxPython 

* Celery

* Twisted

Other
-----

1) For developers producing documentation:

* Doxygen

* doxypy

(note: you have to edit Doxyfile to specify your path to AmonPy in order to run Doxygen)

2) mysql 

3) RabbitMQ


Database
============

Scripts to create databases are in mysql directory. 
README file there explains how to run them.

If you are creating your own database, or recreating database on db.hpc.rcc.psu.edu
run amonpy/dbase/test_db_write.py in order to populate event and alert configuration 
tables. If these two tables are empty, events and alerts produced by
analysis code cannot be written in event and alert table due to the foreign keys constraints.


Amonpy
============

AMON analysis software is in amonpy directory. README file there explains
how to run the software. 

Installation (i.e. only if this code is obtained via package distribution, rather than svn check out)
============

Ignore text bellow if you have a developer distribution of the code from the AMON SVN respiratory.

To install AMON package run:

python setup.py install

Code will run without installation as well, if run from the source code subdirectories:
amonpy/ops 

  Note:

  If installed:

  1) simulation and clustering analysis scripts can be found in build/scripts-2.7
    Copy dbaccess.txt file from amonpy/ops in your running directory and edit it to put 
    your own information there.

  2) Also add these lines to your .bash_profile or create a new script to source before
     running the installed code:
      
     export AMONPY="path-to-your-AmonPy"
     PYTHONPATH="$AMONPY/amonpy:${PYTHONPATH}"
     PYTHONPATH="$AMONPY/amonpy/dbase:${PYTHONPATH}"
     PYTHONPATH="$AMONPY/amonpy:${PYTHONPATH}"
     PYTHONPATH="$AMONPY/amonpy/ops:${PYTHONPATH}"
     PYTHONPATH="$AMONPY/amonpy/sim:${PYTHONPATH}"
     PYTHONPATH="$AMONPY/amonpy/tools:${PYTHONPATH}"
     PYTHONPATH="$AMONPY/amonpy/anal:${PYTHONPATH}"

     export PYTHONPATH 
     
     These lines are not needed to be sourced if code is run from the source code directories.
     

Documentation
============

To browse the AmonPy package documentation, open docs/html/index.html file with your browser.


