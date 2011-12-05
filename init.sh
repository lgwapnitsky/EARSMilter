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
PYTHONPATH=/usr/lib/python2.4

# path to app
APP_PATH=/var/spool/EARS

# path to paster bin
#DAEMON=<path to pylons workingenv>/bin/paster
DAEMON=/var/spool/EARS/pymilter_test8.py

# startup args
#DAEMON_OPTS=" serve --log-file <my logfile> --server-name=main production.ini"

# script name
NAME=EARS_milter.sh

# app name
DESC=EARS_Milter

# pylons user
RUN_AS=postfix

PID_FILE=/var/run/milter.pid

############### END EDIT ME ##################

test -x $DAEMON || exit 0

set -e

case "$1" in
  start)
        echo -n "Starting $DESC: "
        start-stop-daemon -d $APP_PATH -c $RUN_AS --start --background --pidfile $PID_FILE  --make-pidfile --exec $DAEMON -- $DAEMON_OPTS
        echo "$NAME."
        ;;
  stop)
        echo -n "Stopping $DESC: "
        start-stop-daemon --stop --pidfile $PID_FILE
        echo "$NAME."
        ;;

  restart|force-reload)
        echo -n "Restarting $DESC: "
        start-stop-daemon --stop --pidfile $PID_FILE
        sleep 1
        start-stop-daemon -d $APP_PATH -c $RUN_AS --start --background --pidfile $PID_FILE  --make-pidfile --exec $DAEMON -- $DAEMON_OPTS
        echo "$NAME."
        ;;
  *)
        N=/etc/init.d/$NAME
        echo "Usage: $N {start|stop|restart|force-reload}" >&2
        exit 1
        ;;
esac

exit 0