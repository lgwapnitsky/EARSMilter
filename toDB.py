import MySQLdb as mysql
import EARS_db as db

from datetime import date, datetime

class toDB():
    def __init__( self ):
        pass

    def close( self ):
        self.db.commit()
        self.db.close()
