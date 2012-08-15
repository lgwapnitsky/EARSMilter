import MySQLdb as mysql
import EARS_db as db

from datetime import date, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from EARS_db import Message, Recipient, Sender, Attachment

class toDB():
    def __init__( self ):
        Session = sessionmaker()

        engine = create_engine( 'mysql+mysqldb://root:python@python.dev.wrtdesign.com/EARS' )
        Session.configure( bind = engine )
        self.session = Session()

        db.Base.metadata.create_all( engine )

        self.now = datetime.now()

    def newMessage( self, sender, subject, headers, raw_original , recipients ):
        session = self.session

        message = Message( subject, headers, None, self.now, raw_original )

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

    def close( self ):
        self.session.add( self.message )
        self.session.commit()
        self.session.close()

