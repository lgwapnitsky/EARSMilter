"""The main startup file for the EARS milter

.. module:: EARS.py
    :synopsis: The startup file for the EARS milter
    
.. moduleauthor:: Larry G. Wapnitsky <larry@wapnitsky.com>

"""


#!/usr/bin/env python

import Milter
import time

from EARSmilter import EARSmilter as EARS


## === Define multiprocessing == ##

if True:
    from multiprocessing import Process as Thread, Queue
else:
    from threading import Thread
    from Queue import Queue

logq = Queue( maxsize = 4 )


def background():
    """
    This function starts the background threading of EARS so that multiple processes can handle incoming messages.
    """

    while True:
        t = logq.get()
        if not t: break
        msg, id, ts = t
        print "%s [%d]" % ( time.strftime( '%Y%b%d %H:%M:%S', time.localtime( ts ) ), id ),
        # 2005Oct13 02:34:11 [1] msg1 msg2 msg3 ...
        for i in msg: print i,
        print

## === End Define Multiprocesing === ##

def main():
    """
    The main startup for the EARS milter.
    
    Milter factory flags are set so that the milter can:
        * Change the body of the message
        * Change the headers of the message
        * Add headers to the message
        * Add/Delete recipients
    """
    bt = Thread( target = background )
    bt.start()
    socketname = "/var/spool/EARS/EARSmilter.sock"
    timeout = 600
    Milter.factory = EARS.milter
    flags = Milter.CHGBODY + Milter.CHGHDRS + Milter.ADDHDRS
    flags += Milter.ADDRCPT
    flags += Milter.DELRCPT
    Milter.set_flags( flags )     # tell Sendmail/Postfix which features we use
    Milter.runmilter( "EARSmilter", socketname, timeout )
    logq.put( None )
    bt.join()

if __name__ == "__main__":
    main()
