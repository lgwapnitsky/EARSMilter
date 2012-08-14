#/usr/bin/env python
import EARS_db

from datetime import date, timedelta, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from EARS_db import Message, Recipient, Sender
#from EARS_db import Attachment_Link as att_link


daysago = date.today() - timedelta( days = 30 )

class oldItems():
    def __init__( self ):
        Session = sessionmaker()

        engine = create_engine( 'mysql+mysqldb://root:python@python.dev.wrtdesign.com/EARS', echo = True )
        Session.configure( bind = engine )
        self.session = Session()

        EARS_db.Base.metadata.create_all( engine )


def main():
    items = oldItems()
    session = items.session

#    query = items.session.query(Attachment).filter(Attachment.dateReceived < daysago)
#    query.all()

#===============================================================================
#    message = Message( 'subject', 'headers', 'body', datetime.now(), 'raw' )
#    message2 = Message( 'subject2', 'headers2', 'body2', datetime.now(), 'raw2' )
#    message3 = Message( 'subject3', 'headers3', 'body3', datetime.now(), 'raw3' )
#    sender = Sender( email_address = "test@test.com" )
# 
#    query = session.query( Sender ).filter_by( email_address = 'test@test.com' ).first()
#    if not query:
#        message.sender = sender
#    else:
#        message.sender_id = query.id
# 
#    recip_adds = ['bob@one.com', 'fred@two.com', 'bill@three.com']
#    for r in recip_adds:
#        recipient = Recipient( email_address = r )
#        query = session.query( Recipient ).filter_by( email_address = r ).first()
#        if not query:
#            message.recipients.append( recipient )
#        else:
#            query.message.append( message )
#===============================================================================

#    session.add( message )
#    session.commit()

    query = session.query( Message ).filter( Message.sender.has( email_address = 'test@test.com' ) ).all()
    for q in query:
        r = q.recipients
        for i in r:
            print i.email_address

if __name__ == '__main__':
    main()
