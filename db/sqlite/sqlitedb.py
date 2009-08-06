import os  
import datetime, time
from urllib import quote_plus


#from pysqlite2 import dbapi2 as sqlite3 # if using python 2.4  
import sqlite3  # if using python 2.5 or greater

#NOTE: sqlite has issue with multithreading... sample error:
#SQLite objects created in a thread can only be used in that same thread.The object was created in thread id 1101532080 and this is thread id 1269304240
#to fix: add check_same_thread=False param


class Database(object):
    def __init__(self, dbFile=None):
        
        if dbFile is None:
            #homeDir = os.path.expanduser("~")
            #dbFile = os.path.join(homeDir, "queue.db")
            dbFile = "../db/sqlite/queue.db"
        
        if not os.path.exists(dbFile):
            self.__db = sqlite3.connect(dbFile, check_same_thread=False)
            self.__setupDefaultData()    
        else:
            self.__db = sqlite3.connect(dbFile, check_same_thread=False)
            
    def __setupDefaultData(self):
        """Create default Queue Table"""
        sqlStr = """CREATE TABLE queue
                    (   file    TEXT     PRIMARY KEY,
                        time    TIMESTAMP,
                        event   TEXT, 
                        isDir     BOOL DEFAULT 0
                    );"""
        self.__executeScript(sqlStr)
    
    def __execute(self, sqlStr):  
        """ execute any SQL statement but no return value given """
        cursor = self.__db.cursor()    
        cursor.execute(sqlStr)  
        self.__db.commit()  
        cursor.close()  
    
    def __executeScript(self, sqlStr):  
         """Execute sql Command"""
         cursor = self.__db.cursor()    
         cursor.executescript(sqlStr)
         self.__db.commit()  
         cursor.close()  
        
    def getRecordDate(self, dateFrom, dateTo):
        #sqlStr = "SELECT * FROM queue WHERE time between '%s Z' and '%s Z' ORDER BY time asc" % (dateFrom, dateTo)
        #sqlStr = "SELECT * FROM queue WHERE time between '%s' and '%s' ORDER BY time asc" % (dateFrom, dateTo)
        sqlStr = "SELECT * FROM queue WHERE time > '%s' and time < '%s' ORDER BY time asc" % (dateFrom, dateTo)
        cursor = self.__db.cursor()
        cursor.execute(sqlStr)
        records = cursor.fetchall()
        cursor.close()
        return records
    
    def select(self, **kwargs):
        """Select record from queue table"""
        sortBy = ""
        if "sortBy" in kwargs.keys():
            sortBy = kwargs["sortBy"]
        sqlStr = "SELECT * FROM queue "
        whereStr = ""
        for key in kwargs:
            if key!="sortBy":
                whereStr += "%s='%s'" % (key, kwargs[key])
        if whereStr:
            sqlStr = "%s WHERE %s" % (sqlStr, whereStr)
        if sortBy:
            sqlStr = "%s ORDER BY %s asc" % (sqlStr, sortBy)
        cursor = self.__db.cursor()
        cursor.execute(sqlStr)  
        records = cursor.fetchall()  
        cursor.close()  
        return records  
    
    def selectLike(self, dirPath):
        """Select record from queue table"""
        sqlStr = "SELECT * FROM queue WHERE file like '%s/" % dirPath.rstrip("/") 
        sqlStr += "%'"
        cursor = self.__db.cursor()
        cursor.execute(sqlStr)  
        records = cursor.fetchall()  
        cursor.close()  
        return records  
    
    def processEvent(self, eventList):
        for event in eventList:
            filePath, timeStamp, eventName, isDir, init = event
            filePath = filePath.replace("file://", "")
            filePath = "file://" + quote_plus(filePath)
            if init:  #IF init
                records = self.select(file=filePath) # select based on filePath
                if records==[]:#self.dbData.has_key(filePath):
                    #do insertion here
                    #self.dbData[filePath] = timeStamp, eventName, isDir, init
                    sqlStr = "INSERT INTO queue(file, time, event, isDir) VALUES ('%s', '%s', '%s', %s)" % (filePath, timeStamp, eventName, int(isDir))
                    self.__execute(sqlStr)
                else:
                    if eventName == "start":
                        #if stopMod/stopDel found in the db, update it!
                        filePath0, timeStamp0, eventName0, isDir0 = records[0]
                        if eventName0.startswith("stop"):
                            #do update here
                            #self.dbData[filePath] = timeStamp, eventName, isDir, init
                            sqlStr = "UPDATE queue SET time='%s', event='%s' WHERE file='%s'" % (timeStamp, eventName, filePath)
                            self.__execute(sqlStr)
                    if eventName == "stop":
                        filePath0, timeStamp0, eventName0, isDir0 = records[0]
                        if eventName0=="mod":
                            eventName = "stopMod"
                        elif eventName0=="del":
                            eventName = "stopDel"
                        elif eventName0=="start":
                            eventName = "stop"
                        #do update here
                        #self.dbData[filePath] = timeStamp, eventName, isDir, init
                        sqlStr = "UPDATE queue SET time='%s', event='%s' WHERE file='%s'" % (timeStamp, eventName, filePath)
                        self.__execute(sqlStr)
            else: #not initialization anymore, normally only mod/del event
                #if not exist in db: do insert, if exist, do Update
                records = self.select(file=filePath) #select based on filePath
                #self.dbData[filePath] = timeStamp, eventName, isDir, init
                if records == []:
                    #do insertion
                    sqlStr = "INSERT INTO queue(file, time, event, isDir) VALUES ('%s', '%s', '%s', %s)" % (filePath, timeStamp, eventName, int(isDir))
                else:
                    #do update
                    sqlStr = "UPDATE queue SET time='%s', event='%s' WHERE file='%s'" % (timeStamp, eventName, filePath)
                self.__execute(sqlStr)
                
            if isDir and eventName=="del":
                #need to set the files/dir under this directory to del
                fileDirRecord = self.selectLike(filePath)
                for fileDir in fileDirRecord:
                    filePath0, timeStamp0, eventName0, isDir0 = fileDir
                    sqlStr = "UPDATE queue SET time='%s', event='del' WHERE file='%s'" % (timeStamp, filePath0)
                    self.__execute(sqlStr)

                
    
    
#    def processEvent(self, eventList):
#        for event in eventList:
#            filePath, modifiedTime, eventName, isDir, initialize = event
#            if isDir and eventName=="del":
#                #need to set the files/dir under this directory to del
#                fileDirRecord = self.selectLike(filePath)
#                for fileDir in fileDirRecord:
#                    filePath0, modifiedTime0, eventName0, isDir0 = fileDir
#                    sqlStr = "UPDATE queue SET time='%s', event='del' WHERE file='%s'" % (modifiedTime, filePath0)
#                    self.__execute(sqlStr)
#            
#            #do normal insertion & update
#            sqlStr = "INSERT INTO queue(file, time, event, isDir) VALUES ('%s', '%s', '%s', %s)" % (filePath, modifiedTime, eventName, int(isDir))
#            records = self.select(file=filePath)
#            if records != [] and not initialize:
#                sqlStr = "UPDATE queue SET time='%s', event='%s' WHERE file='%s'" % (modifiedTime, eventName, filePath)
#                self.__execute(sqlStr)
#            elif records == []:
#                self.__execute(sqlStr)
            
