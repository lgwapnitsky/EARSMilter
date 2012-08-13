from sqlalchemy import Table, Column, Integer, String, DateTime, MetaData, ForeignKey
from sqlalchemy.dialects.mysql import \
        BIGINT, BINARY, BIT, BLOB, BOOLEAN, CHAR, DATE, \
        DATETIME, DECIMAL, DECIMAL, DOUBLE, ENUM, FLOAT, INTEGER, \
        LONGBLOB, LONGTEXT, MEDIUMBLOB, MEDIUMINT, MEDIUMTEXT, NCHAR, \
        NUMERIC, NVARCHAR, REAL, SET, SMALLINT, TEXT, TIME, TIMESTAMP, \
        TINYBLOB, TINYINT, TINYTEXT, VARBINARY, VARCHAR, YEAR

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Attachment(Base):
    __tablename__ = 'attachment'

    id = Column(Integer, primary_key=True)
    filename = Column(String)
    filesize = Column(Integer)
    fileHash = Column(String)
    file = Column(BLOB)
    dateReceived = Column(DateTime)

    def __init__(self, id, filename, filesize, fileHash, dateReceived):
        self.id = id
        self.filename = filename
        self.filesize = filesize
        self.fileHash = fileHash
        self.dateReceived = dateReceived

    def __repr__(self):
        return "<Attachment('%s','%s','%s', '%s'>" % (self.filename, self.filesize, self.fileHash, self.dateReceived)


class Attachment_Link(Base):
    __tablename__ = "att_link"

    id = Column(Integer, primary_key=True)
    fileID = Column(Integer)
    msgID = Column(Integer)

    def __init__(self, fileID, msgID):
        self.fileID = fileID
        self.msgID = msgID

class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True)
    subject = Column(String)
    headers = Column(String)
    body = Column(String)
    dateReceived = Column(DateTime)
    raw_original = Column(LONGTEXT)

    def __init__(self, subject, headers, body, dateReceived, raw_original):
        self.subject = subjet
        self.headers = headers
        self.body = body
        self.dateReceived = dateReceived
        self.raw_original = raw_original

class Message_Recipient_Link(Base):
    __tablename__ = 'mr_link'

    id = Column(Integer, primary_key=True)
    recipID = Column(Integer)
    msgID = Column(Integer)

    def __init__(self, recipID, msgID):
        self.recipID = recipID
        self.msgID = msgID

class Message_Sender_Link(Base):
    __tablename__ = 'ms_link'

    id = Column(Integer, primary_key=True)
    senderID = Column(Integer)
    msgID = Column(Integer)

    def __init__(self, senderID, msgID):
        self.senderID = senderID
        self.msgID = msgID

class Recipient(Base):
    __tablename__ = 'recipient'

    id = Column(Integer, primary_key=True)
    emailAddress = Column(String)

    def __init__(self, emailAddress):
        self.emailAddress = emailAddress

class Sender(Base):
    __tablename__ = 'sender'

    id = Column(Integer, primary_key=True)
    emailAddress = Column(String)

    def __init__(self, emailAddress):
        self.emailAddress = emailAddress
