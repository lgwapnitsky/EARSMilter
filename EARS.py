import Milter
import datetime
import email
import email.Message
import mime
import tempfile
import re
import rfc822
import os
import sys
import time

from logger import logger

from StringIO import StringIO

from Milter.utils import parse_addr

from email import Errors
from email.Message import Message

from datetime import date
from datetime import datetime

from socket import AF_INET, AF_INET6

from toDB import toDB

class EARS():
    def __init__(self):
        self.log = logger('EARSmilter')
        
    def info(self, *msg):
        for i in msg: self.log.info(i)
    
    def warn(self, *msg):
        for i in msg: self.log.warning(i)
    
    def debug(self, *msg):
        for i in msg: self.log.debug(i.replace("\n","").replace("\r",""))

    def err(self, *msg):
        for i in msg: self.log.error(i) #.replace("\n","").replace("\r",""))


class EARSmilter(Milter.Base):
    def __init__(self):
        #self.EARS = EARS()
        self.log = EARS() #self.EARS.log
        self.log.log.start()
        self.id = Milter.uniqueID()

    def close(self):
        return Milter.CONTINUE

    def abort(self):
        self.log.warn('!!! client disconnected prematurely !!!')

    @Milter.noreply
    def connect(self, IPname, family, hostaddr):
        self.IP = hostaddr[0]
        self.port = hostaddr[1]
        if family == AF_INET6:
            self.flow = hostaddr[2]
            self.scope = hostaddr[3]
        else:
            self.flow = None
            self.scope = None
        self.IPname = IPname # Name from a reverse IP lookup
        self.H = None
        self.fp = None
        self.subjMsgId = {}
        self.receiver = self.getsymval('j')
        self.subjChange = False 
        self.headers = []

        return Milter.CONTINUE

    @Milter.noreply
    def header(self, name, hval):
        rgxSubject = re.compile('^(subject)', re.IGNORECASE | re.DOTALL)
        rgxMessageID = re.compile('^(message-id)', re.IGNORECASE | re.DOTALL)


        self.fp.write("%s: %s\n" % (name, hval))
        self.headers.append("%s: %s\n" % (name, hval))

        if (rgxSubject.search(name)) or (rgxMessageID.search(name)):
            self.log.info("%s: %s" % (name, hval))
            self.subjMsgId[name] = hval
        
        return Milter.CONTINUE


    @Milter.noreply
    def body(self, chunk):
        self.fp.write(chunk)
        return Milter.CONTINUE

    @Milter.noreply
    def eoh(self):
        self.fp.write("\n")# terminate headers
        return Milter.CONTINUE

    def envfrom(self, mailfrom, *str):
        self.F = mailfrom
        self.R = []
        self.fromparms = Milter.dictfromlist(str)
        self.user = self.getsymval('{auth_authen}')
        self.fp = StringIO()
        self.canon_from = '@'.join(parse_addr(mailfrom))
        self.fp.write('From %s %s\n' % (self.canon_from, time.ctime()))
        return Milter.CONTINUE

    @Milter.noreply
    def envrcpt(self, recipient, *str):
        rcptinfo = recipient, Milter.dictfromlist(str)
        self.R.append(rcptinfo)
        return Milter.CONTINUE
                            
    def eom(self):
        self.db = toDB()
        self.db.NewMessage(self.canon_from, self.headers)
        
        self.fp.seek(0)
        msg = mime.message_from_file(self.fp)
        self._msg = msg

        try:
           self._msg = ProcessMessage(self.id, self._msg, self.R, self.db)
           out = tempfile.TemporaryFile()
           try:
               msg.dump(out)
               out.seek(0)
               msg = rfc822.Message(out)
               msg.rewindbody()
               
               
               while 1:
                   buf = out.read(8192)
                   if len(buf) == 0: break
                   self.replacebody(buf)
           finally:
               out.close()
           
           return Milter.ACCEPT
                                           
        except Exception, e:
            self.log.warn(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.log.err(exc_type, fname, exc_tb.tb_lineno)
            
            return Milter.TEMPFAIL


class ProcessMessage():
    def __init__(self, _msgID, _msg, _R, _db):
        self._msg = _msg
        self.msgID = _msgID
        self.recipients = _R
        self.db = _db

        return self.ParseAttachments()

    def ParseAttachments(self):
        msg = self._msg
        removedParts = []
        part_payload = []
        fnames = []
        bn_filesize = ''
        enc_fname = ''

        
        for part in msg.walk():
            fname = ""

            if part.is_multipart():
                continue

            dtypes = part.get_params(None, 'Content-Disposition')

            if not dtypes:
                if part.get_content_type() == 'text/plain':
                    continue

                ctypes = part.getparams()
                if not ctypes:
                    continue
                for key, val in ctypes:
                    if key.lower() == 'name':
                        fname = val
            else:
                for key, val in dtypes:
                    if key.lower() == 'filename':
                        fname = val
                                
            if fname:
                if type(fname) is tuple:
                    fname = fname[2]
                    
            print fname
                    
            data = part.get_payload(decode=1)

