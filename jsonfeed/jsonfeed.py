from datetime import datetime
import sys, time

class JsonFeed(object):
    def __init__(self, db, fs, fromDate=None, toDate=None):
        self.__fs = fs
        self.__fromDate = fromDate
        self.__toDate = toDate
        if self.__toDate is None:
            self.__toDate = time.time()
        else:
            self.__toDate = self.__fs.convertGMTToFloat(self.__toDate)
        if self.__fromDate:
            self.__fromDate = self.__fs.convertGMTToFloat(self.__fromDate)
        self.db = db
        self.records = []
        
    def __getRecord(self):
        if self.__fromDate:
            self.records = self.db.getRecordDate(self.__fromDate, self.__toDate)
        else:
            self.records = self.db.select(sortBy="time")
        
    def getFeed(self):
        dict = {}
        for record in self.records:
            filePath, timeStamp, eventName, isDir = record
            if filePath.startswith("file://") and not isDir:
                dict[filePath] = self.__getjSonEntry(timeStamp, eventName)
        return dict
    
    def lastModifiedTimeStamp(self):
        self.__getRecord()
        totalRecords = len(self.records) 
        if totalRecords>0:
            lastRecord = self.records[totalRecords-1]
            filePath, timeStamp, eventName, isDir = lastRecord
            return self.__fs.formatDateTime(timeStamp, True)
        return self.__fs.formatDateTime(time.time(), True)
    
    def __getjSonEntry(self, timeStamp, eventName):
        detail = {}
        detail["time"] = self.__fs.formatDateTime(timeStamp)
        detail["state"] = eventName
        return detail
    
    
