from sqlalchemy import Table, Column, Integer, String, DateTime, MetaData, ForeignKey

from sqlalchemy.orm import relationship, backref

from sqlalchemy.dialects.mysql import \
        BIGINT, BINARY, BIT, BLOB, BOOLEAN, CHAR, DATE, \
        DATETIME, DECIMAL, DECIMAL, DOUBLE, ENUM, FLOAT, INTEGER, \
        LONGBLOB, LONGTEXT, MEDIUMBLOB, MEDIUMINT, MEDIUMTEXT, NCHAR, \
        NUMERIC, NVARCHAR, REAL, SET, SMALLINT, TEXT, TIME, TIMESTAMP, \
        TINYBLOB, TINYINT, TINYTEXT, VARBINARY, VARCHAR, YEAR

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

mr_link = Table( 'mr_link', Base.metadata,
                Column( 'msg_id', Integer, ForeignKey( 'message.id' ) ),
                Column( 'recipient_id', Integer, ForeignKey( 'recipient.id' ) )
                )


class Message( Base ):
    __tablename__ = "message"

    id = Column( Integer, primary_key = True )
    subject = Column( VARCHAR( 100 ) )
    headers = Column( VARCHAR( 100 ) )
    body = Column( VARCHAR( 100 ) )
    dateReceived = Column( DateTime )
    raw_original = Column( LONGTEXT )

    sender_id = Column( Integer, ForeignKey( 'sender.id' ) )

    recipients = relationship( 'Recipient',
                              secondary = mr_link,
                              backref = 'message',
                              lazy = 'dynamic' )

    def __init__( self, subject, headers, body, dateReceived, raw_original ):
        self.subject = subject
        self.headers = headers
        self.body = body
        self.dateReceived = dateReceived
        self.raw_original = raw_original

class Recipient( Base ):
    __tablename__ = 'recipient'

    id = Column( Integer, primary_key = True )
    email_address = Column( VARCHAR( 100 ) , unique = True )

    def __init__( self, email_address ):
        self.email_address = email_address

class Sender( Base ):
    __tablename__ = 'sender'

    id = Column( Integer, primary_key = True )
    email_address = Column( VARCHAR( 100 ) , unique = True )

    messages = relationship( "Message" , backref = 'sender' )

    def __init__( self, email_address ):
        self.email_address = email_address

