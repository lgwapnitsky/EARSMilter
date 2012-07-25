import MySQLdb as mysql

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
        

        self.cursor.execute(RM_SQL, ('%' + recipient + '%'))
        RM = self.cursor.fetchall()
        for row in RM:
            self.cursor.execute(assoc_SQL, (row['id']))
            assoc = self.cursor.fetchone()

        return (RM, assoc)

    def sendMessage(self, recipient, data):
        from smtplib import SMTP
        server = SMTP('localhost')

        from_addr = '<root@mailproc-test.wrtdesign.com>'
        to_addr=[]
        to_addr.append(recipient)

        

        server.sendmail(from_addr, to_addr, data)
        server.quit()

if __name__ == '__main__':
    resend = Resend()
    RM,assoc = resend.recipMessages('ibu')
    for row in RM:
        print"To:\t%s\nSubj:\t%s\nDate:\t%s\n" % (assoc['emailAddress'], row['subject'], row['dateReceived'])
#        resend.sendMessage(assoc['emailAddress'], row['raw_original'])

