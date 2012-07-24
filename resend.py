import MySQLdb as mysql
import operator

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
        RM_SQL="""SELECT *
        FROM message
        WHERE message.id
        IN (
        SELECT msgID
        FROM mr_link
        WHERE recipID
        IN(
        SELECT id
        FROM recipient
        WHERE emailAddress
        LIKE %s
        )
        ) ORDER BY dateReceived"""
        assoc_SQL="""SELECT emailAddress FROM recipient WHERE recipient.id IN (SELECT recipID FROM mr_link WHERE msgID=%s)"""
        

        self.cursor.execute(RM_SQL, (recipient + '%'))
        RM = self.cursor.fetchall()
        for row in RM:
            self.cursor.execute(assoc_SQL, (row['id']))
            assoc = self.cursor.fetchone()
            print"To: %s\nSubject:%s\nDate:%s\n" % (assoc['emailAddress'], row['subject'], row['dateReceived'])

if __name__ == '__main__':
    resend = Resend()
    resend.recipMessages('lcla')
    
