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

""" Sqlite unit test module to test sqlite module 
@requires: - sys, unittest, os
           - sqlite module from sqlite.py
"""

import sys
if sys.platform=="cli":
    if sys.version.startswith("2.4"):
        sys.path.append("/usr/lib/python2.4")
    elif sys.version.startswith("2.5"):
        sys.path.append("/usr/lib/python2.5")
    elif sys.version.startswith("2.6"):
        sys.path.append("/usr/lib/python2.6")

from unittest import TestCase
import os

from sqlite import Database
#    Constructor:
#        Database(dbFile)        # e.g. dbFile="path/databaseFileName.s3db"
#    Methods:
#        getRecordsFromDate(fromDate, toDate=None)   #Note: Date is an integer number in Seconds
#        getRecordsStartingWithPath(path)
#        getRecordWithPath(path)
#        updateList(uList)     # uList is a list of (file, eventTime, eventName, isDir) tuples
#        close()
#        _open()      # reopen

testDB = "test.s3db"


class DatabaseTest(TestCase):
    """ Main unit test class """
    def setUp(self):
        """ Setting up database """
        self.db = Database(testDB)
        pass

    def tearDown(self):
        """ Closing datase connection """
        self.db.close()
        try:
            os.remove(testDB)
            pass
        except Exception, e:
            print str(e)

    def writeTestRows(self):
        uList = [("one", 1L, "cre", False),
                 ("two", 2L, "mod", False),
                 ("three", 3L, "start", True)]
        self.db.updateList(uList)

    def testInitCreate(self):
        """ Test creating new database file """
        self.assertTrue(os.path.isfile(testDB))

    def testInit(self):
        """ Test initializing database data """
        self.writeTestRows()
        self.db.close()
        self.db = Database(testDB)

    def testUpdateList(self):
        """ Test update database records
        Calling: B{updateList(uList)}     # uList is a list of (file, eventTime, eventName, isDir) tuples
        """
        uList = [("one", 1L, "cre", False),
                 ("two", 2L, "mod", False),
                 ("three", 3L, "start", True)]
        self.db.updateList(uList)
        uList = [("one", 4L, "mod", False),
                 ("two", 5L, "mod", False),
                 ("three", 3L, "start", True)]
        self.db.updateList(uList)
        rows = self.db.getRecordsFromDate(4)
        self.assertEquals(len(rows), 2)

    def testGetRecordsFromDate(self):
        """ Test retrieving records from database by specifying date
        Calling: B{getRecordsFromDate(fromDate, toDate=None)}   #Note: Date is an integer number in Seconds
        """
        self.writeTestRows()
        rows = self.db.getRecordsFromDate(1)
        self.assertEquals(len(rows), 3)
        rows = self.db.getRecordsFromDate(2)
        self.assertEquals(len(rows), 2)
        rows = self.db.getRecordsFromDate(2, 2)
        self.assertEquals(len(rows), 1)

    def testGetRecordsStartingWithPath(self):
        """ Test retrieving records from database by specifying starting file path
        Calling: B{getRecordsStartingWithPath(path)}
        """
        self.writeTestRows()
        rows = self.db.getRecordsStartingWithPath("t")
        self.assertEquals(len(rows), 2)
        rows = self.db.getRecordsStartingWithPath("o")
        self.assertEquals(rows, [("one", 1L, "cre", False)])

    def testGetRecordWithPath(self):
        """ Test retrieving records from database with the specified file path
        Calling: B{getRecordWithPath(path)}
        """
        self.writeTestRows()
        row = self.db.getRecordWithPath("one")
        self.assertEquals(row, ("one", 1L, "cre", False))
        row = self.db.getRecordWithPath("onex")
        self.assertEquals(row, None)

    def testClose(self):
        """ Test closing database connection """
        self.db.close()



def runUnitTests(locals):
    """ Running unit test main method """
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












