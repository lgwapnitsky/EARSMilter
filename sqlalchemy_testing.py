#/usr/bin/env python
import EARS_db
import os, hashlib

from datetime import date, timedelta, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from EARS_db import Message, Recipient, Sender, Attachment


daysago = date.today() - timedelta( days = 30 )
now = datetime.now()

class testing():
    def __init__( self ):
        Session = sessionmaker()

        engine = create_engine( 'mysql+mysqldb://root:python@python.dev.wrtdesign.com/EARS' )#, echo = True )
        Session.configure( bind = engine )
        self.session = Session()

        EARS_db.Base.metadata.create_all( engine )


def main():
    items = testing()
    session = items.session


#    query = items.session.query(Attachment).filter(Attachment.dateReceived < daysago)
#    query.all()

    message = Message( 'subject', 'headers', 'body', now, 'raw' )
#    message2 = Message( 'subject2', 'headers2', 'body2', now, 'raw2' )
#    message3 = Message( 'subject3', 'headers3', 'body3', now, 'raw3' )
    sender = Sender( email_address = "test@test.com" )

    query = session.query( Sender ).filter_by( email_address = 'test@test.com' ).first()
    if not query:
        message.sender = sender
    else:
        message.sender_id = query.id

    recip_adds = ['bob@one.com', 'fred@two.com', 'bill@three.com']
    for r in recip_adds:
        recipient = Recipient( email_address = r )
        query = session.query( Recipient ).filter_by( email_address = r ).first()
        if not query:
            message.recipients.append( recipient )
        else:
            query.message.append( message )

    testfile = '/home/lwapnitsky/Downloads/download.zip'
    openfile = open( testfile, 'rb' )
    data = file.read( openfile )
    path, filename = os.path.split( testfile )
    filehash = hashit( data )

    attachment = Attachment( filename, now, filehash, data )

    query = session.query( Attachment ).filter_by( hash = filehash ).first()
    if not query:
        message.attachments.append( attachment )
    else:
        query.received = now
        query.message.append( message )

#    exit()
    #---------------------------------------------------- session.add( message )
    #---------------------------------------------------------- session.commit()
    #----------------------------------------------------------- session.flush()

    query = session.query( Message ).filter( Message.sender.has( email_address = 'test@test.com' ) ).all()
    for q in query:
        r = q.recipients
        for i in r:
            print i.email_address

    query = session.query( Recipient ).filter( Recipient.email_address.contains( 'bob@one.com' ) ).all()
    for q in query:
        for m in q.message:
            print m.subject

def hashit( data ):
    sha1 = hashlib.sha1()
    sha1.update( data )

    return sha1.hexdigest()

if __name__ == '__main__':
    main()
