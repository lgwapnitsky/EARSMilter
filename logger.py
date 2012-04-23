'''
Created on Apr 23, 2012

@author: lwapnitsky
'''

import datetime, logging, os, sys

class logger():
    now = datetime.datetime.now()
        
    def __init__(self,lname):
        '''
        Constructor
        '''

        self.logname = lname
        
        """set up logging - can be moved to a separate file as a class at some point"""
        self.DEBUG_LOG_FILENAME = '/var/log/%s.log' % lname
        self.WARNING_LOG_FILENAME = '/var/log/%s.err' % lname
        
        if not (os.path.isfile(self.DEBUG_LOG_FILENAME) and os.path.isfile(self.WARNING_LOG_FILENAME)):
            print "Please make sure that the log files exist by running the following commands as root:\n"
            print "touch %s\ntouch %s" %(self.DEBUG_LOG_FILENAME, self.WARNING_LOG_FILENAME)
            print "chmod 666 %s\nchmod 666 %s" %(self.DEBUG_LOG_FILENAME, self.WARNING_LOG_FILENAME)
        
            exit()

        

    def test(self):
        print self.DEBUG_LOG_FILENAME
        
    def start(self):
        formatter = logging.Formatter('[%(asctime)s] %(levelno)s (%(process)d) %(module)s: %(message)s')

        # set up logging to STDOUT for all levels DEBUG and higher
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.DEBUG)
        sh.setFormatter(formatter)

        # set up logging to a file for all levels DEBUG and higher
        fh = logging.FileHandler(self.DEBUG_LOG_FILENAME)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)

        # set up logging to a file for all levels WARNING and higher
        fh2 = logging.FileHandler(self.WARNING_LOG_FILENAME)
        fh2.setLevel(logging.WARN)
        fh2.setFormatter(formatter)

        # create Logger object
        newLogger = logging.getLogger(self.logname)
        newLogger.setLevel(logging.DEBUG)
        newLogger.addHandler(sh)
        newLogger.addHandler(fh)
        newLogger.addHandler(fh2)

        # create shortcut functions
        self.debug = newLogger.debug
        self.info = newLogger.info
        self.warning = newLogger.warning
        self.error = newLogger.error
        self.critical = newLogger.critical
                