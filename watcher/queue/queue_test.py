#!/usr/bin/env python

import sys, os
import unittest
from unittest import TestCase

from queue import Queue
#structure: file, time, event, isDir

class QueueTest(TestCase):
    def setup(self):
        pass
    
    def tearDown(self):
        pass
    
    def testInit(self):
        fs = MockFileSystem()
        q = Queue(fs=fs)
        
    def testInitializingDirStructurWithFiles(self):
        modifiedDate = 1245148106
        files={"/testData/": {"modifiedDate": modifiedDate},
               "/testData/dir/": {"modifiedDate": modifiedDate},
               "/testData/dir2/": {"modifiedDate": modifiedDate},
               "/testData/dir2/file2": {"modifiedDate": modifiedDate},
               "/testData/dir/sub_dir/": {"modifiedDate": modifiedDate}}
        fs = MockFileSystem(files=files)
        q = Queue(fs=fs)
        dirs, _ = fs.walkDirectory()
        
        #when starting to watch a directory, only the watched directory will be passed to the queue
        watchingDir = "/testData/"
        eventsToBeUpdated = q.processQueue(eventDetail=("file://%s/" % fs.absPath(watchingDir), fs.modifiedDate(watchingDir), "mod", True), initialization=True)
        
        expectedEventsToBeUpdated = [('file:///testData/', 1245148106, 'mod', True), 
                                     ('file:///testData/dir/sub_dir', None, 'mod', True), 
                                     ('file:///testData/dir', None, 'mod', True), 
                                     ('file:///testData/dir2', None, 'mod', True), 
                                     ('file:///testData/dir2/file2', 1245148106, 'mod', False)]
        self.assertEqual(eventsToBeUpdated, expectedEventsToBeUpdated)
        
    def testAddNewDirectoryToWatchedDir(self):
        modifiedDate = 1245148106
        files={"/testData/": {"modifiedDate": modifiedDate}}
        
        fs = MockFileSystem(files=files)
        q = Queue(fs=fs)
        
        newDir = "/testData/newDir/"
        eventsToBeUpdated = q.processQueue(eventDetail=("file://%s/" % fs.absPath(newDir), modifiedDate, "mod", True))
        expectedEventsToBeUpdated = [('file:///testData/newDir/', 1245148106, 'mod', True)]
        self.assertEqual(eventsToBeUpdated, expectedEventsToBeUpdated)
    
    def testAddNewFileToDirectory(self):
        modifiedDate = 1245148106
        files={"/testData/": {"modifiedDate": modifiedDate}}
        
        fs = MockFileSystem(files=files)
        q = Queue(fs=fs)
        
        newFile = "/testData/file"
        eventsToBeUpdated = q.processQueue(eventDetail=("file://%s" % fs.absPath(newFile), modifiedDate, "mod", False))
        expectedEventsToBeUpdated = [('file:///testData/file', 1245148106, 'mod', False)]
        self.assertEqual(eventsToBeUpdated, expectedEventsToBeUpdated)
        
    def testDeleteFile(self):
        #when a file is delete.... there will not be any modified date anymore
        files={"/testData/": {"modifiedDate": 0}}
        
        fs = MockFileSystem(files=files)
        q = Queue(fs=fs)
        
        newFile = "/testData/file"
        eventsToBeUpdated = q.processQueue(eventDetail=("file://%s" % fs.absPath(newFile), 0, "del", False))
        expectedEventsToBeUpdated = [('file:///testData/file', 0, 'del', False)]
        self.assertEqual(eventsToBeUpdated, expectedEventsToBeUpdated)


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

    def isDir(self, file):
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
