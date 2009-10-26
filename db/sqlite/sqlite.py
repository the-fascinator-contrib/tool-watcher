

from types import IntType
import sys
if sys.platform=="cli":
    import clr
    try:
        clr.AddReference("System.Data.SQLite")
    except Exception, e:
        clr.LoadAssemblyFromFile("System.Data.SQLite.dll")
        clr.AddReference("System.Data.SQLite")
    clr.AddReference("System.Data")
    from System.Data.SQLite import SQLiteConnection
    from System.Data import DataTable
else:
    #from pysqlite2 import dbapi2 as sqlite3 # if using python 2.4
    import sqlite3


class Database(object):
    """
    Constructor:
        Database(dbFile)        # e.g. dbFile="path/databaseFileName.s3db"
    Methods:
        getRecordsFromDate(fromDate, toDate=None)   #Note: Date is an integer number in Seconds
        getRecordsStartingWithPath(path)
        getRecordWithPath(path)
        updateList(uList)     # uList is a list of (file, eventTime, eventName, isDir) tuples
        close()
        _open()      # reopen
    """

    PathSep = "/"


    def __init__(self, dbFile):
        if dbFile is None:
            dbFile = "../db/sqlite/queue.s3db"
        self.__dbFile = dbFile
        self.__db = None
        self.__connection = None
        self.__open = None
        self.__close = None
        self._executeQuery = None
        self._executeNonQuery = None

        if sys.platform=="cli":
            self.__open = self.__openIP
            self.__close = self.__closeIP
            self._executeQuery = self.__executeQueryIP
            self._executeNonQuery = self.__executeNonQueryIP
        else:
            self.__open = self.__openPy
            self.__close = self.__closePy
            self._executeQuery = self.__executeQueryPy
            self._executeNonQuery = self.__executeNonQueryPy
        self.__open()


    def getRecordsFromDate(self, fromDate, toDate=None):
        sqlStr = "SELECT * FROM queue WHERE time >= '%s'%s ORDER BY time asc"
        t = ""
        if toDate is not None:
            t = " and time <= '%s'" % toDate
        sqlStr = sqlStr % (fromDate, t)
        rows = self._executeQuery(sqlStr)
        return rows


    def getRecordsStartingWithPath(self, path=""):
        path = path.replace("'", "''").replace("\\", "/")
        #sqlStr = "SELECT * FROM queue WHERE file like '%s%s%%'"
        #sqlStr = sqlStr % (path.rstrip(self.PathSep), self.PathSep)
        lpath = path
        if not lpath.endswith("/"):
            lpath += "/"
        sqlStr = "SELECT * FROM queue WHERE file like '%s%%' or file='%s'"
        sqlStr = sqlStr % (lpath, path)
        rows = self._executeQuery(sqlStr)
        return rows


    def getRecordWithPath(self, path):
        path = path.replace("'", "''").replace("\\", "/")
        sqlStr = "SELECT * FROM queue WHERE file='%s'"
        sqlStr = sqlStr % path
        rows = self._executeQuery(sqlStr)
        if len(rows)>0:
            return rows[0]
        else:
            return None


    def updateList(self, uList):
        """
            uList is a list of (file, eventTime, eventName, isDir) tuples
        """
        if uList==[]:
            return 0
        sqlStrs = []
        for file, eventTime, eventName, isDir in uList:
            file = file.replace("'", "''").replace("\\", "/")
            sqlStr = "SELECT count(*) FROM queue WHERE file='%s';" % file
            count = self._executeQuery(sqlStr)[0][0]
            if count:
                sqlStrs.append(self.__getUpdateStr(file, eventTime, eventName, isDir))
            else:
                sqlStrs.append(self.__getAddStr(file, eventTime, eventName, isDir))
        sqlStr = "\n".join(sqlStrs)
        rowsUpdated = self._executeNonQuery(sqlStr)
        return rowsUpdated


    def close(self):
        self.__close()


    def _open(self):
        self.__open()


    def _selectWhere(self, **kwargs):
        sqlStr = "SELECT * FROM queue"
        sortBy = kwargs.pop("sortBy", None)
        if len(kwargs)>0:
            whereStr = " WHERE " + " and ".join(["%s='%s'" % (k, v) for k, v in kwargs.iteritems()])
            sqlStr += whereStr
        if sortBy is not None:
            sqlStr += " ORDER BY %s asc" % sortBy
        rows = self._executeQuery(sqlStr)
        return rows


    def __del__(self):
        self.close()


    def __getAddStr(self, file, eventTime, eventName, isDir):
        if type(isDir) is not IntType:
            isDir = int(isDir)
        sqlStr = "INSERT INTO queue(file, time, event, isDir) VALUES('%s', '%s', '%s', '%s');"
        sqlStr = sqlStr % (file, eventTime, eventName, isDir)
        return sqlStr


    def __getUpdateStr(self, file, eventTime, eventName, isDir):
        if isDir is None:
            sqlStr = "UPDATE queue SET time='%s', event='%s' WHERE file='%s';"
            sqlStr = sqlStr % (eventTime, eventName, file)
        else:
            sqlStr = "UPDATE queue SET time='%s', event='%s', isDir='%s' WHERE file='%s';"
            sqlStr = sqlStr % (eventTime, eventName, int(isDir), file)
        return sqlStr


    def __closeIP(self):
        if self.__connection is not None:
            self.__connection.Close()
            self.__connection.Dispose()
            self.__connection = None

    def __openIP(self):
        self.__connection = SQLiteConnection("Data Source=%s" % self.__dbFile)
        try:
            self.__connection.Open()
            sql = "SELECT name FROM sqlite_master WHERE name='queue' and type='table';"
            rows = self._executeQuery(sql)
            name = rows[0][0]
            if name != "queue":
                raise Exception("need to create table")
        except:
            try:
                try:
                    self.__connection.CreateFile(self.__dbFile)
                    self.__connection.Open()
                except:
                    pass
                sqlStr = """CREATE TABLE queue
                    (   file    NVARCHAR(300) PRIMARY KEY,
                        time    INTEGER,
                        event   VARCHAR(8),
                        isDir   BOOLEAN DEFAULT 0
                    );"""
                r = self._executeNonQuery(sqlStr)
            except Exception, e:
                print "Error - %s" % str(e)
        if self.__connection is None:
            self.__connection = SQLiteConnection("Data Source=%s" % self.__dbFile)
            self.__connection.Open()

    def __executeQueryIP(self, sqlStr):
        cmd = self.__connection.CreateCommand()
        cmd.CommandText = sqlStr
        reader = cmd.ExecuteReader()
        rows = []
        for i in reader:
            row = []
            for x in range(i.FieldCount):
                row.append(i.GetValue(x))
            rows.append(row)
        #dt = DataTable()
        #dt.Load(reader)
        reader.Close()
        cmd.Dispose()
        #for row in dt.Rows:
        #    rows.append(tuple(row.ItemArray))
        #dt.Dispose()
        return rows

    def __executeNonQueryIP(self, sqlStr):
        cmd = self.__connection.CreateCommand()
        cmd.CommandText = sqlStr
        rowsUpdated = cmd.ExecuteNonQuery()
        cmd.Dispose()
        return rowsUpdated


    def __openPy(self):
        import os
        if not os.path.exists(self.__dbFile):
            self.__db = sqlite3.connect(self.__dbFile, check_same_thread=False)
            sqlStr = """CREATE TABLE queue
                        (   file    TEXT     PRIMARY KEY,
                            time    INTEGER,
                            event   VARCHAR(8),
                            isDir   BOOLEAN DEFAULT 0
                        );"""
            self._executeNonQuery(sqlStr.replace("\n", " "))
        else:
            self.__db = sqlite3.connect(self.__dbFile, check_same_thread=False)

    def __closePy(self):
        if self.__db is not None:
            self.__db.close()
            self.__db = None

    def __executeQueryPy(self, sqlStr):
        cursor = self.__db.cursor()
        cursor.execute(sqlStr)
        records = cursor.fetchall()
        cursor.close()
        self.__db.commit()
        return records

    def __executeNonQueryPy(self, sqlStr):
        cursor = self.__db.cursor()
        for s in sqlStr.split("\n"):
            cursor.execute(s)
        cursor.close()
        self.__db.commit()


    #############################################
    def processEvent(self, eventList):
        for event in eventList:
            filePath, timeStamp, eventName, isDir, init = event
            if init:  #IF init
                records = self.select(file=filePath) # select based on filePath
                if records==[]:#self.dbData.has_key(filePath):
                    #do insertion here
                    #self.dbData[filePath] = timeStamp, eventName, isDir, init
                    sqlStr = "INSERT INTO queue(file, time, event, isDir) VALUES ('%s', '%s', '%s', %s)"
                    sqlStr = sqlStr % (filePath, timeStamp, eventName, int(isDir))
                    self.__execute(sqlStr)
                else:
                    if eventName == "start":
                        #if stopMod/stopDel found in the db, update it!
                        filePath0, timeStamp0, eventName0, isDir0 = records[0]
                        if eventName0.startswith("stop"):
                            #do update here
                            #self.dbData[filePath] = timeStamp, eventName, isDir, init
                            sqlStr = "UPDATE queue SET time='%s', event='%s' WHERE file='%s'"
                            sqlStr = sqlStr % (timeStamp, eventName, filePath)
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
                        sqlStr = "UPDATE queue SET time='%s', event='%s' WHERE file='%s'"
                        sqlStr = sqlStr % (timeStamp, eventName, filePath)
                        self.__execute(sqlStr)
            else: #not initialization anymore, normally only mod/del event
                #if not exist in db: do insert, if exist, do Update
                records = self.select(file=filePath) #select based on filePath
                #self.dbData[filePath] = timeStamp, eventName, isDir, init
                if records == []:
                    #do insertion
                    sqlStr = "INSERT INTO queue(file, time, event, isDir) VALUES ('%s', '%s', '%s', %s)"
                    sqlStr = sqlStr % (filePath, timeStamp, eventName, int(isDir))
                else:
                    #do update
                    sqlStr = "UPDATE queue SET time='%s', event='%s' WHERE file='%s'"
                    sqlStr = sqlStr % (timeStamp, eventName, filePath)
                self.__execute(sqlStr)

            if isDir and eventName=="del":
                #need to set the files/dir under this directory to del
                fileDirRecord = self.selectLike(filePath)
                for fileDir in fileDirRecord:
                    filePath0, timeStamp0, eventName0, isDir0 = fileDir
                    sqlStr = "UPDATE queue SET time='%s', event='del' WHERE file='%s'"
                    sqlStr = sqlStr % (timeStamp, filePath0)
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


