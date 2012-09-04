"""
toDB.py - EARS Milter Database Population
*****************************************

.. module:: toDB.py
    :synopsis: EARS database SQLAlchemy Definitions
    
.. moduleauthor:: Larry G. Wapnitsky <larry@qual-ITsystems.com>
"""

from database import SQLAlchemy as db
from database.SQLAlchemy import *

from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class toDB():
    """
    This class holds all the functions to add/update new messages and attachments to the EARS database.
    """
    def __init__( self, username, password, server, database ):
        """
        To initialize the EARS database population class,  you must provide a valid
        username, password, server and database names.

        The database itself must exist prior to the first execution of EARS, but this class
        will automatically generate the necessary tables.
        
        Currently, EARS is configured only to work with MySQL databases.
        """
        Session = sessionmaker()

        engine = create_engine( 'mysql+mysqldb://%s:%s@%s/%s' % ( username,
                                                                  password,
                                                                  server,
                                                                  database ) )

        Session.configure( bind = engine )
        self.session = Session()

        db.Base.metadata.create_all( engine )

        self.now = datetime.now()

    def newMessage( self, sender, subject, headers, raw_original , recipients ):
        """
        When a message is submitted to EARS, existing sender and recipient e-mail addresses are checked for
        in the databse.  If they do not exist, they are added automatically.
        """
        session = self.session

        message = Message( subject, '\n'.join( map( str, headers ) ), None, self.now, raw_original )

        q_sender = session.query( Sender ).filter_by( email_address = sender ).first()
        if not q_sender:
            message.sender = Sender( email_address = sender )
        else:
            message.sender_id = q_sender.id


        for r in recipients:
            r_add = r[0][1:-1]
            q_recipient = session.query( Recipient ).filter_by( email_address = r_add ).first()
            if not q_recipient:
                message.recipients.append( Recipient( email_address = r_add ) )
            else:
                q_recipient.message.append( message )

        self.message = message

    def addAttachment( self, filename, filehash, data ):
        """
        When attachments are submitted to EARS, the filehash is compared with existing files in the database.
        If the file already exists, the datetime stamp is updated so that the attachment does not get deleted
        sooner than it should be when :program:`purgeEARSdb.py` is run.
        """
        session = self.session

        attachment = Attachment( filename, self.now, filehash, data )

        q_attach = session.query( Attachment ).filter_by( hash = filehash ).first()
        if not q_attach:
            self.message.attachments.append( attachment )
        else:
            q_attach.received = self.now
            q_attach.message.append( self.message )


    def close( self ):
        """
        Commits the message and its attachment(s) to the database
        """
        self.session.add( self.message )

        committed = False

        while not committed:
            try:
                self.session.commit()
                committed = True
            finally:
                self.session.close()

