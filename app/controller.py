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

import time


class Controller(object):
    # Constructor:
    #   Controller(db, fileSystem, config, FileWatcher, WatchDirectory, 
    #                                   update=True)
    # Properties:
    #   watchDirectories
    # Methods:
    #   configChanged(config)
    #   startWatching(watchDirectory)
    #   stopWatching(watchDirectory)
    #   getRecordsFromDate(fromDate=0, toDate=None)
    #   addListener(listener)
    #   removeListener(listener)
    #   close()
    #   _getRecordsCount(startingWithPath="")
    #   _updateWalk(watchDirectory)
    #   _updateHandler(file, eventTime, eventName, isDir=False)
    def __init__(self, db, fileSystem, config, FileWatcher, WatchDirectory, \
                        update=True):
        self.__db = db
        self.__fs = fileSystem          # .getModifiedTime(path), .walker(path, callback)
        self.__FileWatcher = FileWatcher        # is a FileSystemWatcher
        self.__WatchDirectory = WatchDirectory
        self.__watchDirectories = self.__getWatchDirectoriesFromConfig(config)
        self.__listeners = []
        #config.addConfigChangeWatcher(self.__)
        for watchDirectory in self.__watchDirectories.values():
            # check to see if we are conintue watching or are starting watching
            if not watchDirectory.stop:
                if self.__isStartWatch(watchDirectory):
                    self.startWatching(watchDirectory)
                else:
                    self.__watch(watchDirectory)
                    if update:
                        self._updateWalk(watchDirectory)


    @property
    def watchDirectories(self):
        return self.__watchDirectories


    def configChanged(self, config):
        # look for watchDirectories to Start and Stop watching
        watchDirectories = self.__getWatchDirectoriesFromConfig(config)
        currentWatchedPaths = self.__watchDirectories.keys()
        for wd in watchDirectories.itervalues():
            cwd = self.__watchDirectories.get(wd.path)
            if cwd is None:
                self.startWatching(wd)
            else:
                currentWatchedPaths.remove(wd.path)
                if wd==cwd:
                    # no change
                    pass
                else:
                    # OK just update the filters
                    cwd.ignoreFileFilter = wd.ignoreFileFilter
                    cwd.ignoreDirectories = wd.ignoreDirectories
        for path in currentWatchedPaths:
            cwd = self.__watchDirectories.get(path)
            self.stopWatching(cwd)


    def startWatching(self, watchDirectory):
        ## Remove all paths that are watched by any other watchDirectories
        self.__watchDirectories[watchDirectory.path] = watchDirectory
        self.__watch(watchDirectory)
        self._updateWalk(watchDirectory, startEvent=True)

    
    def stopWatching(self, watchDirectory):
        print "stopWatching '%s'" % watchDirectory.path
        if self.__watchDirectories.has_key(watchDirectory.path):
            self.__watchDirectories.pop(watchDirectory.path)
        watchDirectory.watcher = None       # will also stop watching and close
        #
        rows = self.__db.getRecordsStartingWithPath(watchDirectory.path[:-1])
        timeNow = self.__timeNow()
        ## Remove all paths that are watched by any other watchDirectories
        #for opath in self.__watchDirectories.keys():
        #    if watchDirectory.path.startswith(opath):
        #        rows = [row for row in rows if row[0].startswith(opath)]
        for row in rows:
            file, eventTime, eventName, isDir = row
            if eventName=="mod":
                eventName = "stopmod"
            elif eventName=="del":
                eventName = "stopdel"
            else:
                eventName = "stop"
            self._updateHandler(file, timeNow, eventName, isDir)
    
    
    def getRecordsFromDate(self, fromDate=0, toDate=None):
        rows = self.__db.getRecordsFromDate(fromDate, toDate)
        return rows
    
    
    def addListener(self, listener):
        self.__listeners.append(listener)
    
    def removeListener(self, listener):
        if self.__listeners.count(listener)>0:
            self.__listeners.remove(listener)
            return True
        return False
    
    
    def close(self):
        for watchDirectory in self.__watchDirectories.itervalues():
            watcher = watchDirectory.watcher
            if watcher is not None:
                watcher.close()
        self.__db.close()


    def _getRecordsCount(self, startingWithPath=""):
        rows = self.__db.getRecordsStartingWithPath(startingWithPath)
        return len(rows)


    def _updateWalk(self, watchDirectory, startEvent=False):
        # run this in its own thread
        rows = self.__db.getRecordsStartingWithPath(watchDirectory.path[:-1])
        dfiles = dict([(row[0], row) for row in rows])
        timeNow = self.__timeNow()

        def callback(path, dirs, files):
            path = path.replace("\\", "/")
            if watchDirectory.filter(path)==False:
                while len(dirs)>0:
                    dirs.pop()
                return
            if startEvent:
                ## remove any other watchDirectories - NO - is still a start watch for this watched path
                etime = timeNow
                eventName = "start"
            else:
                etime = self.__fs.getModifiedTime(path)
                eventName = "mod"
            self._updateHandler(path[:-1], etime, eventName, True)
            if dfiles.has_key(path[:-1]):
                dfiles.pop(path[:-1])
            for file in files:
                fullFile = path + file
                if watchDirectory.filter(fullFile)==False:
                    continue
                if startEvent:
                    etime = timeNow
                    eventName = "start"
                else:
                    etime = self.__fs.getModifiedTime(fullFile)
                    eventName = "mod"
                self._updateHandler(fullFile, etime, eventName, False)
                if dfiles.has_key(fullFile):
                    dfiles.pop(fullFile)
        self.__fs.walker(watchDirectory.path, callback)
        # what is left must have been deleted
        for file, _, _, isDir in dfiles.itervalues():
            print "deleting '%s'" % file
            self._updateHandler(file, timeNow, "del", isDir)


    def _updateHandler(self, file, eventTime, eventName, isDir=False):
        self.__updatedb([(file, eventTime, eventName, isDir)])
        for listener in self.__listeners:
            if callable(listener):
                try:
                    listener(file, eventTime, eventName, isDir)
                except Exception, e:
                    pass


    def __updatedb(self, uList):
        try:
            self.__db.updateList(uList)
        except Exception, e:
            print "ERROR in db.updateList() - '%s'" % str(e)
    
    
    def __watch(self, watchDirectory):
        #print "__watch '%s'" % watchDirectory
        try:
            watcher = self.__FileWatcher(watchDirectory.path, self.__fs, self.__getChildrenOf)
            watchDirectory.watcher = watcher
            watcher.addListener(watchDirectory.updateHandler)
            watchDirectory.addListener(self._updateHandler)
            watcher.startWatching()
        except Exception, e:
            msg = str(e)
            if msg.find("Directory does not exists")!=-1:
                msg = "Directory does not exists!"
            print "Failed to start watching '%s' - %s" % (watchDirectory.path, msg)
    
            
    def __getChildrenOf(self, path):
        rows = self.__db.getAllActiveChildrenOfPath(path)
        return [(file, isDir) for file, et, en, isDir in rows]
    
    
    def __isStartWatch(self, watchDirectory):
        # is a 'start watching' if this path does not exist in the database
        #       or it's eventName starts with 'stop'
        row = self.__db.getRecordWithPath(watchDirectory.path[:-1])
        return row is None or row[2].startswith("stop")


    def __getWatchDirectoriesFromConfig(self, config):
        watchDirectories = {}
        try:
            for path, d in config.watcher.watchDirs.iteritems():
                path = self.__fs.absPath(path)
                #print "path='%s', d='%s'" % (path, d)
                ignoreFileFilter = d.get("ignoreFileFilter", "")
                ignoreDirectories = d.get("ignoreDirectories", "")
                stop = d.get("stop", 0)
                cxtTags = d.get("cxtTags", [])
                watchDir =  self.__WatchDirectory(path)
                watchDir.ignoreFileFilter = ignoreFileFilter
                watchDir.ignoreDirectories = ignoreDirectories
                watchDir.stop = stop
                watchDir.cxtTags = cxtTags
                watchDirectories[watchDir.path] = watchDir
        except Exception, e:
            print str(e)
        return watchDirectories


    def __timeNow(self):
        return int(time.time())


        
        
        
        
        