import traceback, sys, os, time
from time import sleep
from stat import *

#structure: file, time, event, isDir
class Queue(object):
    def __init__(self, db=None, fs=None, programPath=None, test=False):
        #Thread.__init__(self)
        
        self.db = db
        self.__fs = fs
        self.programPath = programPath
        self.test=test
        
    def put(self, *args, **kwargs):
        #self.db.processEvent(*args)
        self.processQueue(*args, **kwargs)
        #self.db.insertFile(*args)
        
    def processQueue(self, *args, **kwargs): 
        eventsToBeUpdated = None
        eventDetail = None
        initialization = False
        renameDir = False
        if "eventDetail" in kwargs.keys():
            eventDetail = kwargs["eventDetail"]
        if "initialization" in kwargs.keys():
            initialization = kwargs["initialization"]
        if "renameDir" in kwargs.keys():
            renameDir = kwargs["renameDir"]
        if eventDetail:
            filePath, timeStamp, eventName, isDir = eventDetail
            #to identify it's file/dir from filesystem instead of url or atom
            if filePath.startswith("file://"):
                eventsToBeUpdated = self.__processFSEvent(filePath, timeStamp, eventName, isDir, initialization, renameDir)
                #self.db.processEvent(eventsToBeUpdated)
        return self.db.processEvent(eventsToBeUpdated)
                
    def __processFSEvent(self, *args):
        filePath, timeStamp, eventName, isDir, initialization, renameDir = args
        listOfFsEvents = []
        fileFullPath = filePath.replace("file://", "")
        if not fileFullPath.startswith(self.programPath):
            #modifiedTime = self.__fs.formatDateTime(timeStamp)
            modifiedTime = timeStamp        
            if initialization:
                if eventName != "stop":
                    eventName = "start"
                listOfFsEvents.append((filePath, modifiedTime, eventName, isDir, initialization))
            else:
                listOfFsEvents.append((filePath, modifiedTime, eventName, isDir, False))
            if self.__fs.isDirectory(fileFullPath):
                if initialization or renameDir:
                    rFiles = []    
                    rDirs = []
                    def callback(path, dirs, files):
                        for dir in dirs:
                            rDirs.append(path + dir)
                        for file in files:
                            rFiles.append(path + file)
                    #start to process child
                    if self.test:
                        rDirs, rFiles = self.__fs.walkDirectory(fileFullPath)
                    else:
                        self.__fs.walker(fileFullPath, callback)
                    for dir in rDirs:
                        #modifiedTime = self.__fs.formatDateTime(os.stat(dir)[ST_MTIME])
                        #modifiedTime = os.stat(dir)[ST_MTIME]
                        #use system time for now
                        dirAbsPath = self.__fs.absPath(dir)
                        listOfFsEvents.append(("file://%s" % dirAbsPath, modifiedTime, eventName, isDir, True))
                    for file in rFiles:
                        #modifiedTime = os.stat(file)[ST_MTIME]
                        #modifiedTime = self.__fs.formatDateTime(os.stat(file)[ST_MTIME])
                        #use system time for now
                        fileAbsPath = self.__fs.absPath(file)
                        listOfFsEvents.append(("file://%s" % fileAbsPath, modifiedTime, eventName, False, True))
                    
                    if initialization and not self.test:
                        #Need to check file against the database.... maybe files/directory is removed when watcher is not working
                        deletedTime = int(time.time())#time.strftime("%Y-%m-%d %H:%M:%S")
                        records = self.db.selectLike(filePath)
                        for record in records:
                            filePath0, modifiedTime0, eventName0, isDir0 = record
                            if isDir0:
                                if filePath0.replace("file://", "") not in rDirs:
                                    listOfFsEvents.append((filePath0, deletedTime, "del", isDir0, False))
                            else:
                                if filePath0.replace("file://", "") not in rFiles:
                                    listOfFsEvents.append((filePath0, deletedTime, "del", isDir0, False))
        return listOfFsEvents

#class QueueHandler(EventHandler):
#    def process_event(self, event):
#        print "event: ", event
#        return 1
    
    
#class ExamineEventHandler(EventHandler):
#    def process_event(self, event):
#        print "------------------"
#        print "Creation Time:    ", time.ctime(event.time)
#        print "Originator's Name:", event.originator
#        print "Original Line:    ", event.data.line,
#        print "Match Object:     ", event.data.match.groups()
#        return 1

        