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

""" Unit test for config module
@requires: sys, unittest, os, config
"""

import sys
import unittest
from unittest import TestCase
sys.path.append("../common")

import os
from config import Config


class ConfigTest(TestCase):
    """ Config Unit test main class """
    # Config
    # Constructor:
    #   Config(fileSystem, configFileName="config.json", configFileSearchPaths=["."]):
    # Properties:
    #   settings            (default None dictionary)
    #   configFile          (the configuration file that is being used)
    # Methods:
    #   reload()
    #   addReloadWatcher(callback)      ( callback method notify(config) )
    #   removeReloadWatcher(callback)
    
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testConfigFilePath(self):
        """ Test on config file path """
        mockFileSystem = MockFileSystem(files={"/test/config.json": "{}"}, testHomePath="/test")
        config = Config(fileSystem=mockFileSystem)
        self.assertEquals(config.configFile, "/test/config.json")

        mockFileSystem = MockFileSystem(
                    files={"/test/x/config.json":"{}", "/test/config.json": "{}"},
                    testHomePath="/test")
        config = Config(configFileSearchPaths=[".", "./x"], fileSystem=mockFileSystem)
        self.assertEquals(config.configFile, "/test/config.json")
        config = Config(configFileSearchPaths=["./x", "."], fileSystem=mockFileSystem)
        self.assertEquals(config.configFile, "/test/x/config.json")


    def testSettings(self):
        """ Test on config settings """
        mockFileSystem = MockFileSystem(
                files={"/test/config.json": '{"key":"value"}'},
                testHomePath="/test")
        config = Config(fileSystem=mockFileSystem)
        settings = config.settings
        self.assertEquals(settings["key"], "value")
        self.assertEquals(settings["missing"], None)


    def testReload(self):
        """ Test on reloading config file """
        mockFileSystem = MockFileSystem(
                files={"/test/config.json": '{"key":"value"}'})
        config = Config(fileSystem=mockFileSystem)
        settings = config.settings
        self.assertEquals(settings["key"], "value")

        mockFileSystem.writeFile("/test/config.json", '{"key":"newValue"}')
        config.reload()
        self.assertEquals(settings["key"], "newValue")


    def testReloadWatcher(self):
        """ Test on reloading watcher """
        mockFileSystem = MockFileSystem(
                files={"/test/config.json": '{"key":"value"}'})
        config = Config(fileSystem=mockFileSystem)
        count = [0]
        def callback(configObj):
            self.assertEquals(configObj, config)
            count[0] += 1
        config.addReloadWatcher(callback)
        #
        mockFileSystem.writeFile("/test/config.json", '{"key":"newValue"}')
        config.reload()
        self.assertEquals(count[0], 1)


class MockFileSystem():
    """ Mock File System class to accomodate the above config unit test """
    # Constructor:
    #   MockFileSystem(files={"/test/config.json": "{}"}, testHomePath="/test")
    # Methods:
    #   join(*args)     -> string
    #   absPath(path)   -> string
    #   isFile(file)    -> True|False
    #   readFile(file)  -> data|None
    def __init__(self, files={}, testHomePath="/test"):
        """ Constructor method for the MockFileSystem class """
        self.__testHomePath = testHomePath
        self.__files = files

    def join(self, *args):
        """ join the file paths """
        return os.path.join(*args)

    def absPath(self, path):
        """ get absolute path of the file """
        if path.startswith("/"):
            return os.path.abspath(path)
        else:
            path = os.path.join(self.__testHomePath, ".", path)
            path = os.path.abspath(path)
            return path

    def isFile(self, file):
        """ Check if it's a file """
        file = self.absPath(file)
        return self.__files.has_key(file)

    def readFile(self, file):
        """ read content of the file """
        if file is None:
            return None
        file = self.absPath(file)
        data = self.__files.get(file, None)
        return data

    def writeFile(self, file, data):        # for testing only
        """ write the content to config """
        file = self.absPath(file)
        self.__files[file] = data





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
