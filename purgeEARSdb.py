#!/usr/bin/env python

import database.SQLAlchemy as EARS_db
import os, hashlib

from datetime import date, timedelta, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.SQLAlchemy import *

from argparse import ArgumentParser
import sys

class Options:
    def __init__( self ):
        self.setOptions()
        self.ageAdjust()

    def setOptions( self ):
        parser = ArgumentParser( description = "Purge old messages/attachments from EARS database" )

        quiet_verbose = parser.add_argument_group()

        quiet_verbose.add_argument( '-q', '--quiet', action = 'store_true',
                             help = 'Run without prompting' )

        quiet_verbose.add_argument( '-v', '--verbose', action = 'store_true',
                                   help = 'Verbose output' )

        age_opts = parser.add_argument_group( 'Message/Attachment age options' )
        age_opts.add_argument( '-D', '--days',
                             dest = 'days', type = int, default = 7,
                             help = 'Remove message older than x days (default = 7)' )


        age_opts.add_argument( '-H', '--hours',
                             dest = 'hours', type = int, default = 0 ,
                             help = 'Remove message older than x hours (default = 0)' )

        age_opts.add_argument( '-M', '--minutes',
                             dest = 'minutes', type = int, default = 0 ,
                             help = 'Remove message older than x minutes (default = 0)' )



        database_opts = parser.add_argument_group( 'Database Options (required)' )

        database_opts.add_argument( '-s', '--server', required = True,
                                    dest = 'server', type = str ,
                                    help = "MySQL server name" )
        database_opts.add_argument( '-d', '--database', required = True,
                                    dest = 'database', type = str,
                                    help = 'MySQL database name' )
        database_opts.add_argument( '-u', '--username', required = True,
                                    dest = 'username', type = str,
                                    help = 'MySQL username' )
        database_opts.add_argument( '-p', '--password', required = True,
                                    dest = 'password', type = str,
                                    help = 'MySQL password' )

        self.args = parser.parse_args()

    def ageAdjust( self ):
        args = self.args

        if ( args.hours > 0 or args.minutes > 0 ):
            if ( '-D' or '--days' ) not in sys.argv:
                args.days = 0

            args.days += args.hours // 24
            args.hours = ( args.hours % 24 ) + ( args.minutes // 60 )
            args.minutes = args.minutes % 60

        self.args = args

class Purge:
    def __init__( self , options ):
        args = options.args
        Session = sessionmaker()

        engine = create_engine( 'mysql+mysqldb://%s:%s@%s/%s' % ( args.username,
                                                                  args.password,
                                                                  args.server,
                                                                  args.database )
                               )

        Session.configure( bind = engine )
        self.session = Session()

        EARS_db.Base.metadata.create_all( engine )

        self.now = datetime.now()
        self.delta = self.now - timedelta( days = args.days, hours = args.hours, minutes = args.minutes )
        self.args = args

    def dbQuery( self ):
        session = self.session
        delta = self.delta
        verbose = self.args.verbose
        quiet = self.args.quiet

        query = session.query( Attachment ).filter( Attachment.received <= delta ).all()

        if not quiet:
            att_count = len( query )
            msg_count = sum( len( q.message ) for q in query )

            count_query = ( "%s attachments associated with %s messages" % ( att_count, msg_count ) )
            delete = self.query_yes_no( "Are you sure you want to delete %s" % count_query, "no" )
            if not delete: exit()

        for q in query:
            for message in q.message:
                if message.dateReceived <= delta:
                    if verbose:
                        print ( "deleting %s\nreceived on:%s" % ( message.subject, message.dateReceived ) )
                    session.delete( message )
            if len( q.message ) == 0:
                session.delete( q )
                if verbose:
                    print ( "deleting %s" % q.filename )

    def query_yes_no( self, question, default = "yes" ):
        """Ask a yes/no question via raw_input() and return their answer.
    
        "question" is a string that is presented to the user.
        "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).
    
        The "answer" return value is one of "yes" or "no".
        """
        valid = {"yes":True, "y":True, "ye":True,
                 "no":False, "n":False}
        if default == None:
            prompt = " [y/n] "
        elif default == "yes":
            prompt = " [Y/n] "
        elif default == "no":
            prompt = " [y/N] "
        else:
            raise ValueError( "invalid default answer: '%s'" % default )

        while True:
            sys.stdout.write( question + prompt )
            choice = raw_input().lower()
            if default is not None and choice == '':
                return valid[default]
            elif choice in valid:
                return valid[choice]
            else:
                sys.stdout.write( "Please respond with 'yes' or 'no' "\
                                 "(or 'y' or 'n').\n" )

        return choice

def main():
    purge = Purge( Options() )
    purge.dbQuery()

if __name__ == '__main__':
    main()
