.. EARS milter requirements

EARS Milter Requirements
########################

The EARS Milter is a Python-based `mail-filter`_ written for the `postfix`_ and `sendmail`_ mail transfer agents (MTAs).

.. note:: *Postfix* or *sendmail* must be installed on your system in order for this milter to function properly.
   It may work with any other MTA that supports milters but has only been tested with postfix and sendmail.

.. note:: *This milter has only been tested on Python 2.7 running on Debian Squeeze/Wheezy*

Server Requirements
*******************

The following software is required for the Milter to run:

* `Debian Squeeze/Wheezy`_
* `MySQL database`_
* `Apache HTTP Server`_
* `PHP 5.x`_
* `postfix`_ or `sendmail`_
* `Git`_ - required to download the Milter from the development repository
* cifs-utils



Python Requirements
*******************

The following Python modules are required on the system in order for the EARS Milter to function:

* `Python 2.7`_
* `SQLAlchemy`_
* `pymilter`_
* `MySQLdb`_
* `tnefparse`_
* `mako`_

Recommended Software
********************

While not necessary, this software should be installed as it will be referenced during the installation procedure:

* telnet
* rsyslog
* logrotate
* `Webmin`_


Optional Software
*****************

The following software is optional, but is useful for diagnostics

* `phpMyAdmin`_


.. _mail-filter: http://www.milter.orghttp://www.webmin.com/deb.html
.. _postfix: http://www.postfix.org
.. _sendmail: http://www.sendmail.com/sm/open_source/docs/
.. _Python 2.7: http://python.org
.. _SQLalchemy: http://sqlalchemy.org
.. _pymilter: http://www.bmsi.com/python/milter.html
.. _MySQLdb: http://mysql-python.sourceforge.net/MySQLdb.html
.. _tnefparse: https://github.com/koodaamo/tnefparse
.. _mako: http://www.makotemplates.org/
.. _MySQL database: http://www.mysql.com
.. _Apache HTTP Server: http://projects.apache.org/projects/http_server.html
.. _PHP 5.x : http://www.php.net
.. _Debian Squeeze/Wheezy: http://www.debian.org/releases
.. _phpMyAdmin: http://www.phpmyadmin.net
.. _Git: http://git-scm.com
.. _Webmin: http://www.webmin.com/deb.html