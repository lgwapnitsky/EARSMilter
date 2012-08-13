#/usr/bin/env python

from datetime import date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from EARS_db import Attachment, Message, Recipient, Sender
from EARS_db import Attachment_Link as att_link

daysago = date.today() - timedelta(days=30)

class oldItems():
    def __init__(self):
        Session = sessionmaker()

        engine = create_engine('mysql+mysqldb://root:python@python.dev.wrtdesign.com/EARS')
        Session.configure(bind=engine)
        self.session = Session()
        

def main():
    items = oldItems()

    query = items.session.query(Attachment).filter(Attachment.dateReceived < daysago)
    x =query.all()
    for i in x:
        print i
    


if __name__ == '__main__':
    main()
