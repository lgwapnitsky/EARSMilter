import MySQLdb as mysql
from datetime import datetime

class db_1():
    def __init__(self):
        self.sqlHost = "python.dev.wrtdesign.com"
        self.sqlUser = "root"
        self.sqlPass = "python"
        self.sqlDB = "EARS"
        
        dbconnect = mysql.connect(self.sqlHost,
                                self.sqlUser,
                                self.sqlPass,
                                self.sqlDB)

        self.cursor = dbconnect.cursor()


    def fot(self, days):
        fot_SQL = """SELECT id, filename, dateReceived FROM attachment WHERE DATE_SUB(CURDATE(), INTERVAL %s DAY) >= dateReceived"""
        fot_msg_SQL = """SELECT COUNT(msgID) FROM att_link WHERE fileID=%s"""
        fot_recip_SQL = """SELECT COUNT(recipID) FROM mr_link WHERE msgID=%s"""

        self.cursor.execute(fot_SQL, (days))
        data = self.cursor.fetchall()
#        for (id, filename, dateReceived) in data:
#            print "(%s) %s : %s" % (id, filename, dateReceived)
        for (id, filename, dateReceived) in data:
            self.cursor.execute(fot_msg_SQL, (id))
            (d2,) = self.cursor.fetchone()
            print "%s is assocated with %s messages in the past %s days" % (filename, d2, days)

            
    def addDates(self):
        noDate_SQL = """SELECT attachment.id, att_link.msgID, message.dateReceived FROM attachment, att_link, message WHERE attachment.dateReceived=%s AND attachment.id = att_link.fileID AND message.id = att_link.msgID"""

        update_SQL = """UPDATE attachment SET dateReceived=%s WHERE id=%s"""

        self.cursor.execute(noDate_SQL, ("0000-00-00 00:00:00"))
        noDate = self.cursor.fetchall()
        for (aid, msgid, dr) in noDate:
            self.cursor.execute(update_SQL, (dr, aid))
#            print aid, dr

            
def main():
    test = db_1()
    test.addDates()
#    test.fot(30)


if __name__ == "__main__":
    main()
