
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
        #print "__onChanged() path='%s', eventName='%s', eventTime='%s'" % (path, eventName, eventTime)
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
        #print "__onRenamed event"
        path = self.__fs.split(e.OldFullPath)[0]
        ev = FileSystemEventArgs(WatcherChangeTypes.Deleted, path, e.OldName)
        self.__onChanged(source, ev)
        path = self.__fs.split(e.FullPath)[0]
        ev = FileSystemEventArgs(WatcherChangeTypes.Created, path, e.Name)
        self.__onChanged(source, ev)
    
    
    def close(self):
        if self.__fsWatcher is not None:
            self.__fsWatcher.EnableRaisingEvents = False
            self.__fsWatcher.Dispose()
            self.__fsWatcher = None


    def __del__(self):
        close()









