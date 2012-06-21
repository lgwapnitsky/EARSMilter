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
import tnefparse
import types
import urllib

import logger

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
EARSlog = logger.logger('EARSmilter')

from optparse import OptionParser
parser = OptionParser()
parser.add_option("-v", "--verbose",
                  action="store_true", dest="verbose", default=False,
                  help="Enables debug logging to %s" % EARSlog.DEBUG_LOG_FILENAME)
(opts, args) = parser.parse_args()


rgxSubject = re.compile('^(subject)', re.IGNORECASE | re.DOTALL)
rgxMessageID = re.compile('^(message-id)', re.IGNORECASE | re.DOTALL)


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

class mltr_SaveAttachments(Milter.Base):

    def __init__(self):
        self.id = Milter.uniqueID()
        self.EARSlog = EARSlog
        self.verbose = opts.verbose
        
    def close(self):
        # always called, even when abort is called.  Clean up
        # any external resources here.
        return Milter.CONTINUE

    def abort(self):
        # client disconnected prematurely
        # self.EARSlog.warning('client disconnected prematurely')
        return Milter.CONTINUE

    def log(self, *msg):
        for i in msg: self.EARSlog.info(i)
    
    def debug(self, *msg):
        if self.verbose == True:
            for i in msg: self.EARSlog.debug(i.replace("\n", "").replace("\r", ""))
        
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
        return Milter.CONTINUE

    @Milter.noreply
    def header(self, name, hval):
        self.fp.write("%s: %s\n" % (name, hval))     # add header to buffer
        self.subjMsgId = {}
        
        if (rgxSubject.search(name)) or (rgxMessageID.search(name)):
            self.log("%s: %s" % (name, hval))
            self.subjMsgId[name] = hval

        else:
            self.debug("%s: %s\n" % (name, hval))
        return Milter.CONTINUE
    
    @Milter.noreply
    def body(self, chunk):
        self.fp.write(chunk)
        return Milter.CONTINUE

    @Milter.noreply
    def eoh(self):
        self.fp.write("\n")				# terminate headers
        return Milter.CONTINUE
    
    def envfrom(self, mailfrom, *str):
#        self.log("envfrom")
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

    
    def attachment(self):
        msg = self._msg
        attachDir = attach_dir(msg)
        removedParts = []
        part_payload = []
        fnames = []
        bn_filesize = ''
        enc_fname = ''

        self.log('From %s' % self.canon_from)
        for R in self.R:
            for recipient in R:
                if not len(recipient) < 1: self.log('To %s' % recipient)
        self.log('Folder: %s' % attachDir)

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
                data = part.get_payload(decode=1)
                fname, lrg_attach = extract_attachment(data, attachDir, fname)

                if re.match('winmail.dat', fname, re.IGNORECASE):
                    removedParts.append(part)
                    winmail_parts = winmail_parse(fname, attachDir)
                    if len(winmail_parts) > 0:
                        self.log('Extracted from "%s":' % fname)
                        for wp in winmail_parts:    
                            fnames.append(wp)
                            self.log('     %s: %s' % (wp[0], filesize_notation(wp[1])))
                    else:
                        self.subjChange = True
                else:
                    if lrg_attach <= min_attach_size:
                        part_payload.append(part)
                    else:
                        removedParts.append(part)
                        self.log('%s: %s' % (fname, filesize_notation(lrg_attach)))
                        fnames.append([fname, lrg_attach, bn_filesize, enc_fname])

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
         
        part_payload.insert(0, msg.get_payload(0))
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

    def delete_attachments(self, part, notice):
        for key, value in part.get_params():
            part.del_param(key)

        del part["content-type"]
        del part["content-disposition"]
        del part["content-transfer-encoding"]
        
        part["content-disposition"] = "attachment; filename=" + remfile
        part["content-type"] = "text/html"
        part.set_payload(notice)
        return part


    def eom(self):
        if self.subjChange:
            regex_AP = re.compile("\[Attachments Processed\]", re.IGNORECASE | re.DOTALL)
            oldSubj = filter(rgxSubject.match, self.subjMsgId.keys())
            newSubj = regex_AP.sub("", oldSubj[0])
            self.chgheader(oldSubj[0], 1, newSubj)
        
        self.fp.seek(0)
        msg = mime.message_from_file(self.fp)
        self._msg = msg
        
        self.attachment()
        return Milter.ACCEPT
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
        


        attach.append(fname)
        
        
    EARStemplate = Template(filename='EARS.html', output_encoding='utf-8', encoding_errors='replace')
    buf = StringIO()
    ctx = Context(buf, filepath=path, attachments=attach, deldate=exp_date)
    
    try:
        EARStemplate.render_context(ctx)
        return buf.getvalue()   
    except:
        return exceptions.html_error_template().render()


def attach_dir(msg):
#    tempname = fname = tempfile.mktemp(".tmp")
    out = tempfile.TemporaryFile()
    msg.dump(out)
    out.seek(0)
    buf = out.read()
    hashDir = hashit(buf)
    attachDir = dropDir + hashDir
    
    if not os.path.isdir(attachDir):
        os.mkdir(attachDir)

    return attachDir


def winmail_parse(fname, attachDir):
    wparts = []
    body_types = ({'body':'txt', 'htmlbody':'html'})
    body = None

    winmail_file = '%s/%s' % (attachDir, fname)

    winmail_file_open = open(winmail_file, 'rb')

    tnef = tnefparse.parseFile(None, winmail_file_open)
    
    for btype, ext in body_types.iteritems():
        if btype in dir(tnef):
            bodydata = getattr(tnef, btype, None)
            msgfname = 'Original_Message.%s' % ext
            if isinstance(bodydata, types.ListType):
                body = bodydata[0]
            else: body = bodydata
            exdir_file = '%s/%s' % (attachDir, msgfname)
            with open(exdir_file, "wb") as origMsg:
                origMsg.write(body)
                wparts.append([msgfname, os.path.getsize(exdir_file), '', ''])
    
    for attachment in tnef.attachments:
        exdir_file = '%s/%s' % (attachDir, attachment.name)
        with open(exdir_file, "wb") as wdat_file:
            wdat_file.write(attachment.data)
        wparts.append([attachment.name, os.path.getsize(exdir_file), '', ''])

    return wparts

def extract_attachment(data, attachDir, fname):
    file_counter = 1
    file_created = False
    fname_to_write = fname.replace("\n", "").replace("\r", "")

    while file_created == False:
        exdir_file = attachDir + "/" + fname_to_write

        if os.path.exists(exdir_file):
            fileName, fileExtension = os.path.splitext(fname)
            fname_to_write = "%s(%d)%s" % (fileName, file_counter, fileExtension)
            file_counter += 1
        else:
            extracted = open(exdir_file, "wb")
            extracted.write(data)
            extracted.close()
            exdir_file_size = os.path.getsize(exdir_file)
            
            file_created = True


            if  (exdir_file_size <= min_attach_size) and (not(re.match('winmail.dat', fname, re.IGNORECASE))):
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
    EARSlog.start()
    bt = Thread(target=background)
    bt.start()
    socketname = "/var/spool/EARS/EARSmilter.sock"
    timeout = 600
    Milter.factory = mltr_SaveAttachments
    flags = Milter.CHGBODY + Milter.CHGHDRS + Milter.ADDHDRS
    flags += Milter.ADDRCPT
    flags += Milter.DELRCPT
    Milter.set_flags(flags)     # tell Sendmail/Postfix which features we use
    EARSlog.info("milter startup")
    Milter.runmilter("EARSmilter", socketname, timeout)
    logq.put(None)
    bt.join()
    EARSlog.info("milter shutdown")

if __name__ == "__main__":
    main()
