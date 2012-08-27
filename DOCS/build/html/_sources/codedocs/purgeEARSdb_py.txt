.. EARS milter code documentation - purgeEARSdb.py

purgeEARSdb.py
##############




How to use
**********
Proper usage of purgeEARSdb.py


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

