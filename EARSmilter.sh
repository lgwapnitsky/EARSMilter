#! /bin/sh

### BEGIN INIT INFO
# Provides:          <my_app> application instance
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts instance of <my_app> app
# Description:       starts instance of <my app> app using start-stop-daemon
### END INIT INFO

############### EDIT ME ##################
# path to workingenv install if any
#PYTHONPATH=/usr/lib/python2.7

# path to app
APP_PATH=/var/spool/EARS

# path to paster bin
DAEMON=/var/spool/EARS/EARSmilter.py

# startup args
#DAEMON_OPTS=" serve --log-file <my logfile> --server-name=main production.ini"

# script name
NAME=EARS_milter.sh

# app name
DESC='WRT E-mail Attachment Retrieval System milter'

# pylons user
RUN_AS=postfix

PID_FILE=/var/run/milter.pid

############### END EDIT ME ##################

do_start()
{
    echo -n "Starting $DESC: "
    until [ -e $PID_FILE ]
    do
	start-stop-daemon -d $APP_PATH -c $RUN_AS --start --background --pidfile $PID_FILE  --make-pidfile --exec $DAEMON -- $DAEMON_OPTS
    done
    echo "$NAME."
}

do_stop()
{
    until [ ! -e $PID_FILE ]
    do
	start-stop-daemon --stop --pidfile $PID_FILE
    done
}


test -x $DAEMON || exit 0

set -e

case "$1" in
  start)
	if ps ax | grep -v grep | grep $DAEMON > /dev/null
	then
	    echo "$DESC is already running..."
	else
	    do_start
            # echo -n "Starting $DESC: "
	    # until [ -e $PID_FILE]
	    # do
	    # 	start-stop-daemon -d $APP_PATH -c $RUN_AS --start --background --pidfile $PID_FILE  --make-pidfile --exec $DAEMON -- $DAEMON_OPTS
	    # done
            # echo "$NAME."
	fi
        ;;
  stop)
        echo -n "Stopping $DESC: "
	until [ ! ps ax | grep -v grep | grep $DAEMON > /dev/null ]
	do
	    do_stop
	done
	# do
        #     start-stop-daemon --stop --pidfile $PID_FILE
	# done
        echo "$NAME."
        ;;

  restart|force-reload)
        echo -n "Restarting $DESC: "
            start-stop-daemon --stop --pidfile $PID_FILE
            #sleep 1
	until [ -e $PID_FILE]
	do
            start-stop-daemon -d $APP_PATH -c $RUN_AS --start --background --pidfile $PID_FILE  --make-pidfile --exec $DAEMON -- $DAEMON_OPTS
	done
        echo "$NAME."
        ;;
  *)
        N=/etc/init.d/$NAME
        echo "Usage: $N {start|stop|restart|force-reload}" >&2
        exit 1
        ;;
esac


exit 0