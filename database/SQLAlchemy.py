"""
SQLAlchemy.py - SQLAlchemy Database Definitions
***********************************************

.. module:: SQLAlchemy.py
    :synopsis: EARS database SQLAlchemy Definitions
    
.. moduleauthor:: Larry G. Wapnitsky <larry@qual-ITsystems.com>

.. code-block:: python

    from sqlalchemy.dialects.mysql import
            BIGINT, BINARY, BIT, BLOB, BOOLEAN, CHAR, DATE,
            DATETIME, DECIMAL, DECIMAL, DOUBLE, ENUM, FLOAT, INTEGER,
            LONGBLOB, LONGTEXT, MEDIUMBLOB, MEDIUMINT, MEDIUMTEXT, NCHAR,
            NUMERIC, NVARCHAR, REAL, SET, SMALLINT, TEXT, TIME, TIMESTAMP,
            TINYBLOB, TINYINT, TINYTEXT, VARBINARY, VARCHAR, YEAR

This import is necessary in order to define the specific field type for a MySQL database

"""


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
                Column( 'recipient_id', Integer, ForeignKey( 'recipient.id' ) ),
                Column( 'msg_id', Integer, ForeignKey( 'message.id' ) )
                )
"""
Special table used to create relationships between messages and recipients/attachments.
This table is never referenced specifically in the code other than in the table definition for :py:class:Message.
Links are generated automatically.
"""

ma_link = Table( 'att_link', Base.metadata,
                 Column( 'file_id', Integer, ForeignKey( 'attachment.id' ) ),
                 Column( 'msg_id', Integer, ForeignKey( 'message.id' ) )
                 )
"""
Special table used to create relationships between messages and recipients/attachments.
This table is never referenced specifically in the code other than in the table definition for ``Message``.
Links are generated automatically.
"""


class Attachment( Base ):
    """
    Attachments are stored as binary blobs in the MySQL database for later retrieval
    """

    __tablename__ = "attachment"

    id = Column( Integer, primary_key = True )
    filename = Column( VARCHAR( 255 ) )
    received = Column( DATETIME )
    hash = Column( VARCHAR( 255 ) , unique = True )
    data = Column( LONGBLOB )

    def __init__( self, filename, received, hash, data ):
        """
        Attachment data requires a filename, the date the attachment was received, the filehash and the binary data
        """

        self.filename = filename
        self.received = received
        self.hash = hash
        self.data = data

class Message( Base ):
    """
    Messages contain automatically generated relationships to attachments and recipients via the ``mr_link`` and ``ma_link`` table definitions.
    
    """

    __tablename__ = "message"

    id = Column( Integer, primary_key = True )
    subject = Column( TEXT )
    headers = Column( TEXT )
    body = Column( LONGTEXT )
    dateReceived = Column( DateTime )
    raw_original = Column( LONGTEXT )

    sender_id = Column( Integer, ForeignKey( 'sender.id' ) )

    recipients = relationship( 'Recipient',
                              secondary = mr_link,
                              backref = 'message',
                              lazy = 'dynamic' )

    attachments = relationship( 'Attachment',
                               secondary = ma_link,
                               backref = 'message',
                               lazy = 'dynamic' )

    def __init__( self, subject, headers, body, dateReceived, raw_original ):
        """
        Message data requires a subject, the headers, message body, the date the message was received and a raw copy of the oricinal message
        """
        self.subject = subject
        self.headers = headers
        self.body = body
        self.dateReceived = dateReceived
        self.raw_original = raw_original

class Recipient( Base ):
    """
    Recipient table
    """
    __tablename__ = 'recipient'

    id = Column( Integer, primary_key = True )
    email_address = Column( VARCHAR( 100 ) , unique = True )

    def __init__( self, email_address ):
        """
        A valid email address must be provided for the recipient
        """
        self.email_address = email_address

class Sender( Base ):
    """
    Sender table
    """
    __tablename__ = 'sender'

    id = Column( Integer, primary_key = True )
    email_address = Column( VARCHAR( 100 ) , unique = True )

    messages = relationship( "Message" , backref = 'sender' )

    def __init__( self, email_address ):
        """
        A valid email address must be provided for the recipient
        """

        self.email_address = email_address

