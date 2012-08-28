.. EARS milter code documentation - purgeEARSdb.py

purgeEARSdb.py
##############

.. automodule:: purgeEARSdb
   :members: 

.. autoclass:: Options
   :members:
   
   .. note:: 
   
         For command-line usage, see :ref:`how_to_use`.

.. autoclass:: Purge
   :members:


.. _how_to_use:

How to use
**********

Proper usage of purgeEARSdb.py

.. code-block:: sh


   usage: purgeEARSdb.py [-h] [-q] [-v] [-D DAYS] [-H HOURS] [-M MINUTES] [-x] -s
                      SERVER -d DATABASE -u USERNAME -p PASSWORD

   Purge old messages/attachments from EARS database

   optional arguments:
     -h, --help            show this help message and exit

    -q, --quiet           Run without prompting
     -v, --verbose         Verbose output

   Message/Attachment age options:
     -D DAYS, --days DAYS  Remove message older than x days (default = 7)
     -H HOURS, --hours HOURS
                           Remove message older than x hours (default = 0)
     -M MINUTES, --minutes MINUTES
                           Remove message older than x minutes (default = 0)

   Sender Options:
     -x, --purge-senders   Purge senders from database that are no longer
                           associated with messages/attachments

   Database Options (required):
     -s SERVER, --server SERVER
                           MySQL server name
     -d DATABASE, --database DATABASE
                           MySQL database name
     -u USERNAME, --username USERNAME
                           MySQL username
     -p PASSWORD, --password PASSWORD
                           MySQL password


Example :program:`cron` job setup:

.. code-block:: sh

   @daily /usr/bin/env python /var/spool/EARS/purgeEARSdb/purgeEARSdb.py -s mailproc.wrtdesign.com -d EARS -u EARS -p WRTears -q -x -v

This setups a daily job to run the script and remove non-associated senders from the database using the default of 7 days

