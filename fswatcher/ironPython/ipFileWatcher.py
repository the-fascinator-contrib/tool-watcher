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
from os import sep as osPathSeperator


class IPFileWatcher(object):
    """
    Note: directory to watch must already exist!
    Constructor:
        IPFileWatcher(path, fs, getChildrenOf=None, getRecordWithPath=None)
    Methods:
        addListener(listener)   #listener(file=path, eventTime=eventTime, eventName=eventName, isDir=isDir)
        removeListener(listener)
        startWatching()
        stopWatching()
        close()
    """
    def __init__(self, path, fs, getChildrenOf=None, getRecordWithPath=None):
        self.__fs = fs                    # .absPath() .isFile(), .isDir(), .split()
        self.__getChildrenOf = getChildrenOf
        self.__getRecordWithPath = getRecordWithPath
        self.__fsWatcher = FileSystemWatcher()
        self.__listeners = []
        self.__lastEvent = None           # to help stop double events from occurring
        self.__fsWatcher.EnableRaisingEvents = False
        try:
            self.__fsWatcher.Path = path.replace("/", osPathSeperator)
        except:
            path, filename = path.rsplit("/", 1)
            self.__fsWatcher.Path = path
            self.__fsWatcher.Filter = filename
        self.__fsWatcher.IncludeSubdirectories = True
        self.__fsWatcher.InternalBufferSize = 4096 * 8        # 32K  best kept in 4K blocks
        self.__fsWatcher.Created += self.__onCreated
        self.__fsWatcher.Changed += self.__onChanged
        self.__fsWatcher.Deleted += self.__onDeleted
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
    
    
    def __onCreated(self, source, e):
        #print "Created %s" % e.FullPath
        self.__onChanged(source, e)
        if self.__fs.isDir(e.FullPath):
            def callback(path, dirs, files):
                path = path.rstrip("/")
                for dir in dirs:
                    ev = FileSystemEventArgs(WatcherChangeTypes.Created, path, dir)
                    self.__onChanged(source, ev)
                for file in files:
                    ev = FileSystemEventArgs(WatcherChangeTypes.Created, path, file)
                    self.__onChanged(source, ev)
            self.__fs.walker(e.FullPath, callback)
    
    
    def __onDeleted(self, source, e):
        #print "Deleted %s" % e.FullPath
        if callable(self.__getChildrenOf):
            # get all children of e.FullPath (which does not end in a \)
            path = e.FullPath.replace("\\", "/")+"/"
            children = self.__getChildrenOf(path)
            def _cmp(a, b):
                return cmp(len(b[0]), len(a[0]))
            children.sort()     # do deepest first
            for file, isDir in children:
                path, name = self.__fs.split(file)
                ev = FileSystemEventArgs(WatcherChangeTypes.Deleted, path, name)
                self.__onChanged(source, ev, isDir=isDir)
        # try and get the info from the database
        try:
            if callable(self.__getRecordWithPath):
                row = self.__getRecordWithPath(path)
                if row:
                    print "db isDir='%s'" % row[3]
        except Exception, e:
            print "Error in __onDeleted() - '%s'" % str(e)
        self.__onChanged(source, e)
    
    
    def __onChanged(self, source, e, isDir=None):
        path = e.FullPath.replace("\\", "/")
        eventName = "mod"
        eventTime = int(time.time())
        if isDir is None:
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
        #print "__onChanged() path='%s', eventName='%s', eventTime='%s'" % (path, eventName, eventTime)
        # to help reduce double events
        if self.__lastEvent==(path, eventName, eventTime):
            return
        self.__lastEvent=(path, eventName, eventTime)
        #
        path = path.replace("\\", "/")
        for listener in self.__listeners:
            try:
                listener(file=path, eventTime=eventTime, eventName=eventName, isDir=isDir)
            except Exception, e:
                print "Error calling FileWatcher listener - %s" % str(e)
                pass
    
    
    def __onRenamed(self, source, e):
        #print " rename oldFullPath=%s, oldName='%s', fullPath=%s, name='%s'" % (e.OldFullPath, e.OldName, e.FullPath, e.Name)
        path = e.OldFullPath.replace(e.OldName, "")
        ev = FileSystemEventArgs(WatcherChangeTypes.Deleted, path, e.OldName)
        self.__onDeleted(source, ev)
        ##
        path = e.FullPath.replace(e.Name, "")
        ev = FileSystemEventArgs(WatcherChangeTypes.Created, path, e.Name)
        self.__onCreated(source, ev)
    
    
    def close(self):
        if self.__fsWatcher is not None:
            self.__fsWatcher.EnableRaisingEvents = False
            self.__fsWatcher.Dispose()
            self.__fsWatcher = None


    def __del__(self):
        close()









