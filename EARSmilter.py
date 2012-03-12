#! /usr/bin/env python

import Milter
import datetime
import email
import email.Message
import hashlib
import mime
import os
import sys
import tempfile
import time
import rfc822
import re
import urllib


from mako.template import Template
from mako.runtime import Context
from mako import exceptions

from StringIO import StringIO

from Milter.utils import parse_addr

from email import Errors
from email.Message import Message

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

class LogOutput():
    def __init__(self, logfile):
        self.stdout = sys.stdout
        d = os.path.dirname(logfile)
        if not os.path.exists(d):
            os.makedirs(d)
        self.log = open(logfile, 'w')
 
    def write(self, text):
        self.stdout.write(text)
        self.log.write(text)
        self.log.flush()
 
    def close(self):
        self.stdout.close()
        self.log.close()


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
    def body(self, chunk):
        self.fp.write(chunk)
        return Milter.CONTINUE

    @Milter.noreply
    def eoh(self):
        self.fp.write("\n")				# terminate headers
        return Milter.CONTINUE
    
    def envfrom(self,mailfrom,*str):
#        self.log("envfrom")
        self.F = mailfrom
        self.R = []
        self.fromparms = Milter.dictfromlist(str)
        self.user = self.getsymval('{auth_authen}')
        self.log("mail from:", mailfrom, *str)
#        self.fp = StringIO.StringIO()
        self.fp = StringIO()
        self.canon_from = '@'.join(parse_addr(mailfrom))
        self.fp.write('From %s %s\n' % (self.canon_from,time.ctime()))
        return Milter.CONTINUE

  ##  def envrcpt(self, to, *str):
    @Milter.noreply
    def envrcpt(self, recipient, *str):
        rcptinfo = recipient,Milter.dictfromlist(str)
        self.R.append(rcptinfo)
        
        return Milter.CONTINUE


    def attachment(self):
        msg = self._msg
        attachDir = attach_dir(msg)
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
                for key,val in ctypes:
                    if key.lower() == 'name':
                        fname = val
            else:
                for key,val in dtypes:
                    if key.lower() == 'filename':
                        fname = val
                        
            if fname:
                data = part.get_payload(decode=1)
                fname,lrg_attach = extract_attachment(data, attachDir, fname)
#                fnames.append([fname, lrg_attach,bn_filesize])

#                if lrg_attach > min_attach_size:
#                    removedParts.append(part)
#                else:
                if lrg_attach <= min_attach_size:
                    part_payload.append(part)
                    #fnames.remove([fname, lrg_attach, bn_filesize])
                else:
                    removedParts.append(part)
                    fnames.append([fname, lrg_attach,bn_filesize, enc_fname])



        if len(removedParts) > 0:
            notice = mako_notice(fnames, attachDir)
            notice_added = False
            for rp in removedParts:
                rp = self.delete_attachments(rp, notice)#, notice_added)
                if notice_added == False:
                    part_payload.append(rp)
                    notice_added = True
        else:
                os.rmdir(attachDir)
         
        part_payload.insert(0,msg.get_payload(0))
#        self.log(msg.get_payload(0))
        msg.set_payload(part_payload)

        self._msg = msg

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
            
            
        return Milter.CONTINUE

    def delete_attachments(self, part, notice):#, fname, notice):
        for key,value in part.get_params():
            part.del_param(key)

        del part["content-type"]
        del part["content-disposition"]
        del part["content-transfer-encoding"]
        
        part["content-disposition"] = "attachment; filename=" + remfile
        part["content-type"] = "text/html"
        part.set_payload(notice)
        return part


    def eom(self):
        self.fp.seek(0)
        msg = mime.message_from_file(self.fp)
        self._msg = msg
        
        self.attachment()
        return Milter.ACCEPT
#        return Milter.TEMPFAIL
## ===

def filesize_notation(filesize):
    f_num = float(filesize)
    notation = ['', 'K', 'M', 'G']
    magnitude = 0
    while f_num > 1024:
        f_num = f_num / 1024
        magnitude += 1
    
    return '{0:.2f} {1}B'.format(f_num, notation[magnitude])





def mako_notice(fnames, attachDir):
    attach = []
    path = '';
    
    exp_date = date.today() + timedelta(30)
    exp_date = exp_date.strftime('%B %d, %Y')

    for fname in fnames:
        regex_dropdir = re.compile("dropdir/(.*)")
        r1 = regex_dropdir.search(attachDir)
        dirs = r1.groups()
        if not path: path = dirs[0]
        
        fname[2] = filesize_notation(fname[1])
        fname[3] = urllib.quote(fname[0])
        

        print fname[3]

        attach.append(fname)#, dirs[0]])
        
        
    EARStemplate = Template(filename='EARS.html', output_encoding='utf-8', encoding_errors='replace')
    buf = StringIO()
    ctx = Context(buf, filepath=path, attachments=attach, deldate=exp_date)
    
    try:
        EARStemplate.render_context(ctx)
        return buf.getvalue()
    except:
        return exceptions.html_error_template().render()


def attach_dir(msg):
    tempname = fname = tempfile.mktemp(".tmp")
    out = tempfile.TemporaryFile()
    msg.dump(out)
    out.seek(0)
    buf = out.read()
    hashDir = hashit(buf)
    attachDir = dropDir + hashDir
    
    if not os.path.isdir(attachDir):
        os.mkdir(attachDir)

    return attachDir


def extract_attachment(data, attachDir, fname):
    file_counter = 1
    file_created = False
    fname_to_write = fname.replace("\n","").replace("\r","")

    while file_created == False:
        exdir_file = attachDir + "/" + fname_to_write

        if os.path.exists(exdir_file):
            fileName,fileExtension = os.path.splitext(fname)
            fname_to_write = "%s(%d)%s" % (fileName,file_counter,fileExtension)
            file_counter += 1
        else:
            extracted = open(exdir_file, "wb")
            extracted.write(data)
            extracted.close()
            exdir_file_size = os.path.getsize(exdir_file)
            
            file_created = True


            if  exdir_file_size <= min_attach_size:
                os.remove(exdir_file)

    return (fname_to_write, exdir_file_size)


def hashit(data):
    sha1 = hashlib.sha1()
    sha1.update(data)
      
    return sha1.hexdigest()

dropDir = "/dropdir/"
min_attach_size = 163840
remfile = "Retrieve_Attachments.html"

def main():
    sys.stdout = LogOutput("/var/log/EARS.log")

    bt = Thread(target=background)
    bt.start()
    socketname = "/var/spool/EARS/EARSmilter.sock"
    timeout = 600
    Milter.factory = mltr_SaveAttachments
    flags = Milter.CHGBODY + Milter.CHGHDRS + Milter.ADDHDRS
    flags += Milter.ADDRCPT
    flags += Milter.DELRCPT
    Milter.set_flags(flags)     # tell Sendmail/Postfix which features we use
    print "%s milter startup" % time.strftime('%Y%b%d %H:%M:%S')
    
    sys.stdout.flush()
    Milter.runmilter("EARSmilter",socketname,timeout)
    logq.put(None)
    bt.join()
    print "%s milter shutdown" % time.strftime('%Y%b%d %H:%M:%S')

if __name__ == "__main__":
    main()
