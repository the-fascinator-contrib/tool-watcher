#!/usr/bin/python

import sys
if sys.platform=="cli":
    if sys.version.startswith("2.4"):
        sys.path.append("/usr/lib/python2.4")
    elif sys.version.startswith("2.5"):
        sys.path.append("/usr/lib/python2.5")
    elif sys.version.startswith("2.6"):
        sys.path.append("/usr/lib/python2.6")

from unittest import TestCase
import time

if sys.platform=="cli":
    sys.path.append("ironPython")
    from ipFileWatcher import IPFileWatcher as FileWatcher
#elif sys.platform=="linux2":
#    sys.path.append("linux")
#    from linuxWatcher import EventWatcherClass as FileWatcher
else:
    print "No FileWatcher defined for platform '%s'" % sys.platform
#Constructor:
#    IPFileWatcher(path, fs)
#Methods:
#    addListener(listener)  #listener(file=path, eventTime=eventTime, eventName=eventName, isDir=isDir)
#    removeListener(listener)
#    startWatching()
#    stopWatching()
#    close()


class FileWatcherTest(TestCase):
    def setUp(self):
        self.fs = MockFileSystem()
        self.testDir = self.fs.absPath("tempTest.tmp")
        self.fs.writeFile(self.testDir + "/test.txt", "x")

    def tearDown(self):
        self.fs.delete(self.testDir)

    def testFileWatch(self):
        testFile = self.testDir + "/test.txt"
        self.fs.writeFile(testFile, "x")
        fswatcher = FileWatcher(testFile, self.fs)
        d = {}
        fswatcher.startWatching()
        def listener(file, eventTime, eventName, isDir, walk=False):
            #sys.stdout.write("path=%s, eventTime=%s, eventName=%s, isDir=%s\n" % (file, eventTime, eventName, isDir))
            d[file] = eventName
        fswatcher.addListener(listener)
        time.sleep(.2)
        self.fs.writeFile(testFile, "xx")
        time.sleep(.2)
        fswatcher.close()
        self.assertEquals(len(d.keys()), 1)


    def testBasic(self):
        fswatcher = FileWatcher(self.testDir, self.fs)
        fswatcher.startWatching()
        r = {}
        def listener(file, eventTime, eventName, isDir, walk=False):
            #sys.stdout.write("path=%s, eventTime=%s, eventName=%s, isDir=%s\n" % (file, eventTime, eventName, isDir))
            r[file[len(self.testDir)+1:], eventName] = isDir
            if walk:
                r["walk"] = True
        fswatcher.addListener(listener)

        self.fs.writeFile(self.testDir + "/test.txt", "y")
        time.sleep(.1)
        self.fs.writeFile(self.testDir + "/test2.txt", "y")
        time.sleep(.1)
        self.fs.writeFile(self.testDir + "/subdir/one.txt", "y")
        time.sleep(.1)
        self.fs.writeFile(self.testDir + "/subdir/two.txt", "x")
        time.sleep(.1)
        self.fs.delete(self.testDir + "/subdir")
        time.sleep(.2)
        results = r.keys()
        results.sort()
        #for r in results:
        #    print r
        if r.has_key("walk"):
            expected = ["Not filled in yet for linux file watcher"]
        else:
            expected = [('subdir', 'del'), ('subdir', 'mod'), ('subdir/one.txt', 'del'),
            ('subdir/one.txt', 'mod'), ('subdir/two.txt', 'del'), ('subdir/two.txt', 'mod'),
            ('test.txt', 'mod'), ('test2.txt', 'mod')]
        self.assertEquals(results, expected)
        fswatcher.close()


import os
# FileSystem   .absPath() .isFile(), .isDir(), .split()
class MockFileSystem(object):
    def absPath(self, path):
        return os.path.abspath(path)

    def isFile(self, path):
        return os.path.isfile(path)

    def isDir(self, path):
        return os.path.isdir(path)

    def split(self, path):
        return os.path.split(path)

    #
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

    def rename(self, fromPath, toPath):
        fromAbsPath = self.absPath(fromPath)
        toAbsPath = self.absPath(toPath)
        os.rename(fromAbsPath, toAbsPath)

    def readFile(self, file):
        data = None
        try:
            f = open(file, "rb")
            data = f.read()
            f.close()
        except: pass
        return data

    def writeFile(self, file, data):
        self.__makeParent(file)
        try:
            f = open(file, "wb")
            f.write(data)
            f.close()
        except: pass

    def __makeParent(self, path):
        path = self.split(path)[0]
        if self.isDir(path)==True:
            return False
        if self.isFile(path):
            raise Exception("Cannot make directory '%s', already exists as a file!" % path)
        self.makeDirectory(path)
        return True

    def makeDirectory(self, path):
        absPath = self.absPath(path)
        if not os.path.exists(absPath):
            os.makedirs(absPath)



def runUnitTests(locals):
    print "\n\n\n\n"
    if sys.platform=="cli":
        print "---- Testing under IronPython ----"
    else:
        print "---- Testing ----"

    # Run only the selected tests
    args = list(sys.argv)
    sys.argv = sys.argv[:1]
    args.pop(0)
    runTests = args
    runTests = [ i.lower().strip(", ") for i in runTests]
    runTests = ["test"+i for i in runTests if not i.startswith("test")] + \
                [i for i in runTests if i.startswith("test")]
    if runTests!=[]:
        testClasses = [i for i in locals.values() \
                        if hasattr(i, "__bases__") and \
                            (TestCase in i.__bases__)]
        testing = []
        for x in testClasses:
            l = dir(x)
            l = [ i for i in l if i.startswith("test") and callable(getattr(x, i))]
            for i in l:
                if i.lower() not in runTests:
                    delattr(x, i)
                else:
                    testing.append(i)
        x = None
        num = len(testing)
        if num<1:
            print "No selected tests found! - %s" % str(args)[1:-1]
        elif num==1:
            print "Running selected test - %s" % (str(testing)[1:-1])
        else:
            print "Running %s selected tests - %s" % (num, str(testing)[1:-1])
    from unittest import main
    main()


if __name__=="__main__":
    runUnitTests(locals())



