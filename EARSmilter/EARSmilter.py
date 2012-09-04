"""EARS Milter definitions and functions

.. :module:: EARSmilter.py
    :synopsis: EARS Milter definitions and functions
    
.. moduleauthor:: Larry G. Wapnitsky <larry@qual-ITsystems.com>

"""

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

from email import Errors
from email.Message import Message

from logs.logger import logger

from mako.template import Template
from mako.runtime import Context
from mako import exceptions

from socket import AF_INET, AF_INET6

from database.toDB import *

sys.stdout = codecs.getwriter( 'utf-8' )( sys.stdout )

class EARSlog():
    """
    Establishes logging for different error statuses:  INFO, WARN, DEBUG, ERR
    """
    def __init__( self ):
        self.log = logger( 'EARSmilter' )

    def info( self, *msg ):
        for i in msg: self.log.info( i )

    def warn( self, *msg ):
        for i in msg: self.log.warning( i )

    def debug( self, *msg ):
        for i in msg: self.log.debug( i.replace( "\n", "" ).replace( "\r", "" ) )

    def err( self, *msg ):
        for i in msg: self.log.error( i ) #.replace("\n","").replace("\r",""))

logfile = EARSlog()
logfile.log.start()

## === === ##

class milter( Milter.Base ):
    """
    Milter processing derived from pymilter.
    
    **Only functions that have been heavily modified from standard Milter processing
    have been documented**
    
    """
    def __init__( self ):
        """
        Connects to the established log and sets a unique ID for the Milter process
        """
        self.log = logfile
        self.id = Milter.uniqueID()

    def close( self ):
        return Milter.CONTINUE

    #===========================================================================
    # def abort( self ):
    #    self.log.warn( '!!! client disconnected prematurely !!!' )
    #===========================================================================

    @Milter.noreply
    def connect( self, IPname, family, hostaddr ):
        """
        Initializes when a new connection to the Milter is made via SMTP
        """
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
        self.receiver = self.getsymval( 'j' )
        self.subjChange = False
        self.Subject = None
        self.headers = []

        return Milter.CONTINUE

    @Milter.noreply
    def header( self, name, hval ):
        """
        Processes headers from the incoming message and writes them to a new variable for database storage.
        """
        rgxSubject = re.compile( '^(subject)', re.IGNORECASE | re.DOTALL )
        rgxMessageID = re.compile( '^(message-id)', re.IGNORECASE | re.DOTALL )


        self.fp.write( "%s: %s\n" % ( name, hval ) )
        self.headers.append( "%s: %s\n" % ( name, hval ) )

        if ( rgxSubject.search( name ) ) or ( rgxMessageID.search( name ) ):
            self.log.info( "%s: %s" % ( name, hval ) )
            self.subjMsgId[name] = hval
            if ( rgxSubject.search( name ) ): self.Subject = hval

        return Milter.CONTINUE


    @Milter.noreply
    def body( self, chunk ):
        self.fp.write( chunk )
        return Milter.CONTINUE

    @Milter.noreply
    def eoh( self ):
        self.fp.write( "\n" )# terminate headers
        return Milter.CONTINUE

    def envfrom( self, mailfrom, *str ):
        self.F = mailfrom
        self.R = []
        self.fromparms = Milter.dictfromlist( str )
        self.user = self.getsymval( '{auth_authen}' )
        self.fp = StringIO()
        self.canon_from = '@'.join( parse_addr( mailfrom ) )
        self.fp.write( 'From %s %s\n' % ( self.canon_from, time.ctime() ) )
        return Milter.CONTINUE

    @Milter.noreply
    def envrcpt( self, recipient, *str ):
        rcptinfo = recipient, Milter.dictfromlist( str )
        self.R.append( rcptinfo )
        return Milter.CONTINUE

    def eom( self ):
        """
        End-Of-Message milter function
        
        Connection to the database is established here via the toDB class:
        
        .. code-block:: py
        
            db = toDB( 'root', 'python', 'python.dev.wrtdesign.com', 'EARS' )
            
        The variables above can be changed accordingly.
        
        New messages are initialized in the database via:
        
        .. code-block:: py
        
            db.newMessage( self.canon_from, self.Subject, self.headers, self._msg, self.R )        

        and are subsequently shipped to the ProcessMessage class to parse/remove attachments,
        then add the EARS link page to the message before being sent to the recipient(s)
        
        If an error occurs, an Exception is thrown and logged to the <logname>.err file
        """

        self.fp.seek( 0 )
        msg = mime.message_from_file( self.fp )
        self._msg = msg

        db = toDB( 'root', 'python', 'python.dev.wrtdesign.com', 'EARS' )
        db.newMessage( self.canon_from, self.Subject, self.headers, self._msg, self.R )

        try:
            parsed = ProcessMessage( db, self.log , self.F )
            self._msg, self.subjChange = parsed.ParseAttachments()
            db.message.body = self._msg

            out = tempfile.TemporaryFile()
            try:
                msg.dump( out )
                out.seek( 0 )
                msg = rfc822.Message( out )
                msg.rewindbody()

                while 1:
                    buf = out.read( 8192 )
                    if len( buf ) == 0: break
                    self.replacebody( buf )

            finally:
                out.close()
                db.close()

#            return Milter.TEMPFAIL
            return Milter.ACCEPT

        except Exception, e:
            self.log.warn( e )
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split( exc_tb.tb_frame.f_code.co_filename )[1]
            self.log.err( exc_type, fname, exc_tb.tb_lineno )

#            return Milter.TEMPFAIL

            return Milter.ACCEPT




## === === ##

class ProcessMessage():
    """
    All message processing is done via this class.
    
    * Attachments are parsed/removed
    * Winmail.DAT files are extracted
    * Retreive_Attachments.html file is added to original message
    * Message information is stored in the MySQL database
    """

    def __init__( self, _db, _log, _from ):
        """
        * **_db** - toDB class
        * **_log** - EARSlog class
        * **_from** - sender's e-mail address
        
        **subChange** is set to *False*.  If no attachments are removed, **subChange**
        will be set to *True* and "Removed Attachments" will be removed from the subject line
        """

        self.db = _db
        self.message = self.db.message
        self.log = _log
        self._from = _from

        self.fhandling = FileSys( self.message.raw_original )
        self.attachDir = self.fhandling.attachDir

        self.subjChange = False

        self.remfile = "Retrieve_Attachments.html"


    def ParseAttachments( self ):
        """
        The message is passed through this function in order to analyze and potentially remove attachments
        
        If the attached file is WINMAIL.DAT, it is sent for further processing so that the files it contains
        can be extracted and provided to the recipient(s)
        
        Attachments are then analyzed for size and, if are above the set threshold, are detached.
        
        If no attachments are extracted, the folder created in the **dropDir** is removed.
        
        Otherwise, the "Retrieve_Attachments.html" notice is created and appended to the original message along
        with any attachments that remained below the threshold
        """

        msg = self.message.raw_original
        sender = self.message.sender
        recipients = self.message.recipients

        removedParts = []
        part_payload = []
        fnames = []
        bn_filesize = ''
        enc_fname = ''

        self.log.info( 'From %s' % self._from )

        for recipient in recipients:
            if not len( recipient.email_address ) < 1: self.log.info( 'To %s' % recipient.email_address )

        self.log.info( 'Folder: %s' % self.attachDir )


        for part in msg.walk():
            fname = ""

            if part.is_multipart():
                continue

            dtypes = part.get_params( None, 'Content-Disposition' )

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
                if type( fname ) is tuple:
                    fname = fname[2]

                data = part.get_payload( decode = 1 )
                fname, lrg_attach = self.extract_attachment( data, fname )

                if re.match( 'winmail.dat', fname, re.IGNORECASE ):
                    self.log.info( 'Processing "%s":' % fname )
                    removedParts.append( part )
                    winmail_parts = self.winmail_parse( fname )
                    if len( winmail_parts ) > 0:
                        self.log.info( 'Extracted from "%s":' % fname )
                        for wp in winmail_parts:
                            fnames.append( wp )
                            self.log.info( '\t%s: %s' % ( wp[0], self.fhandling.filesize_notation( wp[1] ) ) )
                    else:
                        self.subjChange = True
                        removedParts = []

                else:
                    if lrg_attach <= self.fhandling.min_attach_size:
                        part_payload.append( part )
                    else:
                        removedParts.append( part )
                        self.log.info( '\t%s: %s' % ( fname, self.fhandling.filesize_notation( lrg_attach ) ) )
                        fnames.append( [fname, lrg_attach, bn_filesize, enc_fname] )

        if len( removedParts ) > 0:
            notice = self.mako_notice( fnames )
            notice_added = False
            for rp in removedParts:

                rp = self.delete_attachments( rp, notice )
                if notice_added == False:
                    part_payload.append( rp )
                    notice_added = True
        else:
            shutil.rmtree( self.attachDir )

        try:
            part_payload.insert( 0, msg.get_payload( 0 ) )

        finally:
            msg.set_payload( part_payload )

        return ( msg, self.subjChange )

    def extract_attachment( self, data, fname ):
        """
        Used to extract attachments that are NOT in a WINMAIL.DAT file.
        
        Filenames are unicode-corrected.
        """
        file_counter = 1
        file_created = False
        fname_to_write = fname

        while file_created == False:
            fname_to_write = self.fhandling.unicodeConvert( fname_to_write )
            fname_to_write = fname_to_write.replace( "\n", "" ).replace( "\r", "" )

            exdir_file = os.path.join( self.attachDir, fname_to_write )

            if os.path.exists( exdir_file ):
                fileName, fileExtension = os.path.splitext( fname_to_write )
                fileName = re.sub( '\(\d*\)$', '', fileName )
                fname_to_write = u"".join( [unicode( fileName ), u'(', unicode( file_counter ), u')', unicode( fileExtension )] )
                file_counter += 1
            else:
                extracted = open( exdir_file, "wb" )
                extracted.write( data )
                extracted.close()
                exdir_file_size = os.path.getsize( exdir_file )

                self.db.addAttachment( fname_to_write, self.fhandling.hashit( data ), data )

                file_created = True

                if  ( exdir_file_size <= self.fhandling.min_attach_size ) and ( not( re.match( 'winmail.dat', fname, re.IGNORECASE ) ) ):
                    os.remove( exdir_file )


        return ( fname_to_write, exdir_file_size )

    def winmail_parse( self, fname ):
        """
        If a WINMAIL.DAT file is attached to this message, parse and attempt to extract the files it contains.
        
        For more information on WINMAIL.DAT and TNEF files, please see `Transport Neutral Encapsulation Format <http://en.wikipedia.org/wiki/Transport_Neutral_Encapsulation_Format>`_
        """
        wparts = []
        body_types = ( {'body':'txt', 'htmlbody':'html'} )
        body = None

        winmail_file = '%s/%s' % ( self.attachDir, fname )

        winmail_file_open = open( winmail_file, 'rb' )

        tnef = tnefparse.parseFile( None, winmail_file_open )

        for btype, ext in body_types.iteritems():
            if btype in dir( tnef ):
                bodydata = getattr( tnef, btype, None )
                msgfname = 'Original_Message.%s' % ext
                if isinstance( bodydata, types.ListType ):
                    body = bodydata[0]
                else: body = bodydata
                exdir_file = '%s/%s' % ( self.attachDir, msgfname )
                with open( exdir_file, "wb" ) as origMsg:
                    origMsg.write( body )
                    wparts.append( [msgfname, os.path.getsize( exdir_file ), '', ''] )

        for attachment in tnef.attachments:
            exdir_file = '%s/%s' % ( self.attachDir, attachment.name )
            with open( exdir_file, "wb" ) as wdat_file:
                wdat_file.write( attachment.data )
            wparts.append( [attachment.name, os.path.getsize( exdir_file ), '', ''] )

        return wparts

    def delete_attachments( self, part, notice ):
        """
        For each attachment that needs to be removed from the message,
        edit the headers of the message and add in the "Retrieve_Attachments.html" file.
        
        This only needs to be run once to avoid multiple copies of the HTML file being attached
        """
        for key, value in part.get_params():
            part.del_param( key )

        del part["content-type"]
        del part["content-disposition"]
        del part["content-transfer-encoding"]

        part["content-disposition"] = "attachment; filename=" + self.remfile
        part["content-type"] = "text/html"
        part.set_payload( notice )

        return part

    def mako_notice( self, fnames ):
        """
        The "Retrieve_Attachments.html" file is generated.using the `Mako Template Engine for Python <http://www.makotemplates.org/>`_.
        
        The template is stored in the *www* subfolder of the main EARS milter folder.  The CSS and image files should be stored on
        an externally-accessible web server.
        
        Each filename is encoded in Unicode and parsed to be valid for URLs (hence, special characters like ampersands and percent signs
        can be part of valid filenames and still downloaded properly).
        
        """
        attach = []
        path = '';

        exp_date = date.today() + timedelta( 30 )
        exp_date = exp_date.strftime( '%B %d, %Y' )

        for fname in fnames:
            regex_dropdir = re.compile( "dropdir/(.*)" )
            r1 = regex_dropdir.search( self.attachDir )
            dirs = r1.groups()
            if not path: path = dirs[0]

            fname[2] = self.fhandling.filesize_notation( fname[1] )
            fname[3] = urllib2.quote( fname[0].encode( 'utf-8' ) )

            fname[0] = self.fhandling.unicodeConvert( fname[0] )

            attach.append( fname )

        EARStemplate = Template( filename = 'www/EARS.html', input_encoding = 'utf-8', output_encoding = 'utf-8', encoding_errors = 'replace' )
        buf = StringIO()
        ctx = Context( buf, filepath = path, attachments = attach, deldate = exp_date )

        try:
            EARStemplate.render_context( ctx )
            return buf.getvalue()
        except:
            return exceptions.html_error_template().render()

## === === ##

class FileSys():
    def __init__( self, msg ):
        """
        **msg** - Message passed directly from the Milter
        
        Variables that are established for this class are:
        
        * **dropDir** - Base folder where attachment files will be stored
        * **min_attach_size** - Minimum attachment size to detach from the message
        * **remfile** - Name of the file with links to removed attachments
        
        """
        self.msg = msg

        self.dropDir = "/dropdir/"
        self.min_attach_size = 163840
        self.remfile = "Retrieve_Attachments.html"

        self.attachDir = self.Dir()

    def Dir( self ):
        """
        Creates a unique folder in the **dropDir** based on the hash of the whole incoming message
        """
        out = tempfile.TemporaryFile()
        self.msg.dump( out )
        out.seek( 0 )
        buf = out.read()
        hashDir = self.hashit( buf )
        attachDir = self.dropDir + hashDir

        if not os.path.isdir( attachDir ):
            os.mkdir( attachDir )

        return attachDir

    def hashit( self, data ):
        """
        Generates a hash for **dropDir** folders and individual files
        """
        sha1 = hashlib.sha1()
        sha1.update( data )

        return sha1.hexdigest()

    def filesize_notation( self, filesize ):
        """
        Determines proper filesize notation (K, M, G) based on mathematical calculation loop
        """
        f_num = float( filesize )
        notation = ['', 'K', 'M', 'G']
        magnitude = 0
        while f_num > 1024:
            f_num = f_num / 1024
            magnitude += 1

        return '{0:.2f} {1}B'.format( f_num, notation[magnitude] )


    def unicodeConvert( self, fname ):
        """
        Convert text to unicode.
        
        This was designed to address issues with Latin-1 (iso-8859-1) encoding
        in addition to other foreign characters.
        """
        normalized = False

#        if '8859-1' in fname:
        if fname.startswith( '=?' ):
            try:
                from email.header import decode_header
                bytes, encoding = decode_header( fname )[0]
                fname = bytes.decode( encoding )
                normalized = True
            except:
                pass

        while normalized == False:
            try:
                fname = unicodedata.normalize( 'NFKD', unicode( fname, 'utf-8' ) ).encode( 'ascii', 'ignore' )
                normalized = True
            except UnicodeDecodeError:
                fname = fname.decode( 'iso-8859-1' )#.encode('utf-8')
                normalized = True
            except UnicodeError:
                fname = unicode( fname.content.strip( codecs.BOM_UTF8 ), 'utf-8' )
                normalized = True
            except TypeError:
                fname = fname.encode( 'utf-8' )
#                normailized = True
        return fname


