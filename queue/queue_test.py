#!/usr/bin/env python

import sys, os, time
import unittest
from unittest import TestCase

from queue import Queue
#structure: file, time, event, isDir

class MockDb(object):
    def __init__(self, dbData={}):
        self.dbData = dbData
        pass
    #THIS logic need to be implemented in sqllitedb.py
    def processEvent(self, eventList):
        updatedRecord = []
        for event in eventList:
            filePath, timeStamp, eventName, isDir, init = event
            if init:  #IF init and exist in database, do not do anything. if not exist then insert
                if isDir:
                    filePath = "%s/" % filePath.rstrip("/")
                if not self.dbData.has_key(filePath):
                    self.dbData[filePath] = timeStamp, eventName, isDir, init
                else:
                    if eventName == "start":
                        #if stopMod/stopDel found in the db, update it!
                        timeStamp0, eventName0, isDir0, init0 = self.dbData[filePath]
                        if eventName0.startswith("stop"):
                            self.dbData[filePath] = timeStamp, eventName, isDir, init
                    if eventName == "stop":
                        timeStamp0, eventName0, isDir0, init0 = self.dbData[filePath]
                        if eventName0=="mod":
                            eventName = "stopMod"
                        elif eventName0=="del":
                            eventName = "stopDel"
                        elif eventName0=="start":
                            eventName = "stop"
                        self.dbData[filePath] = timeStamp, eventName, isDir, init
            else: #not initialization anymore, normally only mod/del event
                if isDir:
                    filePath = "%s/" % filePath.rstrip("/")
                #if not exist in db: do insert, if exist, do Update
                self.dbData[filePath] = timeStamp, eventName, isDir, init
        for key in self.dbData:
            timeStamp, eventName, isDir, init = self.dbData[key]
            updatedRecord.append((key, timeStamp, eventName, isDir, init))
        return updatedRecord

class QueueTest(TestCase):
    def setup(self):
        pass
    
    def tearDown(self):
        pass
    
    def testInit(self):
        fs = MockFileSystem()
        q = Queue(fs=fs)
        
    def testInitStartWatchWithNoRecordInDb(self):
        eventTime = int(time.time())
        files={"/testData/": {},
               "/testData/dir/": {},
               "/testData/dir/sub_dir/": {},
               "/testData/dir2/": {},
               "/testData/dir2/file2": {}}
        fs = MockFileSystem(files=files)
        db = MockDb({})
        
        q = Queue(db=db, fs=fs)
        dirs, _ = fs.walkDirectory()
        
        #when starting to watch a directory, only the watched directory will be passed to the queue
        watchingDir = "/testData/"
        updatedEvents = \
            q.processQueue(eventDetail=("file://%s/" % fs.absPath(watchingDir), \
                                        eventTime, "mod", True), initialization=True)
        for event in updatedEvents:
            filePath, timeStamp, eventName, isDir, init = event
            if isDir:
                filePath = "%s/" % filePath.replace("file://", "").rstrip("/")
                self.assertTrue(filePath in files.keys())
            else:
                filePath = "%s" % filePath.replace("file://", "").rstrip("/")
                self.assertTrue(filePath in files.keys())
            self.assertEqual(int(timeStamp), eventTime)
            self.assertEqual(eventName, "start")
            self.assertTrue(init)
        
    def testInitStartWatchWithStartEventExistInDB(self):
        eventTime = int(time.time())
        files={"/testData/": {},
               "/testData/dir/": {},
               "/testData/dir/sub_dir/": {},
               "/testData/dir2/": {},
               "/testData/dir2/file2": {}}
        fs = MockFileSystem(files=files)
        dbRecords= {'file:///testData/dir/sub_dir/': (1245298553, 'start', True, True), 
                    'file:///testData/dir/': (1245298553, 'start', True, True), 
                    'file:///testData/dir2/': (1245298553, 'start', True, True), 
                    'file:///testData/dir2/file2': (1245298553, 'start', False, True), 
                    'file:///testData/': (1245298553, 'start', True, True)}
        db = MockDb(dbRecords)
        
        q = Queue(db=db, fs=fs)
        dirs, _ = fs.walkDirectory()
        
        #when starting to watch a directory, only the watched directory will be passed to the queue
        watchingDir = "/testData/"
        updatedEvents = \
            q.processQueue(eventDetail=("file://%s/" % fs.absPath(watchingDir), \
                                        eventTime, "mod", True), initialization=True)
        for event in updatedEvents:
            filePath, timeStamp, eventName, isDir, init = event
            if isDir:
                filePath = "%s/" % filePath.replace("file://", "").rstrip("/")
                self.assertTrue(filePath in files.keys())
            else:
                filePath = "%s" % filePath.replace("file://", "").rstrip("/")
                self.assertTrue(filePath in files.keys())
            self.assertEqual(int(timeStamp), 1245298553)
            self.assertEqual(eventName, "start")
            self.assertTrue(init)
        
    def testInitStartWatchWithModEventExistInDB(self):
        eventTime = int(time.time())
        files={"/testData/": {},
               "/testData/dir/": {},
               "/testData/dir/sub_dir/": {},
               "/testData/dir2/": {},
               "/testData/dir2/file2": {}}
        fs = MockFileSystem(files=files)
        dbRecords= {'file:///testData/dir/sub_dir/': (1245298553, 'start', True, True), 
                    'file:///testData/dir/': (1245298553, 'start', True, True), 
                    'file:///testData/dir2/': (1245298553, 'start', True, True), 
                    'file:///testData/dir2/file2': (1245298553, 'mod', False, True), #will be ignored "%s/" % filePath.rstrip("/")
                    'file:///testData/': (1245298553, 'start', True, True)}
        db = MockDb(dbRecords)
        
        q = Queue(db=db, fs=fs)
        dirs, _ = fs.walkDirectory()
        
        #when starting to watch a directory, only the watched directory will be passed to the queue
        watchingDir = "/testData/"
        updatedEvents = \
            q.processQueue(eventDetail=("file://%s/" % fs.absPath(watchingDir), \
                                        eventTime, "mod", True), initialization=True)
        for event in updatedEvents:
            filePath, timeStamp, eventName, isDir, init = event
            if isDir:
                filePath = "%s/" % filePath.replace("file://", "").rstrip("/")
                self.assertTrue(filePath in files.keys())
                self.assertEqual(eventName, "start")
            else:
                filePath = "%s" % filePath.replace("file://", "").rstrip("/")
                self.assertTrue(filePath in files.keys())
                self.assertEqual(eventName, "mod")
            self.assertEqual(int(timeStamp), 1245298553)
            self.assertTrue(init)
            
    def testInitStartEventWithStopModStopDelEventInDB(self):
        eventTime = int(time.time())
        files={"/testData/": {},
               "/testData/dir/": {},
               "/testData/dir/sub_dir/": {},
               "/testData/dir2/": {},
               "/testData/dir2/file2": {}}
        fs = MockFileSystem(files=files)
        dbRecords= {'file:///testData/dir/sub_dir/': (1245298553, 'stopMod', True, True), 
                    'file:///testData/dir/': (1245298553, 'stopMod', True, True), 
                    'file:///testData/dir2/': (1245298553, 'stopDel', True, True), 
                    'file:///testData/dir2/file2': (1245298553, 'stopDel', False, True), #will be ignored :)
                    'file:///testData/': (1245298553, 'mod', True, True)}
        db = MockDb(dbRecords)
        
        q = Queue(db=db, fs=fs)
        dirs, _ = fs.walkDirectory()
        
        #when starting to watch a directory, only the watched directory will be passed to the queue
        watchingDir = "/testData/"
        updatedEvents = \
            q.processQueue(eventDetail=("file://%s/" % fs.absPath(watchingDir), \
                                        eventTime, "mod", True), initialization=True)
        
        for event in updatedEvents:
            filePath, timeStamp, eventName, isDir, init = event
            if isDir:
                filePath = "%s/" % filePath.replace("file://", "").rstrip("/")
                if filePath == watchingDir:
                    self.assertEqual(eventName, "mod")
                    self.assertEqual(int(timeStamp), 1245298553)
                else:
                    self.assertEqual(eventName, "start")
                    self.assertEqual(int(timeStamp), eventTime)
                self.assertTrue(filePath in files.keys())
            else:
                filePath = "%s" % filePath.replace("file://", "").rstrip("/")
                self.assertTrue(filePath in files.keys())
                self.assertEqual(eventName, "start")
                self.assertEqual(int(timeStamp), eventTime)
            self.assertTrue(init)
    
    def testStopWatchEventAndNotExistInDb(self):
        eventTime = int(time.time())
        files={"/testData/": {},
               "/testData/dir/": {},
               "/testData/dir/sub_dir/": {},
               "/testData/dir2/": {},
               "/testData/dir2/file2": {}}
        fs = MockFileSystem(files=files)
        db = MockDb({})
        
        q = Queue(db=db, fs=fs)
        dirs, _ = fs.walkDirectory()
        
        #when starting to watch a directory, only the watched directory will be passed to the queue
        watchingDir = "/testData/"
        updatedEvents = \
            q.processQueue(eventDetail=("file://%s/" % fs.absPath(watchingDir), \
                                        eventTime, "stop", True), initialization=True)
        
        for event in updatedEvents:
            filePath, timeStamp, eventName, isDir, init = event
            if isDir:
                filePath = "%s/" % filePath.replace("file://", "").rstrip("/")
            else:
                filePath = "%s" % filePath.replace("file://", "").rstrip("/")
            self.assertTrue(filePath in files.keys())
            self.assertEqual(eventName, "stop")
            self.assertEqual(int(timeStamp), eventTime)
            self.assertTrue(init)
            
    def testStopWatchEventAndLastEventIsMod(self):
        eventTime = int(time.time())
        files={"/testData/": {},
               "/testData/dir/": {},
               "/testData/dir/sub_dir/": {},
               "/testData/dir2/": {},
               "/testData/dir2/file2": {}}
        fs = MockFileSystem(files=files)
        dbRecords= {'file:///testData/dir/sub_dir/': (1245298553, 'mod', True, True), 
                    'file:///testData/dir/': (1245298553, 'mod', True, True), 
                    'file:///testData/dir2/': (1245298553, 'mod', True, True), 
                    'file:///testData/dir2/file2': (1245298553, 'mod', False, True), #will be ignored :)
                    'file:///testData/': (1245298553, 'mod', True, True)}
        db = MockDb(dbRecords)
        
        q = Queue(db=db, fs=fs)
        dirs, _ = fs.walkDirectory()
        
        #when starting to watch a directory, only the watched directory will be passed to the queue
        watchingDir = "/testData/"
        updatedEvents = \
            q.processQueue(eventDetail=("file://%s/" % fs.absPath(watchingDir), \
                                        eventTime, "stop", True), initialization=True)
        
        for event in updatedEvents:
            filePath, timeStamp, eventName, isDir, init = event
            if isDir:
                filePath = "%s/" % filePath.replace("file://", "").rstrip("/")
            else:
                filePath = "%s" % filePath.replace("file://", "").rstrip("/")
            self.assertTrue(filePath in files.keys())
            self.assertEqual(eventName, "stopMod")
            self.assertEqual(int(timeStamp), eventTime)
            self.assertTrue(init)
            
    def testStopWatchEventAndLastEventIsDel(self):
        eventTime = int(time.time())
        files={"/testData/": {},
               "/testData/dir/": {},
               "/testData/dir/sub_dir/": {},
               "/testData/dir2/": {},
               "/testData/dir2/file2": {}}
        fs = MockFileSystem(files=files)
        dbRecords= {'file:///testData/dir/sub_dir/': (1245298553, 'del', True, True), 
                    'file:///testData/dir/': (1245298553, 'del', True, True), 
                    'file:///testData/dir2/': (1245298553, 'del', True, True), 
                    'file:///testData/dir2/file2': (1245298553, 'del', False, True), #will be ignored :)
                    'file:///testData/': (1245298553, 'mod', True, True)}
        db = MockDb(dbRecords)
        
        q = Queue(db=db, fs=fs)
        dirs, _ = fs.walkDirectory()
        
        #when starting to watch a directory, only the watched directory will be passed to the queue
        watchingDir = "/testData/"
        updatedEvents = \
            q.processQueue(eventDetail=("file://%s/" % fs.absPath(watchingDir), \
                                        eventTime, "stop", True), initialization=True)
        
        for event in updatedEvents:
            filePath, timeStamp, eventName, isDir, init = event
            if isDir:
                filePath = "%s/" % filePath.replace("file://", "").rstrip("/")
            else:
                filePath = "%s" % filePath.replace("file://", "").rstrip("/")
            if filePath == watchingDir:
                self.assertEqual(eventName, "stopMod")
            else:
                self.assertEqual(eventName, "stopDel")
            self.assertTrue(filePath in files.keys())
            self.assertEqual(int(timeStamp), eventTime)
            self.assertTrue(init)
            
    def testStopWatchEventAndLastEventIsStart(self):
        eventTime = int(time.time())
        files={"/testData/": {},
               "/testData/dir/": {},
               "/testData/dir/sub_dir/": {},
               "/testData/dir2/": {},
               "/testData/dir2/file2": {}}
        fs = MockFileSystem(files=files)
        dbRecords= {'file:///testData/dir/sub_dir/': (1245298553, 'start', True, True), 
                    'file:///testData/dir/': (1245298553, 'start', True, True), 
                    'file:///testData/dir2/': (1245298553, 'start', True, True), 
                    'file:///testData/dir2/file2': (1245298553, 'start', False, True), #will be ignored :)
                    'file:///testData/': (1245298553, 'start', True, True)}
        db = MockDb(dbRecords)
        
        q = Queue(db=db, fs=fs)
        dirs, _ = fs.walkDirectory()
        
        #when starting to watch a directory, only the watched directory will be passed to the queue
        watchingDir = "/testData/"
        updatedEvents = \
            q.processQueue(eventDetail=("file://%s/" % fs.absPath(watchingDir), \
                                        eventTime, "stop", True), initialization=True)
        
        for event in updatedEvents:
            filePath, timeStamp, eventName, isDir, init = event
            if isDir:
                filePath = "%s/" % filePath.replace("file://", "").rstrip("/")
            else:
                filePath = "%s" % filePath.replace("file://", "").rstrip("/")
            self.assertEqual(eventName, "stop")
            self.assertTrue(filePath in files.keys())
            self.assertEqual(int(timeStamp), eventTime)
            self.assertTrue(init)
        
    def testModOnSingleDirOrFileEventNotExistInDb(self):
        eventTime = int(time.time())
        files={"/testData/": {},
               "/testData/dir/": {},
               "/testData/dir/sub_dir/": {},
               "/testData/dir2/": {},
               "/testData/dir2/file2": {}}
        fs = MockFileSystem(files=files)
        db = MockDb({})
        
        q = Queue(db=db, fs=fs)
        dirs, _ = fs.walkDirectory()
        
        #updating a dir
        updatingDir = "/testData/dir/sub_dir/"
        updatedEvents = \
            q.processQueue(eventDetail=("file://%s/" % fs.absPath(updatingDir), \
                                        eventTime, "mod", True), initialization=False)
        
        filePath, timeStamp, eventName, isDir, init = updatedEvents[0]
        filePath = "%s/" % filePath.replace("file://", "").rstrip("/")
        self.assertEqual(eventName, "mod")
        self.assertTrue(filePath in files.keys())
        self.assertEqual(int(timeStamp), eventTime)
        self.assertFalse(init)

        #updating a file
        updatingFile = "/testData/dir2/file2"
        updatedEvents = \
            q.processQueue(eventDetail=("file://%s" % fs.absPath(updatingFile), \
                                        eventTime, "mod", False), initialization=False)
        filePath, timeStamp, eventName, isDir, init = updatedEvents[1]
        filePath = "%s" % filePath.replace("file://", "")
        self.assertEqual(eventName, "mod")
        self.assertTrue(filePath in files.keys())
        self.assertFalse(isDir)
        self.assertEqual(int(timeStamp), eventTime)
        self.assertFalse(init)
    
    def testModOnSingleDirOrFileEventExistInDb(self):
        eventTime = int(time.time())
        files={"/testData/": {},
               "/testData/dir/": {},
               "/testData/dir/sub_dir/": {},
               "/testData/dir2/": {},
               "/testData/dir2/file2": {}}
        fs = MockFileSystem(files=files)
        dbRecords= {'file:///testData/dir/sub_dir/': (1245298553, 'start', True, False), 
                    'file:///testData/dir/': (1245298553, 'start', True, False), 
                    'file:///testData/dir2/': (1245298553, 'start', True, False), 
                    'file:///testData/dir2/file2': (1245298553, 'start', False, False), 
                    'file:///testData/': (1245298553, 'start', True, False)}
        db = MockDb(dbRecords)
        
        q = Queue(db=db, fs=fs)
        dirs, _ = fs.walkDirectory()
        
        #updating a dir
        updatingDir = "/testData/dir/sub_dir/"
        updatedEvents = \
            q.processQueue(eventDetail=("file://%s/" % fs.absPath(updatingDir), \
                                        eventTime, "mod", True), initialization=False)
        
        #updating a file
        updatingFile = "/testData/dir2/file2"
        updatedEvents = \
            q.processQueue(eventDetail=("file://%s" % fs.absPath(updatingFile), \
                                        eventTime, "mod", False), initialization=False)
        
        for event in updatedEvents:
            filePath, timeStamp, eventName, isDir, init = event
            if isDir:
                filePath = "%s/" % filePath.replace("file://", "").rstrip("/")
            else:
                filePath = "%s" % filePath.replace("file://", "")
            if filePath == updatingDir or filePath == updatingFile:
                self.assertEqual(eventName, "mod")
                self.assertEqual(int(timeStamp), eventTime)
            else:
                self.assertEqual(eventName, "start")
                self.assertEqual(int(timeStamp), 1245298553)
            self.assertTrue(filePath in files.keys())
            self.assertFalse(init)
    
    def testIgnoreDirWhereTheProgramRun(self):
        programPath = "/home/octalina/workspace/watcher2"
        
        eventTime = int(time.time())
        files={"/testData/": {},
               "/testData/dir/": {},
               "/testData/dir/sub_dir/": {},
               "/testData/dir2/": {},
               "/testData/dir2/file2": {}}
        fs = MockFileSystem(files=files)
        dbRecords= {'file:///testData/dir/sub_dir/': (1245298553, 'start', True, False), 
                    'file:///testData/dir/': (1245298553, 'start', True, False), 
                    'file:///testData/dir2/': (1245298553, 'start', True, False), 
                    'file:///testData/dir2/file2': (1245298553, 'start', False, False), 
                    'file:///testData/': (1245298553, 'start', True, False)}
        db = MockDb(dbRecords)
        
        q = Queue(db=db, fs=fs, programPath=programPath)
        dirs, _ = fs.walkDirectory()
        
        #updating a dir
        updatingDir = "/home/octalina/workspace/watcher2/app"
        updatedEvents = \
            q.processQueue(eventDetail=("file://%s/" % fs.absPath(updatingDir), \
                                        eventTime, "mod", True), initialization=False)
        
        #updating a file
        updatingFile = "/home/octalina/workspace/watcher2/app/watcher.py"
        updatedEvents = \
            q.processQueue(eventDetail=("file://%s" % fs.absPath(updatingFile), \
                                        eventTime, "mod", False), initialization=False)
        
        for event in updatedEvents:
            filePath, timeStamp, eventName, isDir, init = event
            if isDir:
                filePath = "%s/" % filePath.replace("file://", "").rstrip("/")
            else:
                filePath = "%s" % filePath.replace("file://", "")
            self.assertTrue(filePath != updatingDir)
            self.assertTrue(filePath != updatingFile)

            self.assertEqual(eventName, "start")
            self.assertEqual(int(timeStamp), 1245298553)


class MockFileSystem():
    # Constructor:
    #   MockFileSystem(files={"/test/config.json": "{}"}, testHomePath="/test")
    # Methods:
    #   join(*args)     -> string
    #   absPath(path)   -> string
    #   isFile(file)    -> True|False
    #   readFile(file)  -> data|None
    #   isFile(file)    -> Boolean
    #   isDir(file)     -> Boolean
    #   walkDirectory() -> list, list
    def __init__(self, files={}, testHomePath="/testData"):
        self.__testHomePath = testHomePath
        self.__files = files        

    def join(self, *args):
        return os.path.join(*args)

    def absPath(self, path):
        if path.startswith("/"):
            return os.path.abspath(path)
        else:
            path = os.path.join(self.__testHomePath, ".", path)
            path = os.path.abspath(path)
            return path

    def isFile(self, file):
        file = self.absPath(file)
        if self.__files.has_key(file):
            if self.__files[file] == "file":
                return True
        return False
    
    def exists(self, file):
        return os.path.exists(file)

    def modifiedDate(self, file):
        if file in self.__files.keys():
            return self.__files[file]["modifiedDate"]
        return None

    def isDirectory(self, file):
        #file = self.absPath(file)
        #if self.__files.has_key(file):
        if file.endswith("/"):
            return True
        return False
    
    def delete(self, file):
        if file in self.__files.keys():
            self.__files.pop(file)
        
    def deleteFile(self, file):
        os.remove(file)
        
    def readFile(self, file):
        if file is None:
            return None
        file = self.absPath(file)
        return self.__files.get(file, None)

    def writeFile(self, file, data):        # for testing only
        file = self.absPath(file)
        self.__files[file] = data

    def walkDirectory(self, path="."):      #for testing only
        if path==".":
            path = self.__testHomePath
        dirList = []
        fileList = []
        for file in self.__files:
            if file.find(path)!=-1:
                filePath = file.replace(path, "")
                if filePath.endswith("/"):
                    dirPath = "%s" % filePath
                elif filePath != path:
                    dirs = filePath.split("/")
                    dirPath = ""
                    count = 0
                    for dir in dirs:
                        if count != len(dirs)-1:
                            dirPath += "%s/" % dir
                            count += 1
                        else:
                            filePath = path + filePath
                            if filePath != path:
                                fileList.append(filePath)
                dirPath = path + dirPath
                if dirPath not in dirList and dirPath != path:
                    dirList.append(dirPath)
        return dirList, fileList  
    
if __name__ == "__main__":
    print "\n\n"
    print "---- Testing ----"
    print
    args = list(sys.argv)
    sys.argv = sys.argv[:1]
    args.pop(0)
    runTests = args
    runTests = [ i.lower().strip(", ") for i in runTests]
    runTests = ["test"+i for i in runTests if not i.startswith("test")] + \
                [i for i in runTests if i.startswith("test")]
    if runTests!=[]:
        testClasses = [i for i in locals().values() \
                        if hasattr(i, "__bases__") and TestCase in i.__bases__]
        for x in testClasses:
            l = dir(x)
            l = [ i for i in l if i.startswith("test") and callable(getattr(x, i))]
            testing = []
            for i in l:
                if i.lower() not in runTests:
                    #print "Removing '%s'" % i
                    delattr(x, i)
                else:
                    #print "Testing '%s'" % i
                    testing.append(i)
        x = None
        print "Running %s selected tests - %s" % (len(testing), str(testing)[1:-1])

    unittest.main()
