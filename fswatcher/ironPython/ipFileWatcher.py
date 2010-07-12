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

import clr
from System.IO import FileSystemWatcher, FileSystemEventArgs, WatcherChangeTypes
import time
import os


class IPFileWatcher(object):
    """
    Note: directory to watch must already exist!
    Constructor:
        IPFileWatcher(path, fs)
    Methods:
        addListener(listener)   #listener(path=path, eventTime=eventTime, eventName=eventName, isDir=isDir)
        removeListener(listener)
        startWatching()
        stopWatching()
        close()
    """
    def __init__(self, path, fs):
        self.__fs = fs                    # .absPath() .isFile(), .isDir(), .split()
        self.__fsWatcher = FileSystemWatcher()
        self.__listeners = []
        self.__lastEvent = None           # to help stop double events from occurring
        self.__fsWatcher.EnableRaisingEvents = False
        try:
            self.__fsWatcher.Path = path.replace("/", os.sep)
        except:
            path, filename = path.rsplit("/", 1)
            self.__fsWatcher.Path = path
            self.__fsWatcher.Filter = filename
        self.__fsWatcher.IncludeSubdirectories = True
        self.__fsWatcher.InternalBufferSize = 4096 * 8        # 32K  best kept in 4K blocks
        self.__fsWatcher.Created += self.__onChanged
        self.__fsWatcher.Changed += self.__onChanged
        self.__fsWatcher.Deleted += self.__onChanged
        self.__fsWatcher.Renamed += self.__onRenamed

    
    def addListener(self, listener):
        self.__listeners.append(listener)
    
    
    def removeListener(self, listener):
        if self.__listeners.count(listener)>0:
            self.__listeners.remove(listener)
            return True
        return False
    
    
    def startWatching(self):
        self.__fsWatcher.EnableRaisingEvents = True
    
    
    def stopWatching(self):
        self.__fsWatcher.EnableRaisingEvents = False


    def __onChanged(self, source, e):
        path = e.FullPath.replace("\\", "/")
        eventName = "mod"
        eventTime = int(time.time())
        isDir = None
        try:
            if self.__fs.isDir(path):
                isDir = True
            elif self.__fs.isFile(path):
                isDir = False
        except Exception, e:
            pass
            print " error eventName='%s', path='%s' - %s" % (eventName, path, str(e))
        if e.ChangeType==WatcherChangeTypes.Created:
            eventName = "mod"
        elif e.ChangeType==WatcherChangeTypes.Changed:
            eventName = "mod"
        elif e.ChangeType==WatcherChangeTypes.Deleted:
            eventName = "del"
        print "__onChanged() path='%s', eventName='%s', eventTime='%s'" % (path, eventName, eventTime)
        # to help reduce double events
        if self.__lastEvent==(path, eventName, eventTime):
            return
        self.__lastEvent=(path, eventName, eventTime)
        #
        path = path.replace("\\", "/")
        #if isDir and not path.endswith("/"):
        #    path = path + "/"
        for listener in self.__listeners:
            try:
                listener(file=path, eventTime=eventTime, eventName=eventName, isDir=isDir)
            except Exception, e:
                print "Error calling FileWatcher listener - %s" % str(e)
                pass
    
    
    def __onRenamed(self, source, e):
        print " rename oldName=%s, name=%s" % (e.OldFullPath, e.FullPath)
        #path = self.__fs.split(e.FullPath)[0]
        #This is done to fix the renaming of file or folder within sub directory
        path = e.FullPath.replace(e.Name, "")
        ev = FileSystemEventArgs(WatcherChangeTypes.Created, path, e.Name)
        self.__onChanged(source, ev)
        #path = self.__fs.split(e.OldFullPath)[0]
        #This is done to fix the renaming of file or folder within sub directory
        path = e.OldFullPath.replace(e.OldName, "")
        ev = FileSystemEventArgs(WatcherChangeTypes.Deleted, path, e.OldName)
        self.__onChanged(source, ev)
    
    
    def close(self):
        if self.__fsWatcher is not None:
            self.__fsWatcher.EnableRaisingEvents = False
            self.__fsWatcher.Dispose()
            self.__fsWatcher = None


    def __del__(self):
        close()









