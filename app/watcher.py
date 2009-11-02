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
import time

if sys.platform!="cli":
    raise Exception("Currently this program can only run under IronPython (under the Windows or Mono .NET framework)")


sys.path.append("../common")
sys.path.append("../config")

if sys.platform=="cli":
    sys.path.append("../fswatcher/ironPython")
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
    def __init__(self, logger):
        os.chdir("../")
        self.programPath = os.getcwd()
        os.chdir("app")
        self.__fs = FileSystem(".")
        self.__utils = Utils()
        self.__config = Config(fileSystem=self.__fs)
        self.__db = None
        self.__controller = None
        self.__feeder = None
        self.__webServerShutdownMethod = None
        self.__logger = logger
        self.__configWatcher = None
        dbName = self.__config.watcher.get("db", "sqlite")
        sys.path.append("../db/%s" % dbName)
        Database = __import__(dbName).Database
        dbFileName = self.__config.watcher.get("dbFile", "queue.db")

        print "Starting file watcher..."
        #------------------------
        self.__db = Database(dbFileName)
        self.__controller = Controller(self.__db, self.__fs, self.__config, \
                                FileWatcher, WatchDirectory, update=False)
        #self.__controller.configChanged(config)
        #self.__config.addReloadWatcher(self.__controller.configChanged)
        self.__configWatcher = FileWatcher(self.__config.configFile, self.__fs)
        self.__configWatcher.startWatching()
        def configChanged(file, eventName, **kwargs):
            #file=path, eventTime=eventTime, eventName=eventName, isDir=isDir, walk=False
            if eventName!="del" and file==self.__config.configFile:
                print "configChanged - reloading"
                self.__config.reload()
                self.__controller.configChanged(self.__config)
        self.__configWatcher.addListener(configChanged)

        self.__feeder = Feeder(self.__utils, self.__controller)
        feedservice = self.__config.watcher.get("feedservice", {})
        self.host = feedservice.get("host", "localhost")
        self.port = feedservice.get("port", 9000)
        self.__webServerShutdownMethod = webServe(self.host, self.port, self.__feeder)
        #------------------------
        print "host='%s', port=%s" % (self.host, self.port)


    @property
    def controller(self):
        return self.__controller

    @property
    def config(self):
        return self.__config
    
    @property
    def configFile(self):
        return self.__config.configFile


    def close(self):
        print "FileWatcher closing"
        self.__configWatcher.close()
        self.__controller.close()
        self.__webServerShutdownMethod()
        print "FileWatcher closed"
        #print self.__controller._getRecordsCount()
        #print self.queue.getFromDate(0)


    def __testListener(self, *args, **kwargs):
        path = kwargs.get("path")
        eTime = kwargs.get("eventTime")
        eName = kwargs.get("eventName")
        isDir = kwargs.get("isDir")
        print path, eTime, eName, isDir



class Logger(object):
    def __init__(self, logFile=""):
        self.__stdout = sys.stdout
        self.__stderr = sys.stderr
        self.__logFile = None
        self.__print = True
        # Note: must not output any data when running as a windows server.
        if hasattr(thisModule, "RunningAsWindowsSevice") and \
                    RunningAsWindowsSevice:
            self.__print = False
        sys.stdout = self
        sys.stderr = self
        try:
            if True:
                self.__logFile = open(logFile, "wb")
        except:
            pass

    def write(self, msg):
        self.__out(msg)

    def info(self, msg):
        self.__out("INFO: " + msg)

    def error(self, msg):
        self.__out("ERROR: " + msg)

    def __out(self, msg):
        try:
            if self.__print:
                self.__stdout.write(msg)
            if self.__logFile is not None:
                self.__logFile.write(msg)
                self.__logFile.flush()
        except:
            pass

    def __del__(self):
        if self.__logFile:
            self.__logFile.close()
            self.__logFile = None


def notify(watcher):
    # watcher.controller.watchDirectories
    print "notify"
    import clr
    clr.AddReference("System.Windows.Forms")
    clr.AddReference("System.Drawing")
    from System.Windows.Forms import NotifyIcon, Application, MenuItem, ContextMenu
    from System.Drawing import Icon
    notify = NotifyIcon()
    notify.Text = "FileWatcher"
    try:
        notify.Icon = Icon("watcher.ico")
    except:
        notify.Icon = Icon("watcher2.ico")
    notify.Visible = True
    notify.BalloonTipTitle = "FileWatcher"
    notify.BalloonTipText = "serving on http://%s:%s" % (watcher.host, watcher.port)
    #for wd in watcher.controller.watchDirectories:
    #    notify.BalloonTipText += "\nwatching: %s" % wd
    def click(sender, eArgs):
        notify.ShowBalloonTip(3000)
    notify.Click += click
    notify.ContextMenu = ContextMenu()
    mItem = MenuItem()
    notify.ContextMenu.MenuItems.Add(mItem)
    mItem.Text = "E&xit"
    def exit(sender, eArgs):
        watcher.close()
        time.sleep(1)
        Application.Exit()
    mItem.Click += exit
    extras(notify.ContextMenu.MenuItems, watcher)
    Application.Run()
    notify.Dispose()

def extras(menuItems, watcher):
    from System.Windows.Forms import MenuItem, MessageBox, FolderBrowserDialog
    config = watcher.config
    if False:
        mItem = MenuItem()
        mItem.Text = "Test"
        menuItems.Add(mItem)
        def mclick(s, e):
            config.settings["watcher"]["watchDirs"]["/temp"] = {}
            print config.settings
            #config.save()
        mItem.Click += mclick
    if True:
        def editConfig(sender, eArgs):
            configFile = watcher.configFile.replace("/", os.sep)
            try:
                if hasattr(os, "system"):
                    os.system(r'"c:\Program Files\Windows NT\Accessories\wordpad.exe" %s' % configFile)
                elif hasattr(os, "startfile"):
                    os.startfile("gedit %s" % configFile)
            except Exception, e:
                print "Failed to start edittor - %s" % str(e)
        mItem2 = MenuItem()
        menuItems.Add(mItem2)
        mItem2.Text = "Edit config file"
        mItem2.Click += editConfig
    if True:
        for wd in watcher.controller.watchDirectories.itervalues():
            def cxt(wd):
                mItem = MenuItem()
                mItem.Text = "Stop watching: %s" % wd.path
                def click(s, e):
                    if mItem.Text.startswith("Stop"):
                        watcher.controller.stopWatching(wd)
                        mItem.Text = "Start watching: %s" % wd.path
                    else:
                        watcher.controller.startWatching(wd)
                        mItem.Text = "Stop watching: %s" % wd.path
                mItem.Click += click
                menuItems.Add(mItem)
            cxt(wd)


if __name__ == "__main__" or __name__=="<module>":
    import time
    logger = Logger("log.txt")
    watcher = Watcher(logger)
    try:
        if len(sys.argv)>1 and sys.argv[1]=="notify":
            raise Exception("notify")
        t = time.time()
        x = raw_input("Press enter to exit...")
        if time.time()-t<.1:
            raise Exception("")
    except:
        if sys.platform=="cli":# and os.sep=="\\":        # Windows
            notify(watcher)
        else:
            while True:
                time.sleep(1)
    watcher.close()


