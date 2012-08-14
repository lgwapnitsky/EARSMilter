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

class Attachment(Base):
    __tablename__ = 'attachment'

    id = Column(Integer, primary_key=True)
    filename = Column(VARCHAR(100))
    filesize = Column(Integer)
    fileHash = Column(VARCHAR(100))
    file = Column(BLOB)
    dateReceived = Column(DateTime)
    
    message_id = Column(Integer, ForeignKey('message.id'))


    def __init__(self, id, filename, filesize, fileHash, dateReceived):
        self.id = id
        self.filename = filename
        self.filesize = filesize
        self.fileHash = fileHash
        self.dateReceived = dateReceived

    def __repr__(self):
        return "<Attachment('%s','%s','%s', '%s'>" % (self.filename, self.filesize, self.fileHash, self.dateReceived)


#class Attachment_Link(Base):
#    __tablename__ = "att_link"

#    id = Column(Integer, primary_key=True)
#    fileID = Column(Integer, ForeignKey('attachment.id'))
#    msgID = Column(Integer, ForeignKey('message.id'))

#    def __init__(self, fileID, msgID):
#        self.fileID = fileID
#        self.msgID = msgID

class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True)
    subject = Column(VARCHAR(100))
    headers = Column(VARCHAR(100))
    body = Column(VARCHAR(100))
    dateReceived = Column(DateTime)
    raw_original = Column(LONGTEXT)

#    sender_id = Column(Integer, ForeignKey('sender.id'))
#    recipient_id = Column(Integer, ForeignKey('recipient.id'))
#    attachment_id = Column(Integer, ForeignKey('attachment.id'))

    sender = relationship('Sender', backref=backref('message', order_by=id))
    recipients = relationship('Recipient', backref=backref('message', order_by=id))
    attachments = relationship('Attachment', backref=backref('message', order_by=id))


    def __init__(self, subject, headers, body, dateReceived, raw_original):
        self.subject = subject
        self.headers = headers
        self.body = body
        self.dateReceived = dateReceived
        self.raw_original = raw_original

# class Message_Recipient_Link(Base):
#     __tablename__ = 'mr_link'

#     id = Column(Integer, primary_key=True)
#     recipID = Column(Integer)
#     msgID = Column(Integer)

#     def __init__(self, recipID, msgID):
#         self.recipID = recipID
#         self.msgID = msgID

# class Message_Sender_Link(Base):
#     __tablename__ = 'ms_link'

#     id = Column(Integer, primary_key=True)
#     senderID = Column(Integer)
#     msgID = Column(Integer)

#     def __init__(self, senderID, msgID):
#         self.senderID = senderID
#         self.msgID = msgID

class Recipient(Base):
    __tablename__ = 'recipient'

    id = Column(Integer, primary_key=True)
    emailAddress = Column(VARCHAR(100))

    message_id = Column(Integer, ForeignKey('message.id'))
    

    def __init__(self, emailAddress):
        self.emailAddress = emailAddress

class Sender(Base):
    __tablename__ = 'sender'

    id = Column(Integer, primary_key=True)
    emailAddress = Column(VARCHAR(100))
    
    message_id = Column(Integer, ForeignKey('message.id'))
    
    def __init__(self, emailAddress):
        self.emailAddress = emailAddress

    def __repr__(self):
        return self.emailAddress

        
