import MySQLdb as mysql

from datetime import date, datetime

class toDB():
    def __init__(self):
        self.sqlHost = "python.dev.wrtdesign.com"
        #sqlHost = "rbl.wrtdesign.com"
        self.sqlUser = "root"
        self.sqlPass = "python"
        self.sqlNMdb = "EARS"
        self.now = datetime.now()

        self.db = mysql.connect(self.sqlHost,
                                self.sqlUser,
                                self.sqlPass,
                                self.sqlNMdb,
                                compress=True)
        
        self.cursor = self.db.cursor()
        


    def NewMessage(self, sender="", subject="", headers="", raw_original=""):
        NM_SQL = """INSERT INTO message(sender, subject, headers, dateReceived, body, raw_original)
                VALUES(%s, %s, %s, %s, "", %s)"""
        
        self.cursor.execute(NM_SQL, (sender, subject, "\n".join(headers), self.now, raw_original))
        
        #return(NM_db, self.cursor.lastrowid, NM_cursor)
        return self.cursor.lastrowid
    
    def AttachmentsToDB(self, data, fname, msgID, fHash):
        ATD_existingFileCount = """SELECT COUNT(fileHash) FROM attachment WHERE fileHash LIKE %s"""
        ATD_existingFileID = """SELECT id FROM attachment WHERE fileHash LIKE %s"""
        ATD_existingFileUpdate = """UPDATE attachment SET dateReceived=%s WHERE id=%s"""
        ATD_newFile = """INSERT INTO attachment(filename, filesize, file, fileHash, dateReceived)
                VALUES(%s, %s, %s, %s, %s)"""
        ATD_link = """INSERT INTO att_link(fileID, msgID) VALUES(%s, %s)"""
        
        self.cursor.execute(ATD_existingFileCount, (fHash))
        (fhCount,) = self.cursor.fetchone()
        if fhCount > 0:
            self.cursor.execute(ATD_existingFileID, (fHash))
            (fileID,) = self.cursor.fetchone()
            self.cursor.execute(ATD_existingFileUpdate, (self.now, fileID))
        else:
            self.cursor.execute(ATD_newFile, (fname, len(data), data, fHash, self.now))
            fileID = self.cursor.lastrowid

            self.cursor.execute(ATD_link, (fileID, msgID))
        
        
        
    def RecipientsToDB(self, msgID, recipients):
        RTD_existingUser = """SELECT COUNT(emailAddress) FROM recipient WHERE emailAddress LIKE %s"""
        RTD_existingUserID = """SELECT id FROM recipient WHERE emailAddress LIKE %s"""
        RTD_newUser = """INSERT INTO recipient(emailAddress) VALUES(%s)"""
        
        
        for r in recipients:
            emailAddress = r[0][1:-1]
            self.cursor.execute(RTD_existingUser, (emailAddress))
            (euCount,) = self.cursor.fetchone()
            if euCount > 0:
                self.cursor.execute(RTD_existingUserID, (emailAddress))
                (recipID,) = self.cursor.fetchone()
            else:
                self.cursor.execute(RTD_newUser, (emailAddress))
                recipID = self.cursor.lastrowid

            RTD_link = """INSERT INTO mr_link(recipID, msgID) VALUES(%s, %s)"""
            self.cursor.execute(RTD_link, (recipID, msgID))
                    
    def BodyToDB(self, msgID, body):
        BTD_SQL = """UPDATE message SET body=%s WHERE id=%s"""
        
        self.cursor.execute(BTD_SQL, (body, msgID))

    def close(self):
        self.db.commit()
        self.db.close()
