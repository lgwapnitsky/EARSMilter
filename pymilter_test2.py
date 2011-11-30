#! /usr/bin/env python

import Milter
import StringIO
import email
import email.Message
import mime
import rfc822
import sys
import tempfile
import time
import unittest
import os

from email import Errors
from email.Message import Message

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


def background():
    while True:
        t = logq.get()
        if not t: break
        msg,id,ts = t
        print "%s [%d]" % (time.strftime('%Y%b%d %H:%M:%S',time.localtime(ts)),id),
        # 2005Oct13 02:34:11 [1] msg1 msg2 msg3 ...
        for i in msg: print i,
        print

## === End Define Multiprocesing === ##

class mltr_SaveAttachments(Milter.Base):

    def __init__(self):
        self.id = Milter.uniqueID()

    def log(self,*msg):
        logq.put((msg,self.id,time.time()))
    
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
        self.receiver = self.getsymval('j')
        self.log("connect from %s at %s" % (IPname, hostaddr) )
        return Milter.CONTINUE

    @Milter.noreply
    def header(self, name, hval):
        self.fp.write("%s: %s\n" % (name,hval))	# add header to buffer
        return Milter.CONTINUE
    
    @Milter.noreply
    def eoh(self):
        self.fp.write("\n")				# terminate headers
        return Milter.CONTINUE
    
    

    def envfrom(self,mailfrom,*str):
#        self.log("envfrom")
        # self.F = mailfrom
        # self.R = []
        # self.fromparms = Milter.dictfromlist(str)
        # self.user = self.getsymval('{auth_authen}')
        # self.log("mail from:", mailfrom, *str)
        self.fp = StringIO.StringIO()
        # self.canon_from = '@'.join(parse_addr(mailfrom))
        # self.fp.write('From %s %s\n' % (self.canon_from,time,ctime()))
        return Milter.CONTINUE

    def body(self, chunk):
 #       self.log("body")
        self.fp.write(chunk)
        return Milter.CONTINUE
  
    def replacebody(self,chunk):
  #      self.log("replacebody") 
        if self._body:
            self._body.write(chunk)
            self.bodyreplaced = True
            #            self.log("mail body chunk")
            #            self.log(chunk)
            return Milter.CONTINUE
        else:
            raise IOError,"replacebody not called from eom()"
        return Milter.TEMPFAIL
    
    def attachment(self):
        self.log("### check_name ###")
        parts = self._msg.get_payload()
        for p in parts:
            self.log(p.getnames())
            mime.check_name(self._msg)
        self.log(self._msg.ismodified())
#        self.log(self._msg)
    #     self.log("### attachment ###")
    #     self.log("ismultipart",self._msg.ismultipart())
    #     parts = self._msg.get_payload()
    #     self.log("number of parts: ",len(parts))
    #     self.log("parts:\n",parts)
    #     t = self._msg.get_content_type().lower()
    #     for i in parts:
    #         name = i.getname()
    #         if name:
    #             self.log(name)
    #             warning = name+".txt"
    #             del self._msg["content-type"]
    #             del self._msg["content-disposition"]
    #             del self._msg["content-transfer-encoding"]
    #             self._msg["Content-Type"] = "text/plain; name="+warning
    #     self.log("content-type",t)

    

    def eom(self):
        self.fp.seek(0)
        msg = mime.message_from_file(self.fp)
        self.log("### iterators.structure ###")
        email.Iterators._structure(msg)
        self.log("### check_attachments ###")
        mime.check_attachments(msg,_list_attach)
        self._msg = msg
        self.attachment()
        

#        self._body = StringIO.StringIO()


#         self.tempname = fname = tempfile.mktemp(".tmp")
# #        self.log(self.tempname)
        
#         out = tempfile.TemporaryFile()
        
#         try:
#             msg = self._msg
#             msg.dump(out)
#             out.seek(0)
#             msg = rfc822.Message(out)
        
#             msg.rewindbody()
#             while 1:
#                 buf = out.read(8192)
#                 if len(buf) == 0: break
#                 self.replacebody(buf)
        msg = self._msg
#        self.log("### message ###\n",msg)
#        return Milter.ACCEPT
        return Milter.TEMPFAIL
        # finally:
        #     out.close()
        # return Milter.TEMPFAIL
        

## ===

def _list_attach(msg):
    t = msg.get_content_type()
    p = msg.get_payload(decode=True)
    print msg.get_filename(),msg.get_content_type(),type(p)
    msg = msg.get_submsg()
    if isinstance(msg,Message):
        return mime.check_attachments(msg,_list_attach)
    return Milter.CONTINUE

# def check_attachments(msg,check):
#     """Scan attachments.
#     msg	MimeMessage
#     check	function(MimeMessage): int
#     Return CONTINUE, REJECT, ACCEPT
#     """
#     if msg.is_multipart():
#         for i in msg.get_payload():
#             rc = check_attachments(i,check)
#             if rc != Milter.CONTINUE: return rc
#         return Milter.CONTINUE
#     return check(msg)


def main():
    bt = Thread(target=background)
    bt.start()
    socketname = "/tmp/py_testmilter.sock"
    timeout = 600
    Milter.factory = mltr_SaveAttachments
    flags = Milter.CHGBODY + Milter.CHGHDRS + Milter.ADDHDRS
    flags += Milter.ADDRCPT
    flags += Milter.DELRCPT
    Milter.set_flags(flags)     # tell Sendmail/Postfix which features we use
    print "%s milter startup" % time.strftime('%Y%b%d %H:%M:%S')
    sys.stdout.flush()
    Milter.runmilter("py_testmilter",socketname,timeout)
    logq.put(None)
    bt.join()
    print "%s bms milter shutdown" % time.strftime('%Y%b%d %H:%M:%S')

if __name__ == "__main__":
    main()
