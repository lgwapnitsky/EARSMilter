.. EARS milter requirements

EARS Milter Requirements
########################

The EARS Milter is a `python-based mail-filter`_ written for the `postfix mail transfer agent (MTA)`_.  Postfix must be installed on your system in order for this milter to function properly.  It may work with any other MTA that supports milters but has only been tested with postfix.

*This milter has only been tested on Python 2.7*

Python Requirements
*******************

The following Python modules are required on the system in order for the EARS Milter to function:

* `Python 2.7`_
* `SQLAlchemy`_
* `pymilter`_
* `MySQLdb`_
* `tnefparse`_
* `mako`_

Additional Requirements
***********************

The following software is required for the milter to run:

* `MySQL database`_
* `Apache HTTP Server`_
* `PHP 5.x`_



.. _python-based mail-filter: http://www.postfix.org/www.postfix.org/MILTER_README.html
.. _postfix mail transfer agent (MTA): http://www.postfix.org
.. _Python 2.7: http://python.org
.. _SQLalchemy: http://sqlalchemy.org
.. _pymilter: http://www.bmsi.com/python/milter.html
.. _MySQLdb: http://mysql-python.sourceforge.net/MySQLdb.html
.. _tnefparse: https://github.com/koodaamo/tnefparse
.. _mako: http://www.makotemplates.org/
.. _MySQL database: http://www.mysql.com
.. _Apache HTTP Server: http://projects.apache.org/projects/http_server.html
.. _PHP 5.x : http://www.php.net