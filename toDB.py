import MySQLdb as mysql

from datetime import date, datetime

class toDB():
    def __init__(self):
        self.sqlHost = "python.dev.wrtdesign.com"
        #sqlHost = "rbl.wrtdesign.com"
        self.sqlUser = "root"
        self.sqlPass = "python"
        self.sqlNMdb = "EARS"
        

    def NewMessage(self, sender="", headers=""):
        self.db = mysql.connect(self.sqlHost,
                              self.sqlUser,
                              self.sqlPass,
                              self.sqlNMdb)
        
        self.cursor = self.db.cursor()
        
        NM_SQL = """INSERT INTO message(sender, headers, dateReceived, body)
                VALUES(%s, %s, %s, "")"""
        
        self.cursor.execute(NM_SQL, (sender, "\n".join(headers), datetime.now()))
        
        #return(NM_db, NM_crsr.lastrowid, NM_crsr)
    
    def AttachmentsToDB(self, data, fname, msgID):
        ATD_crsr = self.cursor
        ATD_SQL = """INSERT INTO attachment(filename, filesize, file, msgID)
                VALUES(%s, %s, %s, %s)"""
        
        ATD_crsr.execute(ATD_SQL, (fname, len(data), data, msgID))
        
    def RecipientsToDB(self, msgID, recipients):
        RTD_crsr = self.cursor
        RTD_existingUser = """SELECT COUNT(emailAddress) FROM recipient WHERE emailAddress LIKE %s"""
        RTD_existingUserID = """SELECT id FROM recipient WHERE emailAddress LIKE %s"""
        RTD_newUser = """INSERT INTO recipient(emailAddress) VALUES(%s)"""
        
        print recipients, msgID
        
        for r in recipients:
            emailAddress = r[0][1:-1]
            RTD_crsr.execute(RTD_existingUser, (emailAddress))
            (euCount,) = RTD_crsr.fetchone()
            if euCount > 0:
                RTD_crsr.execute(RTD_existingUserID, (emailAddress))
                (recipID,) = RTD_crsr.fetchone()
            else:
                RTD_crsr.execute(RTD_newUser, (emailAddress))
                recipID = RTD_crsr.lastrowid
                
            RTD_link = """INSERT INTO link(recipID, msgID) VALUES(%s, %s)"""
            RTD_crsr.execute(RTD_link, (recipID, msgID))
                    
    def BodyToDB(self, msgID, body):
        BTD_crsr = self.cursor
        BTD_SQL = """UPDATE message SET body=%s WHERE id=%s"""
        
        BTD_crsr.execute(BTD_SQL, (body, msgID))
        
