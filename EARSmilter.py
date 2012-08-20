#!/usr/bin/env python

import Milter
import codecs
import datetime
import email
import email.Message
import hashlib
import mime
import os
import re
import rfc822
import shutil
import sys
import tempfile
import time
import tnefparse
import urllib2
import unicodedata
import types

from Milter.utils import parse_addr

from StringIO import StringIO

from datetime import date, datetime, timedelta
>>>>>>> Stashed changes

import Milter
import EARS

from datetime import date
from datetime import timedelta


## ==  IP Information
from socket import AF_INET, AF_INET6
## ==

## === Define multiprocessing == ##

if True:
    from multiprocessing import Process as Thread, Queue
else:
    from threading import Thread
    from Queue import Queue

logq = Queue(maxsize=4)

#from optparse import OptionParser
#parser = OptionParser()
#parser.add_option("-v", "--verbose",
#                  action="store_true", dest="verbose", default=False,
#                  help="Enables debug logging to %s" % EARSlog.DEBUG_LOG_FILENAME)
#(opts, args) = parser.parse_args()


#rgxSubject = re.compile('^(subject)', re.IGNORECASE | re.DOTALL)
#rgxMessageID = re.compile('^(message-id)', re.IGNORECASE | re.DOTALL)


def background():
    while True:
        t = logq.get()
        if not t: break
        msg, id, ts = t
        print "%s [%d]" % (time.strftime('%Y%b%d %H:%M:%S', time.localtime(ts)), id),
        # 2005Oct13 02:34:11 [1] msg1 msg2 msg3 ...
        for i in msg: print i,
        print

## === End Define Multiprocesing === ##

def main():
    bt = Thread(target=background)
    bt.start()
    socketname = "/var/spool/EARS/EARSmilter.sock"
    timeout = 600
    Milter.factory = EARS.milter
    flags = Milter.CHGBODY + Milter.CHGHDRS + Milter.ADDHDRS
    flags += Milter.ADDRCPT
    flags += Milter.DELRCPT
    Milter.set_flags(flags)     # tell Sendmail/Postfix which features we use
    Milter.runmilter("EARSmilter", socketname, timeout)
    logq.put(None)
    bt.join()

if __name__ == "__main__":
    main()
