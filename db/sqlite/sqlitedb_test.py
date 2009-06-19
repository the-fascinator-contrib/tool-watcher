#!/usr/bin/env python

import sys, os
import unittest
from unittest import TestCase

import os, datetime
from sqlitedb import Database

class SqliteTest(TestCase):
    def setup(self):
        pass
    
    def tearDown(self):
        pass

    def testInit(self):
        db = Database()
        
        homeDir = os.path.expanduser("~")
        dbFile = os.path.join(homeDir, "queue.db")
        self.assertTrue(os.path.exists(dbFile))
            
    def testInsertAndRemoveDirEntries(self):
        homeDir = os.path.expanduser("~")
        dbFile = os.path.join(homeDir, "queue.db")
        if os.path.exists(dbFile):
            os.remove(dbFile)
        
        db = Database()
        files={"/watchDir/dir/": {},
               "/watchDir/dir2/": {},
               "/watchDir/dir/sub_dir/": {}}
        mockFileSystem = MockFileSystem(
                         files=files, 
                         testHomePath="/watchDir")
        
        dirList, fileList = mockFileSystem.walkDirectory("/watchDir")
        #inserting record
        for dir in dirList:
            db.insertDir(dir)
            
        records = db.select()
        for record in records:
            filePath, timeStamp, event = record
            self.assertTrue(files.has_key(filePath))
            self.assertTrue(filePath in dirList)
            self.assertEqual(event, "dir")
        
        #deleting record
        for dir in dirList:
            db.delete(dir, isDir=True)
            
        records = db.select()
        self.assertEqual(len(records), 0)
        
    def testInsertAndRemoveFileEntriesWithModEvent(self):
#UNCOMMENT below code if need to use fresh table        
        homeDir = os.path.expanduser("~")
        dbFile = os.path.join(homeDir, "queue.db")
        if os.path.exists(dbFile):
            os.remove(dbFile)
        
        db = Database()
        files={"/watchDir/file1": {},
               "/watchDir/file2": {},
               "/watchDir/file3": {}}
        mockFileSystem = MockFileSystem(
                         files=files, 
                         testHomePath="/watchDir")
        
        dirList, fileList = mockFileSystem.walkDirectory("/watchDir")
        
        #deleting watchDir folder
        for dir in dirList:
            db.delete(dir)
        
        #mod event for each of the file
        eventName = "mod"    
        for file in fileList:
            db.insertFile(file, eventName, datetime.datetime.now())
        
        records = db.select()
        self.assertEqual(len(records), 3)
        for record in records:
            filePath, timeStamp, event = record
            self.assertTrue(files.has_key(filePath))
            self.assertTrue(filePath in fileList)
            self.assertEqual(event, eventName)
            #self.assertEqual(timeStamp, "0")
        
    def testInsertDeleteWatchFolderEvent(self):
#UNCOMMENT below code if need to use fresh table
        homeDir = os.path.expanduser("~")
        dbFile = os.path.join(homeDir, "queue.db")
        if os.path.exists(dbFile):
            os.remove(dbFile)
        
        db = Database()
        files={"/watchDir/file1": {},
               "/watchDir/file2": {},
               "/watchDir/file3": {}}
        mockFileSystem = MockFileSystem(
                         files=files, 
                         testHomePath="/watchDir")
        
        dirList, fileList = mockFileSystem.walkDirectory("/watchDir")
        
        #deleting watchDir folder
        for dir in dirList:
            db.delete(dir)
        
        #delete event for each of the file
        eventName = "del"    
        for file in fileList:
            db.insertFile(file, eventName, datetime.datetime.now())
        
        records = db.select()
        self.assertEqual(len(records), 3)
        for record in records:
            filePath, timeStamp, event = record
            self.assertTrue(files.has_key(filePath))
            self.assertTrue(filePath in fileList)
            self.assertEqual(event, eventName)
            #self.assertEqual(timeStamp, "0")
    
    #test adding file entry and automatically add directory if the not exist in database
    def testAddFileTogetherWithDirName(self):
        homeDir = os.path.expanduser("~")
        dbFile = os.path.join(homeDir, "queue.db")
        if os.path.exists(dbFile):
            os.remove(dbFile)
        
        db = Database()
        files={"/watchDir/dir/": {},
               "/watchDir/dir/file1": {},
               "/watchDir/file2": {},
               "/watchDir/dir/sub_dir/file1": {}}
        mockFileSystem = MockFileSystem(
                         files=files, 
                         testHomePath="/watchDir")
        
        dirList, fileList = mockFileSystem.walkDirectory("/watchDir")
        dirListExpected = ['/watchDir/', '/watchDir/dir/', '/watchDir/dir/sub_dir/']
        fileListExpected = ['/watchDir/file2', '/watchDir/dir/file1', '/watchDir/dir/sub_dir/file1']
        for dir in dirList:
            db.insertDir(dir)
            
        eventName = "mod"
        for file in fileList:
            db.insertFile(file, "mod", datetime.datetime.now())
        records = db.select()
        self.assertEqual(len(records), 6)
        
        for record in records:
            filePath, timeStamp, event = record
            if event == "dir":
                self.assertTrue(filePath in dirListExpected)
                self.assertEqual(event, "dir")
                self.assertEqual(str(timeStamp), "0")
            else:
                print filePath
                print fileListExpected
                self.assertTrue(filePath in fileListExpected)
                self.assertEqual(event, "mod")
        
        homeDir = os.path.expanduser("~")
        dbFile = os.path.join(homeDir, "queue.db")
        if os.path.exists(dbFile):
            os.remove(dbFile)
        
        #try watching different directory
        db = Database()
        dirList, fileList = mockFileSystem.walkDirectory("/watchDir/dir")
        dirListExpected = ['/watchDir/dir/', '/watchDir/dir/sub_dir/'] 
        fileListExpected = ['/watchDir/dir/file1', '/watchDir/dir/sub_dir/file1']
        for dir in dirList:
            db.insertDir(dir)
            
        eventName = "mod"
        for file in fileList:
            db.insertFile(file, "mod", datetime.datetime.now())
        records = db.select()
        self.assertEqual(len(records), 4)
        
        for record in records:
            filePath, timeStamp, event = record
            if event == "dir":
                self.assertTrue(filePath in dirListExpected)
                self.assertEqual(event, "dir")
                self.assertEqual(str(timeStamp), "0")
            else:
                self.assertTrue(filePath in fileListExpected)
                self.assertEqual(event, "mod")
    
    
    #test deleting directory and make sure:
        #the event of files under this directory will be changed the to "del"
        #the sub dires will be deleted
            #and the event of files under the subdirs will be changed to "del" 
    def testDeleteDirectory(self):
        homeDir = os.path.expanduser("~")
        dbFile = os.path.join(homeDir, "queue.db")
        if os.path.exists(dbFile):
            os.remove(dbFile)
        
        db = Database()
        files={"/watchDir/dir/file1": {},
               "/watchDir/file2": {},
               "/watchDir/dir/sub_dir/file1": {}}
        mockFileSystem = MockFileSystem(
                         files=files, 
                         testHomePath="/watchDir")
        
        dirList, fileList = mockFileSystem.walkDirectory("/watchDir")
        dirListExpected = ['/watchDir/', '/watchDir/dir/', '/watchDir/dir/sub_dir/']
        fileListExpectedWatchDir = ['/watchDir/file2', '/watchDir/dir/file1', '/watchDir/dir/sub_dir/file1']
        
        #insert all the record first....
        for dir in dirList:
            db.insertDir(dir)
            
        eventName = "mod"
        for file in fileList:
            db.insertFile(file, eventName, datetime.datetime.now())
            
        records = db.select()
        self.assertEqual(len(records), 6)
        for record in records:
            filePath, timeStamp, event = record
            if event == "dir":
                self.assertTrue(filePath in dirListExpected)
                self.assertEqual(event, "dir")
                self.assertEqual(str(timeStamp), "0")
            else:
                self.assertTrue(filePath in fileListExpectedWatchDir)
                self.assertEqual(event, "mod")
        
        #now delete /watchDir/dir
        dirList, fileList = mockFileSystem.walkDirectory("/watchDir/dir")
        dirListExpected = ['/watchDir/dir/', '/watchDir/dir/sub_dir/']
        fileListExpected = ['/watchDir/dir/file1', '/watchDir/dir/sub_dir/file1']
        for dir in dirList:
            db.delete(dir)
            
        eventName="del"
        for file in fileList:
            db.insertFile(file, eventName, datetime.datetime.now())
        
        records = db.select()
        self.assertEqual(len(records), 4)
        for record in records:
            filePath, timeStamp, event = record
            if event == "dir":
                self.assertEqual(filePath, "/watchDir/")
                self.assertEqual(event, "dir")
                self.assertEqual(str(timeStamp), "0")
            else:
                self.assertTrue(filePath in fileListExpectedWatchDir)
                if filePath == "/watchDir/file2":
                    self.assertEqual(event, "mod")
                else:
                    self.assertEqual(event, "del")

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
    def __init__(self, files={}, testHomePath="/watchDir"):
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

    def isDir(self, file):
        file = self.absPath(file)
        if self.__files.has_key(file):
            if self.__files[file] == "dir":
                return True
        return False
    
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
                else:
                    dirs = filePath.split("/")
                    dirPath = ""
                    count = 0
                    for dir in dirs:
                        if count != len(dirs)-1:
                            dirPath += "%s/" % dir
                            count += 1
                        else:
                            fileList.append(path + filePath)
                dirPath = path + dirPath
                if dirPath not in dirList:
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
