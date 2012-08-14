#/usr/bin/env python
import EARS_db

from datetime import date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from EARS_db import Attachment, Message, Recipient, Sender
#from EARS_db import Attachment_Link as att_link


daysago = date.today() - timedelta(days=30)

class oldItems():
    def __init__(self):
        Session = sessionmaker()

        engine = create_engine('mysql+mysqldb://root:python@python.dev.wrtdesign.com/EARS', echo=True)
        Session.configure(bind=engine)
        self.session = Session()

        EARS_db.Base.metadata.create_all(engine)


def main():
    items = oldItems()

#    query = items.session.query(Attachment).filter(Attachment.dateReceived < daysago)
#    query.all()


if __name__ == '__main__':
    main()
