#
#    Copyright (C) 2009  ADFI,
#    University of Southern Queensland
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

""" Sqlite Module to handle database transaction
@requires: types, sys
 - If running through ironPython, requires cli, System.Data.SQLite and System.Data modules
 - If running using standard Python, requires sqlite3 
"""

from types import IntType
import sys, platform
if sys.platform=="cli":
    import clr
    try:
        if platform.architecture()[0]=="64bit":
            clr.AddReferenceToFileAndPath("64bit/System.Data.SQLite.dll")
        else:
            clr.AddReferenceToFileAndPath("32bit/System.Data.SQLite.dll")
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
    @ivar PathSep: path separator
    """

    PathSep = "/"


    def __init__(self, dbFile):
        """ Database Constructor class
        @param dbFile: database filename 
        @type dbFile: String 
        """
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
        """ Get record list from provided date 
        @param fromDate: From date in number in seconds
        @type fromDate: integer 
        @param toDate: To date in number in seconds, defaulted to None
        @type toDate: integer  
        @return: rows of result
        @rtype: list
        """
        sqlStr = "SELECT * FROM queue WHERE time >= '%s'%s ORDER BY time asc"
        t = ""
        if toDate is not None:
            t = " and time <= '%s'" % toDate
        sqlStr = sqlStr % (fromDate, t)
        rows = self._executeQuery(sqlStr)
        return rows


    def getRecordsStartingWithPath(self, path=""):
        """ Get record list starting with provided path
        @param path: file path name, defaulted to ""
        @type path: String
        @return: rows of result
        @rtype: list  
        """
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
        """ Get record list with provided path
        @param path: file path name
        @type path: String
        @return: list of result if found, otherwise None
        @rtype: list  
        """
        path = path.replace("'", "''").replace("\\", "/")
        sqlStr = "SELECT * FROM queue WHERE file='%s'"
        sqlStr = sqlStr % path
        rows = self._executeQuery(sqlStr)
        if len(rows)>0:
            return rows[0]
        else:
            return None


    def updateList(self, uList):
        """ Update record in database based on the provided uList
        @param uList: uList is a list of (file, eventTime, eventName, isDir) tuples
        @type uList: tuples 
        @return: number of rows updated
        @rtype: integer
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
        """ Close database connection """
        self.__close()


    def _open(self):
        """ Open database connection """
        self.__open()


    def _selectWhere(self, **kwargs):
        """ Retrieve records based on provided query information
        @param kwargs: list of keywords argument provided for select statement
        @param kwargs: dictionary
        @return: list of results if found
        @rtype: list 
        """
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
        """ Destructor to close database connection """
        self.close()


    def __getAddStr(self, file, eventTime, eventName, isDir):
        """ Get insert record to database sql statement
        @param file: file path to be inserted to database
        @type file: String
        @param eventTime: event time when event happened in number in seconds
        @type eventTime: integer     
        @param eventName: event name returned from filesystem watcher
        @type eventName: String
        @param isDir: True if the file path is a directory, otherwise False
        @type isDir: boolean
        @return: sql insert statement
        @rtype: String  
        """
        if type(isDir) is not IntType:
            isDir = int(isDir)
        sqlStr = "INSERT INTO queue(file, time, event, isDir) VALUES('%s', '%s', '%s', '%s');"
        sqlStr = sqlStr % (file, eventTime, eventName, isDir)
        return sqlStr


    def __getUpdateStr(self, file, eventTime, eventName, isDir):
        """ Get update record to database sql statement
        @param file: file path to be inserted to database
        @type file: String
        @param eventTime: event time when event happened in number in seconds
        @type eventTime: integer     
        @param eventName: event name returned from filesystem watcher
        @type eventName: String
        @param isDir: True if the file path is a directory, otherwise False
        @type isDir: boolean
        @return: sql update statement
        @rtype: String  
        """
        if isDir is None:
            sqlStr = "UPDATE queue SET time='%s', event='%s' WHERE file='%s';"
            sqlStr = sqlStr % (eventTime, eventName, file)
        else:
            sqlStr = "UPDATE queue SET time='%s', event='%s', isDir='%s' WHERE file='%s';"
            sqlStr = sqlStr % (eventTime, eventName, int(isDir), file)
        return sqlStr


    def __closeIP(self):
        """ Closing database connection using ironpython sqlite library"""
        if self.__connection is not None:
            self.__connection.Close()
            self.__connection.Dispose()
            self.__connection = None

    def __openIP(self):
        """ Opening database connection using ironpython sqlite library"""
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
                except Exception, e2:
                    print "Error creating file '%s' - %s" % (self.__dbFile, str(e2))
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
        """ Executing database querying statement using ironpython sqlite library 
        @param sqlStr: sql query statement
        @type sqlStr: String
        @return: list of found result
        @rtype: list
        """
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
        """ Executing database update/delete statement using ironpython sqlite library
        @param sqlStr: sql query statement
        @type sqlStr: String
        @return: number of rows updated/deleted
        @rtype: integer
        """
        cmd = self.__connection.CreateCommand()
        cmd.CommandText = sqlStr
        rowsUpdated = cmd.ExecuteNonQuery()
        cmd.Dispose()
        return rowsUpdated


    def __openPy(self):
        """ Connect to database and create necessary queue table information 
        using standard sqlite library"""
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
        """ Close database connection using standard sqlite library"""
        if self.__db is not None:
            self.__db.close()
            self.__db = None

    def __executeQueryPy(self, sqlStr):
        """ Executing database querying statement using standard sqlite library 
        @param sqlStr: sql query statement
        @type sqlStr: String
        @return: list of found result
        @rtype: list
        """
        cursor = self.__db.cursor()
        cursor.execute(sqlStr)
        records = cursor.fetchall()
        cursor.close()
        self.__db.commit()
        return records

    def __executeNonQueryPy(self, sqlStr):
        """ Executing database update/delete statement using standard sqlite library
        @param sqlStr: sql query statement
        @type sqlStr: String
        """
        cursor = self.__db.cursor()
        for s in sqlStr.split("\n"):
            cursor.execute(s)
        cursor.close()
        self.__db.commit()


    #############################################
    def processEvent(self, eventList):
        """ Process Event method (only used when standard sqlite library is used)
        @param eventList: list of events to be processed
        @type eventList: tuple  
        """
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


