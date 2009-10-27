#!/usr/bin/env python
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

import os
import time

import sys
import unittest
from unittest import TestCase

from ipFileWatcher import IPFileWatcher
#    Constructor:
#        IPFileWatcher(fs)
#    Methods:
#        setDirsToBeWatched(paths, startWatching=True)  Note: directories to watch must already exist!
#        addListener(listener)
#        removeListener(listener)
#        startWatching()
#        stopWatching()
#        close()

testDir = "_testDir"

class IPFileWatcherTest(TestCase):
    def delay(self):
        time.sleep(0.2)     # 0.1 not enough, 0.15 ok
        
    def setUp(self):
        self.fs = MockFileSystem()
        self.testDir = self.fs.absPath(testDir) + os.path.sep
        self.fs.delete(self.testDir)
        self.fs.makeDirectory(self.testDir)

    def tearDown(self):
        #self.fs.delete(self.testDir)
        pass

    def testWatcherBasic(self):
        fw = IPFileWatcher(self.fs)
        paths = [self.testDir]
        events = []
        def listener(*args):    # (path, eventName, eventTime):
            events.append(args)
        fw.setDirsToBeWatched(paths)
        fw.addListener(listener)
        
        # assert that we have received a 'mod' event
        events = []
        self.fs.writeFile(self.testDir + "test1.txt", "testing")
        self.assertTrue(self.fs.isFile(self.testDir + "test1.txt"))
        self.delay()
        self.assertEqual("mod", events[-1][1])
        
        # assert that we have received a 'del' and 'cre' events
        events = []        
        self.fs.rename(self.testDir + "test1.txt", self.testDir + "test2.txt")
        self.delay()
        self.assertEqual("del", events[-2][1])
        self.assertEqual(self.testDir + "test1.txt", events[-2][0])
        self.assertEqual("cre", events[-1][1])
        self.assertEqual(self.testDir + "test2.txt", events[-1][0])
        
        # assert that we have received a 'del' event
        events = []
        self.fs.delete(self.testDir + "test2.txt")
        self.delay()
        self.assertTrue(len(events)>0)
        self.assertEqual("del", events[-1][1])
        
        # assert stopped watching
        events = []
        fw.stopWatching()
        self.delay()
        self.fs.writeFile(self.testDir + "test1.txt", "testing")
        self.delay()
        self.assertEqual(len(events), 0)
        
        fw.close()
        fw = None
        print "done"
        

    def testWatcherMultiPaths(self):
        fw = IPFileWatcher(self.fs)
        testPath1 = self.testDir + "one" + os.path.sep
        testPath2 = self.testDir + "two" + os.path.sep
        testPath3 = self.testDir + "three" + os.path.sep
        self.fs.makeDirectory(testPath1)
        self.fs.makeDirectory(testPath2)
        self.fs.makeDirectory(testPath3)
        events = []
        def listener(*args):    # (path, eventName, eventTime):
            events.append(args)
        fw.setDirsToBeWatched([testPath1, testPath2])
        fw.addListener(listener)
        
        events = []
        self.fs.writeFile(testPath1 + "subDir" + os.path.sep + "test.txt", "testing")
        self.fs.writeFile(testPath1 + "test.txt", "testing")
        self.delay()
        self.assertTrue(len(events)>0)
        
        # Test adding and removing of directories
        fw.setDirsToBeWatched([testPath2, testPath3])
        
        events = []
        self.fs.writeFile(testPath1 + "test2.txt", "testing")
        self.delay()
        self.assertTrue(len(events)==0)
        
        events = []
        self.fs.writeFile(testPath2 + "test2.txt", "testing")
        self.delay()
        self.assertTrue(len(events)>0)
        
        events = []
        self.fs.writeFile(testPath3 + "test2.txt", "testing")
        self.delay()
        self.assertTrue(len(events)>0)
    
    
    def testSubDir(self):
        fw = IPFileWatcher(self.fs)
        testPath = self.testDir
        testPath1 = self.testDir + "one" + os.path.sep
        testPath2 = self.testDir + "two" + os.path.sep
        self.fs.makeDirectory(testPath)
        events = []
        def listener(*args):    # (path, eventName, eventTime):
            events.append(args)
        fw.setDirsToBeWatched([testPath])
        fw.addListener(listener)
        
        self.fs.writeFile(testPath1 + "test1.txt", "one")
        self.fs.writeFile(testPath1 + "test2.txt", "two")
        self.delay()
        for event in events:
            print event
        print
        
        events = []
        self.fs.rename(testPath1, testPath2)
        self.delay()
        for event in events:
            print event
        print
        
        # moving a dir to outside of watched location - one delete event
        # moving a dir from outside of watched location - one create event


class MockFileSystem(object):
    def __init__(self):
        pass
    
    def absPath(self, path):
        return os.path.abspath(path)

    def writeFile(self, path, data):
        self.__makeParent(path)
        f = None
        try:
            f = open(self.absPath(path), "wb")
            f.write(data)
        finally:
            if f is not None:
                f.close()
    
    def rename(self, fromPath, toPath):
        fromPath = self.absPath(fromPath)
        toPath = self.absPath(toPath)
        os.rename(fromPath, toPath)
    
    def __makeParent(self, path):
        path = self.split(path)[0]
        if self.isDirectory(path)==True:
            return False
        if self.isFile(path):
            raise Exception("Cannot make directory '%s', already exists as a file!" % path)
        self.makeDirectory(path)
        return True
    
    def makeDirectory(self, path):
        absPath = self.absPath(path)
        if not os.path.exists(absPath):
            os.makedirs(absPath)
    
    def split(self, path):
        return os.path.split(path)

    def isDir(self, path):
        return self.isDirectory(path)
    def isDirectory(self, path):
        absPath = self.absPath(path)
        return os.path.isdir(absPath)
        
    def isFile(self, path):
        absPath = self.absPath(path)
        return os.path.isfile(absPath)
    
    def delete(self, path):
        if self.isFile(path):
            os.remove(path)
        else:
            absPath = self.absPath(path)
            self.__removeDirectory(absPath)
            
    def __removeDirectory(self, dir):
        if os.path.exists(dir):
            files = os.listdir(dir)
            for file in files:
                    file = dir + "/" + file
                    if os.path.isdir(file):
                        self.__removeDirectory(file)
                    else:
                        os.remove(file)
            os.rmdir(dir)
        


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








