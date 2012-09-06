.. EARS milter installation

EARS Milter Installation
########################

.. contents::
   :local:

Server Installation
*******************

This milter has been tested on Debian Squeeze/Wheezy using a LAMP
(Linux/Apache/MySQL/PHP)-based web server [#f1]_.

Debian Install
==============

Installing a Debian Squeeze/Wheezy server is a fairly straight-forward
procedure.  The best method to use can be found via HowtoForge's
`The Perfect Server - Debian Squeeze (Debian 6.0) [ISPConfig 2]`_ and following
it up through **8 Change The Default Shell** on page 3.


.. note::
   In WRT's environment, virtual linux servers are set up using Linux Containers (`lxc`_). 
   
   To create a new system, log in to the LXC server as root and use the  ``lxc-prepare`` `script`_.
   
   Make sure to edit ``/var/lib/lxc/<machine name>/rootfs/etc/network/interfaces`` and enter the appropriate
   static IP, routing and gateway information.
   
After logging in, make sure to install ``anacron``, ``cifs-utils``, ``telnet``,
``rsyslog`` and ``logrotate``.

.. code-block:: sh

   aptitude install telnet rsyslog logrotate cifs-utils anacron
   
   
   
Web Server Installation
=======================

.. note:: Unless otherwise specified, all commands are run as the ``root`` user.

The web server needs to be set up in a LAMP configuration (Apache Web Server,
MySQL, PHP)

#. Install MySQL

   .. code-block:: sh

      % aptitude install mysql-server mysql-client

   Enter a password for the root MySQL user.

#. Install Apache2

   .. code-block:: sh

      % aptitude install apache2

   Test to see that the web-server is running properly by visiting the IP
   address of this server in a web browser. You should see an image similar to
   this:

   .. image:: images/apache2.png

#. Install PHP5

   PHP5 and the Apache PHP5 module are required to serve the EARS web-based
   code.  Install them as follows:

   .. code-block:: sh

      % aptitude install php5 libapache2-mod-php5

   Restart Apache:

   .. code-block:: sh

     % /etc/init.d/apache2 restart

#. Install MySQL support in PHP5

   To get MySQL support in PHP, we can install the *php5-mysql* package. It's
   a good idea to install some other PHP5 modules as well as you might need
   them for your applications.

   .. code-block:: sh

      % aptitude install php5-mysql php5-curl php-pear php5-imagick \
         php5-mcrypt php5-memcache

   .. note::
   
      You can search for available PHP5 modules like
      this:
   
      .. code-block:: sh
   
         % apt-cache search php5

   
   Now restart Apache2:

   .. code-block:: sh

     % /etc/init.d/apache2 restart


Git Installation
================

`Git`_ [#f2]_ is required to download the EARS Milter code from the development
repository.

#. Install Git

   .. code-block:: sh

      % aptitude install git

#. Configure git access

   * On the EARS Milter server, create a *ssh* key and copy it to the
     development repository server:

      .. code-block:: sh

         ssh-keygen -t rsa

      Hit return at the prompts to create the key without passphrase
      authentication.

      .. code-block:: sh

         % scp ~/.ssh/id_rsa.pub root@git:/root

   * Log in to the repository server and authorize the key:

      .. code-block:: sh

         % ssh root@git
         % cd gitolite-admin
         % git pull
         % cp ~/id_rsa.pub keydir/root\@<milterservername>.pub
         % sed -i 's/\@.*$//g' keydir/root\@<milterservername>.pub
         % git add keydir/root\@<milterservername>.pub
         % git commit -a
         % git push
         % exit

   * On the EARS Milter server, test access to the repository server:

      .. code-block:: sh

         % cd /tmp % git clone gitolite@git:gitolite-admin

      If this fails, please verify all the steps in this section


Mail Server Installation
========================

EARS requires an MTA.  Please choose **either** postfix or sendmail.

.. contents::
   :local:

Postfix
-------

#. Install postfix with `PCRE`_ support:

   .. code-block:: sh

      % aptitude install postfix postfix-pcre

   If prompted to remove packages relating to ``exim4`` or ``sendmail``,
   choose to *Accept the solution*.

   When prompted for *mail server configuration type*, choose
   *Satellite System*:

   .. image:: images/postfix1.png

   Enter a fully-qualified domain name in the form of
   *servername.wrtdesign.com*, where *servername* is the name of the EARS
   Milter server. Make sure that there is a DNS entry for this server and its
   corresponding IP address on the DNS server.

   .. image:: images/postfix2.png

   Enter the FQDN of the MS Exchange server when prompted for a relay host:

   .. image:: images/postfix3.png

   Accept the defaults for *Root and postmaster mail recipient*,
   *Other destinations to accept mail for* and *Force synchronous updates...*.

   For *Local networks*, enter ``10.102.0.0/16, 192.168.0.0/24, 127.0.0.1``.
   This will handle all of WRT's internal networks as well as the localhost.

   Accept all the rest of the defaults.

#. Add the following lines to ``/etc/postfix/main.cf``:

   .. code-block:: sh

      disable_vrfy_command = yes 
      smtpd_command_filter = pcre:/etc/postfix/bogus_commands 
      smtpd_recipient_restrictions = permit_mynetworks reject_unauth_destination

   Remove the following line from the same file:

   .. code-block:: sh

      #inet_interfaces = loopback-only

   Edit the following line to read:

   .. code-block:: sh

      inet_protocols = ipv4


#. Open up ``/etc/postfix/master.cf`` and uncomment the line:

   .. code-block:: sh

      #submission inet n       -       -       -       -       smtpd

   Add the following lines (with indentation) to the same file:

   .. code-block:: sh

      scan      unix  -       -       n       -       10      smtp
       -o smtp_send_xforward_command=yes 
       -o disable_mime_output_conversion=yes 
       -o smtp_generic_maps=

   Add the following (indented) after the line marked ``relay``:

   .. code-block:: sh

        -o smtp_fallback_relay=

#. Create a file called ``/etc/postfix/bogus_commands`` and enter the
   following two lines:

   .. code-block:: sh

      /^[^ ]{3}\s.*/  NOOP 
      /^https{0,1}\:\/\/.*/ NOOP

#. Reload the configuration and send a test message:

   .. code-block:: sh

      % postfix reload
      % telnet localhost 25
      telnet localhost 25
      Trying 127.0.0.1...
      Connected to localhost.
      Escape character is '^]'.
      220 ph-wks-lin01.wrtdesign.com ESMTP Postfix (Debian/GNU)
      ehlo localhost
      250-ph-wks-lin01.wrtdesign.com
      250-PIPELINING
      250-SIZE 10240000
      250-ETRN
      250-STARTTLS
      250-ENHANCEDSTATUSCODES
      250-8BITMIME
      250 DSN
      mail from: root
      250 2.1.0 Ok
      rcpt to: ph_test@wrtdesign.com
      250 2.1.5 Ok
      data
      354 End data with <CR><LF>.<CR><LF>
      test
      .
      250 2.0.0 Ok: queued as 4F00049F2A
      quit

Sendmail
--------

#. Install sendmail:

   .. code-block:: sh

      % aptitude install sendmail

   If prompted to remove packages relating to ``exim4`` or ``postfix``,
   choose to *Accept the solution*.

#. Open the file ``/etc/mail/sendmail.mc`` in an editor.  Add the following
   lines above ``MAILER DEFINITIONS``:

   .. code-block:: sh

      dnl # FEATURE(`allmasquerade')dnl FEATURE(`masquerade_envelope')dnl
      FEATURE(`accept_unresolvable_domains') FEATURE(`accept_unqualified_senders')
      define(`SMART_HOST',`exchange.domain.com')dnl
      define(`confDOMAIN_NAME',`milterserver.domain.com') dnl #

   Change these lines:

   .. code-block:: sh

      dnl
      DAEMON_OPTIONS(`Family=inet6, Name=MTA-v6, Port=smtp, Addr=::1')dnl
      DAEMON_OPTIONS(`Name=MTA-v4,Address=127.0.0.1,Family=inet,Port=smtp')
      dnl
      DAEMON_OPTIONS(`Family=inet6, Name=MSP-v6, Port=submission, M=Ea, Addr=::1')dnl
      DAEMON_OPTIONS(`Name=MSP-v4,Address=127.0.0.1,Family=inet,Port=submission,Modifiers=aE')

   to

   .. code-block:: sh

      dnl
      DAEMON_OPTIONS(`Family=inet6, Name=MTA-v6, Port=smtp, Addr=::1')dnl
      DAEMON_OPTIONS(`Name=MTA,Family=inet,Port=smtp')
      dnl
      DAEMON_OPTIONS(`Family=inet6, Name=MSP-v6, Port=submission, M=Ea, Addr=::1')dnl
      DAEMON_OPTIONS(`Name=MSP,Family=inet,Port=submission,Modifiers=aE')


#. Open the file ``/etc/mail/access``.  Uncomment the following lines
   (according to your network):

   .. code-block:: sh

      Connect:10
      RELAY GreetPause:10           0
      ClientConn:10           OK
      ClientRate:10           0

   Add additional lines for each FQDN of this IP address

#. Add all internal recipient domains to ``/etc/mail/relay-domains``

   Example:

      .. code-block:: sh

         wrtdesign.com ph.wrtdesign.com


#. Recompile the ``sendmail`` files and restart the MTA and send a test
   message

   .. code-block:: sh

      % touch /etc/mail/access.new.db
      % sendmailconfig
      % telnet localhost 25
      Connected to localhost.
      Escape character is '^]'.
      220 mailproc-test2 ESMTP
      ehlo localhost
      250-mailproc-test2 Hello localhost [127.0.0.1], pleased to meet you
      250-ENHANCEDSTATUSCODES
      250-PIPELINING
      250-EXPN
      250-VERB
      250-8BITMIME
      250-SIZE
      250-DSN
      250-ETRN
      250-DELIVERBY
      250 HELP
      mail from: root
      250 2.1.0 root... Sender ok
      rcpt to: ph_test@wrtdesign.com
      250 2.1.5 ph_test@wrtdesign.com... Recipient ok
      data
      354 Enter mail, end with "." on a line by itself
      test
      .
      250 2.0.0 q7VDE019017465 Message accepted for delivery
      quit


Python Installation/Configuration
*********************************

.. contents::
   :local:

The default version of Python in Debian Squeeze/Wheezy is 2.7.  This is what we
will be installing, along with a Python package installer (pip) and some
development libraries.

.. code-block:: sh

   % aptitude install python python-pip python-dev libmilter-dev libmilter1.0.1  libmysqlclient-dev
   
   
Next we will need to install a number of Python modules.  There are two ways to
do this - the Debian way and the Python way. Each one has its advantages and
disadvantages, but both are provided for instructional purposes.

The recommendation is to stick with one method instead of combining them.

The Python Method (preferred)
=============================

The Python Package Index (`PyPI`_) is the most up-to-date resource for Python
modules.  Bugfixes and updates are regularly submitted for a majority of
modules.  The downside is that there is currenlty no way to automatically
update the modules, but this can be considered a benefit as well since there is
less chance of your code breaking.

.. code-block:: sh
   
   % pip install SQLAlchemy pymilter MySQL-python Mako tnefparse

The Debian Method
=================

Using debian's built-in package manager is very easy and convenient.  When you
do a full update on a Debian system, installed Python modules will be updated
as well.  The downside is that sometimes the modules in the Debian repositories
can be out-of-date.

Here is the simple command to install the required modules, except for
``tnefparse`` which has to be installed via the Python method:

.. code-block:: sh

   % aptitude install python-sqlalchemy python-milter python-mysqldb python-mako


Optional Software Installation
******************************

.. contents::
   :local:

phpMyAdmin
==========

`phpMyAdmin`_ is a web interface through which you can manage your MySQL
databases. It's a good idea to install it:

.. code-block:: sh

   % aptitude install phpmyadmin php5-gd

You will see the following question:

   | ``Web server to reconfigure automatically:`` <-- apache2
   | ``Configure database for phpmyadmin with dbconfig-common?`` <-- No

Afterwards, you can access phpMyAdmin by going to
``http://<serverIP>/phpmyadmin/:``

.. image:: images/phpMyAdmin.png

`Webmin`_ Installation
======================

#. Create a file called ``/etc/apt/sources.list.d/webmin.list``.  Add the
   following lines, then save:

   .. code-block:: sh

      deb http://download.webmin.com/download/repository sarge contrib deb
      http://webmin.mirror.somersettechsolutions.co.uk/repository sarge contrib

#. Download and install the security key, then update and install ``webmin``:

   .. code-block:: sh

      % cd /root
      % wget http://www.webmin.com/jcameron-key.asc
      % apt-key add jcameron-key.asc
      % aptitude update
      % aptitude install webmin

#. Test the installation by going to ``https://<serverIP>:10000``.  Log in
   using the system root password.




Accquiring and configuring the Milter
*************************************
#. Using *git*, clone **EARS** from the repository to the ``/var/spool``
   folder:

   .. code-block:: sh

      % cd /var/spool % git clone gitolite@git:EARSmilter EARS % cd EARS


   #. Copy EARS.sh to ``/etc/init.d``.  Make it executable and enable it
      at boot.

      .. code-block:: sh

         % cp /var/spool/EARS/EARS.sh /etc/init.d 
         % chmod +x /etc/init.d/EARS.sh 
         % update-rc.d EARS.sh enable defaults

#. Create a virtual host file for Apache in
   ``/etc/apache2/sites-available/ears.conf`` that contains the following
   (modify as necessary):

   .. code-block:: sh

      <VirtualHost *:80>
         ServerName ears.wrtdesign.com DocumentRoot /var/www/EARS
         Options -Indexes
      </VirtualHost>

   Create a link to this file to make the site active:

   .. code-block:: sh

      % ln -s /etc/apache2/sites-available/ears.conf \
      /etc/apache2/sites-enabled/ears.conf

   Create a folder called ``/var/www/EARS``.  Copy the files from
   ``/var/spool/EARS/www`` to this new folder and give Apache full rights to
   the folder. Restart Apache.

   .. code-block:: sh

      % mkdir -p /var/www/EARS % cp -R /var/spool/EARS/www/* /var/www/EARS
      % chown -R www-data.www-data  /var/www/EARS
      % chmod -x /var/www/EARS/*.php
      % /etc/init.d/apache2 restart


#. Open the MySQL command-line utility

   .. code-block:: sh

      % mysql -u 'root' -p

   Create a blank database and associated MySQL user

   .. code-block:: sql

      mysql> CREATE DATABASE EARS; mysql> GRANT ALL PRIVILEGES ON
      EARS.* TO "EARS"@"%" IDENTIFIED BY "password"; mysql> FLUSH PRIVILEGES; mysql> EXIT

   and change this line in ``/etc/mysql/my.cnf``:

   .. code-block::  sh

      bind-address = 127.0.0.1

   to:

   .. code-block:: sh

      bind-address = 0.0.0.0


#. Set the appropriate permissions on ``/var/spool/EARS`` and its
   subdirectories based on the MTA installed.

   Postfix

   .. code-block:: sh

      % chown -R postfix.postfix /var/spool/EARS


   Sendmail

   .. code-block:: sh

      % chown -R smmta.smmta /var/spool/EARS


   You will also need to edit ``/etc/init.d/EARS.sh`` and replace **postfix**
   with **smmta**.

   .. code-block:: sh

      % sed -i.bak 's/postfix/smmta/g' /etc/init.d/EARS.sh




#. Create the log files:

   .. code-block:: sh

      % touch /var/log/EARSmilter.log
      % touch /var/log/EARSmilter.err
      % chmod 666 /var/log/EARSmilter.log
      % chmod 666 /var/log/EARSmilter.err

#. Add/edit the following lines to the configuration file for the appropriate
   MTA:

   **Postfix** - ``/etc/postfix/main.cf``

   .. code-block:: sh

      milter_protocol = 6
      smtpd_milters = unix:/var/spool/EARS/EARSmilter.sock milter_default_action = accept

   Reload postfix - ``postfix reload``

  **Sendmail** - ``/etc/mail/sendmail.mc``.

   .. code-block:: sh

      INPUT_MAIL_FILTER(`EARS', `S=unix:/var/spool/EARS/EARSmilter.sock, F=T, T=S:240s;R:240s;E:5m')dnl

   Recompile the ``sendmail`` files and restart the MTA

   .. code-block:: sh

      % touch /etc/mail/access.new.db % sendmailconfig

   .. note:: If/when you add additional milters to this sytem, make sure that
      **EARS** is the last one listed, as milters are processed in order.

#. Edit the database information in
   ``/var/spool/EARS/EARSmilter/EARSmilter.py`` with what is appropriate for
   your environment.

   This is listed under :py:func:`EARSmilter.EARSmilter.milter.eom`

   .. code-block:: py

      db = toDB( 'EARS', 'password', 'localhost', 'EARS' )

#. Create a folder called ``/dropdir`` :

   .. code-block:: sh

      % mkdir -p /dropdir

   Mount it to a folder called ``dropdir`` on a FTP server.  This example
   assumes the folder is on a MS Windows box:

   .. code-block:: sh

      % echo '\\FTPSERVER\FTPSHARE\dropdir  /dropdir  cifs  workgroup=DOMAIN, \
         file_mode=0777,dir_mode=0777,password=PASSWORD,uid=1000,gid=1000, \
         username=USERNAME 0  0' >> /etc/fstab % mount -a
      % mount -a

#. Start the EARS milter:

   .. code-block:: sh

      /etc/init.d/EARS.sh start

#. Add a ``cron`` job to run the ``purgeEARSdb`` script on a weekly basis.

   .. code-block:: sh

      % crontab -e

  Add this line:

  .. code-block:: sh

      /usr/bin/env python /var/spool/EARS/purgeEARSdb/purgeEARSdb.py -s \
         milter.domain.com -d EARS -u EARS -p password -q -x -v#purge EARS database

  For a description of the options, see **How To Use** under :py:func:`purgeEARSdb`.

#. Add the following lines to ``/etc/logrotate.conf``:

   .. code-block:: sh

      /var/log/EARSmilter.* {
        compress copytruncate
      }


.. :rubric:: Footnotes

.. [#f1] Adapted from HowtoForge's `Installing Apache2 With PHP5 And MySQL Support On Debian Squeeze (LAMP)`_
.. [#f2] `Pro Git`_ by Scott Chacon is available to read online for free.

.. _Postfix before-queue Milter support: http://www.postfix.org/MILTER_README.html
.. _The Perfect Server - Debian Squeeze (Debian 6.0) [ISPConfig 2]: http://www.howtoforge.com/perfect-server-debian-squeeze-ispconfig-2
.. _Installing Apache2 With PHP5 And MySQL Support On Debian Squeeze (LAMP): http://www.howtoforge.com/installing-apache2-with-php5-and-mysql-support-on-debian-squeeze-lamp
.. _lxc: http://lxc.sourceforge.net/
.. _script: http://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=1&ved=0CCAQFjAA&url=http://mindref.blogspot.com/2011/01/debian-lxc-create.html&ei=Gxk-UO7IMIH86wGEoIGgDg&usg=AFQjCNH8nf1DFSRpLmQigOgj8AsU-xhA3Q&sig2=KpSOTudr5eTp97MCE7aLRw
.. _phpMyAdmin:  http://www.phpmyadmin.net
.. _Git: http://git-scm.com
.. _Pro Git: http://git-scm.com/book
.. _Webmin: http://www.webmin.com/deb.html
.. _PCRE:  http://www.pcre.org
.. _PyPI: http://pypi.python.org 
.. _How To Use: codedocs/purgeEARSdb_py#how_to_use