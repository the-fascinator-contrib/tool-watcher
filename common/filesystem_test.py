#!/usr/bin/env python

import sys
import unittest
from unittest import TestCase

from filesystem import FileSystem

class FileSystemTest(TestCase):
    def setUp(self):
        self.fs = FileSystem(".")

    def tearDown(self):
        pass
    
    def testOne(self):    
        print self.fs.absPath("../watchDir")
        pass
    
    
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
