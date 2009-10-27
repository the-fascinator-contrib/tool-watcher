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

""" Watcher main class
@requires: sys, os
"""
import sys
try:
    thisModule = sys.modules.get(__name__)
    if hasattr(thisModule, "RunningAsWindowsSevice") and \
            RunningAsWindowsSevice:
        sys.stderr.write("RunninAsWindowsService!!!")
        sys.path.append("C:/program files/ironpython 2.6/Lib")
        sys.path.append("C:/Python26/Lib")
        #
        try:
            import os
            #simpleLogger.WriteInfo(str(dir()))
            #simpleLogger.WriteInfo(rootDir)
            os.chdir(rootDir)
            simpleLogger.WriteInfo("From watcher.py - os.getcwd=%s" % os.getcwd())
            #sys.stderr.write("__name__='%s'" % __name__)
            ipService.LogPythonStdout(True)
            ipService.LogPythonStderr(False)
        except Exception, e:
            sys.stderr.write(str(e))
            simpleLogger.WriteError("ERROR: %s" % str(e))
    elif sys.prefix.startswith("/"):
        if sys.version.startswith("2.5") or sys.version.startswith("2.4"):
            sys.path.append("/usr/lib/python2.5")
except:
    pass
import os

if sys.platform!="cli":
    raise Exception("Currently this program can only run under IronPython (under the Windows or Mono .NET framework)")


sys.path.append("../common")
sys.path.append("../config")

if sys.platform=="cli":
    sys.path.append("../fswatcher/windows")
    from ipFileWatcher import IPFileWatcher as FileWatcher
elif sys.platform=="linux2":
    sys.path.append("../fswatcher/linux")
    #from linuxWatcher import EventWatcherClass as FileWatcher
    from iNotifyWatcher import INotifyWatcher as FileWatcher
else:
    print "No FileWatcher defined for platform '%s'" % sys.platform

from filesystem import FileSystem
from utils import Utils
from config import Config
from controller import Controller
from watchDirectory import WatchDirectory
#   #Controller(db, fileSystem, config, Watcher, WatchDirectory, update=True)
from feeder import Feeder           # Feeder(utils, controller)
from webServer import webServe      # webServe(host, port, feeder) -> shutdownMethod



class Watcher(object):
    def __init__(self):
        os.chdir("../")
        self.programPath = os.getcwd()
        os.chdir("app")
        self.__fs = FileSystem(".")
        self.__utils = Utils()
        self.__config = Config(fileSystem=self.__fs)
        self.__dbFullFileame = None
        self.__db = None
        self.__controller = None
        self.__feeder = None
        self.__webServerShutdownMethod = None
        self.__watcherProgDir = self.__fs.absPath(".").rstrip("/app")
        dbName = self.__config.watcher.get("db", "sqlite")
        sys.path.append("../db/%s" % dbName)
        Database = __import__(dbName).Database
        self.__dbFullFileame = self.__config.watcher.get("dbFile", "queue.db")
        self.__dbFullFileame = self.__fs.absPath(self.__dbFullFileame)


        #------------------------
        stdout = sys.stdout
        stderr = sys.stderr
        # Note: must not output any data when running as a windows server.
        class Writer(object):
            def write(self, data):
                #stdout.write("** "+ data)
                # log
                pass
        if self.__config.daemon:
            w = Writer()
            sys.stdout = w
            sys.stderr = w
        #------------------------
        self.__db = Database(self.__dbFullFileame)
        self.__controller = Controller(self.__db, self.__fs, self.__config, \
                                FileWatcher, WatchDirectory, update=False, \
                                globalIgnoreFilter=self.__globalIgnoreFilter)
        #self.__controller.configChanged(config)
        #self.__config.addReloadWatcher(self.__controller.configChanged)
        configFile = self.__fs.absPath(self.__config.configFile)
        configWatcher = FileWatcher(configFile, self.__fs)
        configWatcher.startWatching()
        def configChanged(file, eventName, **kwargs):
            #file=path, eventTime=eventTime, eventName=eventName, isDir=isDir, walk=False
            if eventName!="del" and file==self.__config.configFile:
                print "configChanged - reloading"
                self.__config.reload()
                self.__controller.configChanged(self.__config)
        configWatcher.addListener(configChanged)

        self.__feeder = Feeder(self.__utils, self.__controller)
        feedservice = self.__config.watcher.get("feedservice", {})
        host = feedservice.get("host", "localhost")
        port = feedservice.get("port", 9000)
        self.__webServerShutdownMethod = webServe(host, port, self.__feeder)
        #------------------------
        print "host='%s', port=%s" % (host, port)
        print "Press enter to exit..."
        raw_input()
        configWatcher.close()
        self.__controller.close()
        self.__webServerShutdownMethod()
        #print self.__controller._getRecordsCount()
        #print self.queue.getFromDate(0)
        sys.stdout = stdout
        sys.stderr = stderr


    def __globalIgnoreFilter(self, fullFile):
        if fullFile==self.__dbFullFileame or fullFile.startswith(self.__watcherProgDir):
            return True
        return False


    def __testListener(self, *args, **kwargs):
        path = kwargs.get("path")
        eTime = kwargs.get("eventTime")
        eName = kwargs.get("eventName")
        isDir = kwargs.get("isDir")
        print path, eTime, eName, isDir



if __name__ == "__main__" or __name__=="<module>":
    sys.stderr.write("Starting watcher...\n")
    watcher = Watcher()


