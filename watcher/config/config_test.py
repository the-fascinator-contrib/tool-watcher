#!/usr/bin/env python

import sys
import unittest
from unittest import TestCase

import os
from config import Config


class ConfigTest(TestCase):
    # Config
    # Constructor:
    #   Config(configFileSearchPaths=["."], configFileName="config.json", fileSystem=None)
    # Properties:
    #   settings            (default None dictionary)
    #   configFilePath      (the configuration file that is being used)
    # Methods:
    #   reload()
    #   addReloadWatcher(callback)      ( callback method notify(config) )
    #   removeReloadWatcher(callback)
    def setup(self):
        pass

    def tearDown(self):
        pass

    def testConfigFilePath(self):
        mockFileSystem = MockFileSystem(files={"/test/config.json": "{}"}, testHomePath="/test")
        config = Config(fileSystem=mockFileSystem)
        self.assertEquals(config.configFilePath, "/test/config.json")

        mockFileSystem = MockFileSystem(
                    files={"/test/x/config.json":"{}", "/test/config.json": "{}"},
                    testHomePath="/test")
        config = Config([".", "./x"], fileSystem=mockFileSystem)
        self.assertEquals(config.configFilePath, "/test/config.json")
        config = Config(["./x", "."], fileSystem=mockFileSystem)
        self.assertEquals(config.configFilePath, "/test/x/config.json")


    def testSettings(self):
        mockFileSystem = MockFileSystem(
                files={"/test/config.json": "{'key':'value'}"},
                testHomePath="/test")
        config = Config(fileSystem=mockFileSystem)
        settings = config.settings
        self.assertEquals(settings["key"], "value")
        self.assertEquals(settings["missing"], None)


    def testReload(self):
        mockFileSystem = MockFileSystem(
                files={"/test/config.json": "{'key':'value'}"})
        config = Config(fileSystem=mockFileSystem)
        settings = config.settings
        self.assertEquals(settings["key"], "value")

        mockFileSystem.writeFile("/test/config.json", "{'key':'newValue'}")
        config.reload()
        self.assertEquals(settings["key"], "newValue")


    def testReloadWatcher(self):
        mockFileSystem = MockFileSystem(
                files={"/test/config.json": "{'key':'value'}"})
        config = Config(fileSystem=mockFileSystem)
        count = [0]
        def callback(configObj):
            self.assertEquals(configObj, config)
            count[0] += 1
        config.addReloadWatcher(callback)
        #
        mockFileSystem.writeFile("/test/config.json", "{'key':'newValue'}")
        config.reload()
        self.assertEquals(count[0], 1)


class MockFileSystem():
    # Constructor:
    #   MockFileSystem(files={"/test/config.json": "{}"}, testHomePath="/test")
    # Methods:
    #   join(*args)     -> string
    #   absPath(path)   -> string
    #   isFile(file)    -> True|False
    #   readFile(file)  -> data|None
    def __init__(self, files={}, testHomePath="/test"):
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
        return self.__files.has_key(file)

    def readFile(self, file):
        if file is None:
            return None
        file = self.absPath(file)
        return self.__files.get(file, None)

    def writeFile(self, file, data):        # for testing only
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
