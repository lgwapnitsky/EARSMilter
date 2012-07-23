import MySQLdb as mysql
from pprint import pprint

from datetime import date, datetime

class Resend():
    def __init__(self):
        self.sqlHost = "python.dev.wrtdesign.com"
        self.sqlUser = "root"
        self.sqlPass = "python"
        self.sqlNMdb = "EARS"
        self.now = datetime.now()

        self.db = mysql.connect(self.sqlHost,
                                self.sqlUser,
                                self.sqlPass,
                                self.sqlNMdb,
                                compress=True)
        
        self.cursor = self.db.cursor(cursorclass=mysql.cursors.DictCursor)

    def getMessage(self, id):
        GM_SQL = """SELECT id, sender, subject, dateReceived, raw_original FROM message WHERE id=%s"""

        self.cursor.execute(GM_SQL, (id))
        row = self.cursor.fetchone()
        return row

    def recipMessages(self, recipient):
        RecipID_SQL = """SELECT id FROM recipient WHERE emailAddress LIKE %s"""
        RM_SQL="""SELECT * FROM message WHERE message.id IN (select msgID FROM mr_link WHERE recipID=%s)"""

        self.cursor.execute(RecipID_SQL, (recipient + '%'))
        recipID = self.cursor.fetchall()
        for row in recipID:
            self.cursor.execute(RM_SQL, (row['id']))
            for x in self.cursor.fetchall():
                pprint(x['subject'])


if __name__ == '__main__':
    resend = Resend()
    resend.recipMessages('svargas')
    
