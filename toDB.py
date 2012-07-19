import MySQLdb as mysql

from datetime import date, datetime

class toDB():
    def __init__(self):
        self.sqlHost = "python.dev.wrtdesign.com"
        #sqlHost = "rbl.wrtdesign.com"
        self.sqlUser = "root"
        self.sqlPass = "python"
        self.sqlNMdb = "EARS"
        


    def NewMessage(self, sender="", headers="", raw_original=""):
        self.db = mysql.connect(self.sqlHost,
                              self.sqlUser,
                              self.sqlPass,
                              self.sqlNMdb)
        
        self.cursor = self.db.cursor()
        
        NM_SQL = """INSERT INTO message(sender, headers, dateReceived, body, raw_original)
                VALUES(%s, %s, %s, "", %s)"""
        
        self.cursor.execute(NM_SQL, (sender, "\n".join(headers), datetime.now(), raw_original))
        
        #return(NM_db, NM_crsr.lastrowid, NM_crsr)
        return self.cursor.lastrowid
    
    def AttachmentsToDB(self, data, fname, msgID, fHash):
        ATD_crsr = self.cursor
        ATD_existingFileCount = """SELECT COUNT(fileHash) FROM attachment WHERE fileHash LIKE %s"""
        ATD_existingFileID = """SELECT id FROM attachment WHERE fileHash LIKE %s"""
        ATD_newFile = """INSERT INTO attachment(filename, filesize, file, fileHash)
                VALUES(%s, %s, %s, %s)"""
        ATD_link = """INSERT INTO att_link(fileID, msgID) VALUES(%s, %s)"""
        
        ATD_crsr.execute(ATD_existingFileCount, (fHash))
        (fhCount,) = ATD_crsr.fetchone()
        if fhCount > 0:
            ATD_crsr.execute(ATD_existingFileID, (fHash))
        else:
            ATD_crsr.execute(ATD_newFile, (fname, len(data), data, fHash))

        (fileID,) = ATD_crsr.fetchone()

        ATD_crsr.execute(ATD_link, (fileID, msgID))
        
        
        
    def RecipientsToDB(self, msgID, recipients):
        RTD_crsr = self.cursor
        RTD_existingUser = """SELECT COUNT(emailAddress) FROM recipient WHERE emailAddress LIKE %s"""
        RTD_existingUserID = """SELECT id FROM recipient WHERE emailAddress LIKE %s"""
        RTD_newUser = """INSERT INTO recipient(emailAddress) VALUES(%s)"""
        
        
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

            RTD_link = """INSERT INTO mr_link(recipID, msgID) VALUES(%s, %s)"""
            RTD_crsr.execute(RTD_link, (recipID, msgID))
                    
    def BodyToDB(self, msgID, body):
        BTD_crsr = self.cursor
        BTD_SQL = """UPDATE message SET body=%s WHERE id=%s"""
        
        BTD_crsr.execute(BTD_SQL, (body, msgID))

    def close(self):
        self.db.commit()
        self.db.close()
