#!/usr/bin/python
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

import sys
if sys.platform=="cli":
    if sys.version.startswith("2.4"):
        sys.path.append("/usr/lib/python2.4")
    elif sys.version.startswith("2.5"):
        sys.path.append("/usr/lib/python2.5")
    elif sys.version.startswith("2.6"):
        sys.path.append("/usr/lib/python2.6")

from unittest import TestCase

from watchDirectory import WatchDirectory
# Constructor:
#   WatchDirectory(path)
# Properties:
#   path
#   watcher         # a FSWatcher (a placeholder 'tag' only. Not used internally)
#   ignoreFileFilter
#   ignoreDirectories
# Methods:
#   filter(file)
#   addListener(listener)
#   removeListener(listener)
#   updateHandler(file, eventTime, eventName, isDir=False, walk=False)
#   __cmp__
#   __str__


class WatchDirectoryTest(TestCase):
    def testProperties(self):
        wd = WatchDirectory("/test/one")
        self.assertEquals(wd.path, "/test/one/")
        wd.watcher = "x"
        self.assertEquals(wd.watcher, "x")
        wd.ignoreFileFilter = "*.tmp|test"
        self.assertEquals(wd.ignoreFileFilter, "*.tmp|test")
        wd.ignoreDirectories="temp|tmp"
        self.assertEquals(wd.ignoreDirectories, "temp|tmp")

    def testFilter(self):
        wd = WatchDirectory("/test/one/")
        wd.ignoreFileFilter = "*.tmp|test"
        wd.ignoreDirectories="temp|tmp|one"
        self.assertTrue(wd.filter("/test/one/test.txt"))
        self.assertFalse(wd.filter("/test/one/test.tmp"))
        self.assertFalse(wd.filter("/test/one/subdir/one/test.txt"))

    def testListenerUpdateHandler(self):
        #   updateHandler(file, eventTime, eventName, isDir=False, walk=False)
        wd = WatchDirectory("/test/one/")
        wd.ignoreFileFilter = "*.tmp|test"
        wd.ignoreDirectories="temp|tmp|one"
        files = []
        def listener(file, eventTime, eventName, isDir=False, walk=False):
            files.append(file)
        wd.addListener(listener)
        wd.updateHandler("/test/one/file1", 42L, "eName", isDir=False, walk=False)
        wd.updateHandler("/test/one/ignore.tmp", 42L, "eName", isDir=False, walk=False)
        wd.updateHandler("/test/one/temp/ignore", 42L, "eName", isDir=False, walk=False)
        wd.updateHandler("/test/one/subdir/file1", 42L, "eName", isDir=False, walk=False)
        self.assertEquals(len(files), 2)


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



