import Milter
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

from Milter.utils import parse_addr

from StringIO import StringIO

from datetime import date
from datetime import datetime

from email import Errors
from email.Message import Message

from logger import logger

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
        self.log = EARS() 
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
            parsed = ProcessMessage(self.id, self._msg, self.R, self.db, self.log)
            self._msg, self.subjChange = parsed.ParseAttachments()

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


## === === ##

class ProcessMessage():
    def __init__(self, _id, _msg, _R, _db, _log):
        self._msg = _msg
        self.id = _id
        self.recipients = _R
        self.db = _db
        self.log = _log
        
        self.fhandling = FileSys(self._msg)
        self.attachDir = self.fhandling.attachDir

        self.subjChange = False

#        return self.ParseAttachments()


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
                    
            data = part.get_payload(decode=1)
            fname, lrg_attach = self.extract_attachment(data, fname)

            if re.match('winmail.dat', fname, re.IGNORECASE):
                self.log.info('Processing "%s":' % fname)
                removedParts.append(part)
                winmail_parts = self.winmail_parse(fname)
                if len(winmail_parts) > 0:
                    self.log.info('Extracted from "%s":' % fname)
                    for wp in winmail_parts:
                        fnames.append(wp)
                        self.log.info('\t%s: %s' % (wp[0], self.fhandling.filesize_notation(wp[1])))
                else:
                    self.subjChange = True
                    removedParts = []

            else:
                if lrg_attach <= self.fhandling.min_attach_size:
                    part_payload.append(part)
                else:
                    removedParts.append(part)
                    self.log.info('\t%s: %s' % (fname, self.fhandling.filesize_notation(lrg_attach)))
                    fnames.append([fname, lrg_attach, bn_filesize, enc_fname])

            if len(removedParts) > 0:
#                notice = mako_notice(fnames, attachDir)
                notice_added = False
                for rp in removedParts:
                    rp = self.delete_attachments(rp, notice)#, notice_added)
                    if notice_added == False:
                        part_payload.append(rp)
                        notice_added = True
                    else:
                        shutil.rmtree(attachDir)
                        
                        
            part_payload.insert(0, msg.get_payload(0))
            msg.set_payload(part_payload)

            return (msg, self.subjChange)
                                                                                                                    
            

    def extract_attachment(self, data, fname):
        file_counter = 1
        file_created = False
        fname_to_write = fname.replace("\n","").replace("\r","")

        while file_created == False:
            exdir_file = "%s/%s" % (self.attachDir, fname_to_write)
            
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
                                
                if  (exdir_file_size <= self.fhandling.min_attach_size) and (not(re.match('winmail.dat', fname, re.IGNORECASE))):
                    os.remove(exdir_file)
                    
        return (fname_to_write, exdir_file_size)

    def winmail_parse(self, fname):
        wparts = []
        body_types = ({'body':'txt', 'htmlbody':'html'})
        body = None
        
        winmail_file = '%s/%s' % (self.attachDir, fname)
        
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
                                                                                                                                                                            
## === === ##

class FileSys():
    def __init__(self, msg):
        self.msg = msg
        
        self.dropDir = "/dropdir/"
        self.min_attach_size = 163840
        self.remfile = "Retrieve_Attachments.html"
        
        self.attachDir = self.Dir()

    def Dir(self):
        out = tempfile.TemporaryFile()
        self.msg.dump(out)
        out.seek(0)
        buf = out.read()
        hashDir = self.hashit(buf)
        attachDir = self.dropDir + hashDir
        
        if not os.path.isdir(attachDir):
            os.mkdir(attachDir)
            
        return attachDir

    def hashit(self, data):
        sha1 = hashlib.sha1()
        sha1.update(data)

        return sha1.hexdigest()
    
    def filesize_notation(self,filesize):
        f_num = float(filesize)
        notation = ['', 'K', 'M', 'G']
        magnitude = 0
        while f_num > 1024:
            f_num = f_num / 1024
            magnitude += 1
            
        return '{0:.2f} {1}B'.format(f_num, notation[magnitude])
                            
