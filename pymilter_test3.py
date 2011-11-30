#! /usr/bin/env python

import Milter
import StringIO
import email
import email.Message
import hashlib
import mime
import os
import sys
import tempfile
import time
import rfc822


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

    def close(self):
        # always called, even when abort is called.  Clean up
        # any external resources here.
        return Milter.CONTINUE

    def abort(self):
        # client disconnected prematurely
        return Milter.CONTINUE

    def log(self,*msg):
        logq.put((msg,self.id,time.time()))
    
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
    
    @Milter.noreply
    def body(self,chunk):
        self.fp.write(chunk)
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


    def attachment(self):
        msg = self._msg
        attachDir = attach_dir(msg)
        removedParts = []
        payload = []
        
        
        for part in msg.walk():
            fname = ""
            
            if part.is_multipart():
                continue
            
            dtypes = part.get_params(None, 'Content-Disposition')

            if not dtypes:
                if part.get_content_type() == 'text/plain':
                    payload.append(part)
                    continue
                ctypes = part.getparams()
                if not ctypes:
                    continue
                for key,val in ctypes:
                    if key.lower() == 'name':
                        fname = val
            else:
                for key,val in dtypes:
                    if key.lower() == 'filename':
                        fname = val
                        
            if fname:
                removedParts.append(fname)
                data = part.get_payload(decode=1)
                extract_attachment(data, attachDir, fname)
                part = self.delete_attachments(part, fname)
                payload.append(part)

#        self.log(payload)
        del msg["content-type"]
        del msg["content-disposition"]
        del msg["content-transfer-encoding"]

        msg.set_type('plain/txt')
        msg.set_payload(payload)

        self._msg = msg

        return Milter.CONTINUE
        
    def delete_attachments(self, part,fname):
        for key,value in part.get_params():
            part.del_param(key)
            
        part.set_payload('[DELETED]\n')
        del part["content-type"]
        del part["content-disposition"]
        del part["content-transfer-encoding"]
        part["Content-Type"] = "text/plain, name="+fname+".TXT"
        return part


    def eom(self):
        self.fp.seek(0)
        self._msg = mime.message_from_file(self.fp)
        self.attachment()
        
        self.log("### MESSAGE ###")
        self.log(self._msg)

        #return Milter.ACCEPT
        return Milter.TEMPFAIL
## ===





def attach_dir(msg):
    tempname = fname = tempfile.mktemp(".tmp")
    out = tempfile.TemporaryFile()
    msg.dump(out)
    out.seek(0)
    buf = out.read()
    hashDir = hashit(buf)
    attachDir = dropDir + hashDir
    
    if not os.path.isdir(hashDir):
        os.mkdir(attachDir)

    return attachDir


def extract_attachment(data, attachDir, fname):
    exdir_file = attachDir + "/" + fname
    extracted = open(exdir_file, "wb")
    extracted.write(data)
    extracted.close()
    


def hashit(data):
    sha1 = hashlib.sha1()
    # f = open(filepath, 'rb')
    # try:
    #     sha1.update(f.read())
    # finally:
    #     f.close()
    sha1.update(data)
       
    return sha1.hexdigest()

dropDir = "/dropdir/"

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
    print "%s milter shutdown" % time.strftime('%Y%b%d %H:%M:%S')

if __name__ == "__main__":
    main()
