from database import SQLAlchemy as db
from database.SQLAlchemy import *

from datetime import date, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class toDB():
    def __init__( self, username, password, server, database ):
        Session = sessionmaker()

        engine = create_engine( 'mysql+mysqlconnector://%s:%s@%s/%s' % ( username,
                                                                  password,
                                                                  server,
                                                                  database ) )

        Session.configure( bind = engine )
        self.session = Session()

        db.Base.metadata.create_all( engine )

        self.now = datetime.now()

    def newMessage( self, sender, subject, headers, raw_original , recipients ):
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
        session = self.session

        attachment = Attachment( filename, self.now, filehash, data )

        q_attach = session.query( Attachment ).filter_by( hash = filehash ).first()
        if not q_attach:
            self.message.attachments.append( attachment )
        else:
            q_attach.received = self.now
            q_attach.message.append( self.message )


    def close( self ):
        self.session.add( self.message )
        self.session.commit()
        self.session.close()

