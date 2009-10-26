
from pyinotify import Notifier, WatchManager, ProcessEvent, ThreadedNotifier
from pyinotify import IN_DELETE, IN_CREATE, IN_MODIFY, IN_ATTRIB, IN_IGNORED
from pyinotify import IN_MOVE_SELF, IN_MOVED_FROM, IN_MOVED_TO
from pyinotify import IN_DELETE_SELF, IN_CLOSE_WRITE, IN_ISDIR
import os
import time
from stat import *


class INotifyWatcher(object):
    """
    Constructor:
        INotifyWatcher(path, fs)
    Methods:
        addListener(listener)   #listener(path=path, eventTime=eventTime, eventName=eventName, isDir=isDir)
        removeListener(listener)
        startWatching()
        stopWatching()
        close()
    """

    #  *** BUG ***
    #  When a directory is moved, it's sub-directories will then still report changes using the
    #       old pathname!
    #  Also does not indicate that sub items have been removed
    #  ***********

    # (wm = WatchManager())
    #  wd = wm.get_wd(path)
    #  wm._wmd  -> dictionary of wd:Watch
    #  wm.rm_watch(wd)
    #  wdd = wm.add_watch(path, mask, rec=True, auto_add=True)
    # (n = Notifier(wm, p [, timeout=10])
    #  n.stop()
    #       # Manual processing
    #       n.process_events()
    #       if n.check_events():
    #           n.read_events()
    #           n.process_events()

    # IN_CLOSE_WRITE instead of IN_CREATE | IN_MODIFY
    # IN_DELETE_SELF instead of IN_IGNORED
    mask = IN_DELETE | IN_CLOSE_WRITE
    mask |= IN_MOVED_FROM | IN_MOVED_TO
    mask |= IN_CREATE | IN_ISDIR        # received together on mkdir
    #mask |=  | IN_ATTRIB | IN_IGNORED | IN_MOVE_SELF | IN_DELETE_SELF

    __watchManager = None
    __notifier = None
    __watchers = {}                 # path: INotifyWatcher

    @staticmethod
    def __processEvent(event):
        # event - .dir(isdir), .name(filename), .path(pathOnly), .pathname(fullname), .wd, .mask, .maskname
        if event.pathname.endswith("-wrong-path"):
            # ignore this - error event!
            return
        mask = event.mask
        if mask==(IN_CREATE | IN_ISDIR) and event.dir:
            # create dir
            eventName = "create"
        elif mask & IN_CREATE:
            return
        elif mask & IN_DELETE:
            eventName = "del"
        elif mask & IN_MOVED_FROM:            # delete
            eventName = "moveFrom"
            # delete all sub items
        elif mask & IN_MOVED_TO:
            eventName = "moveTo"
        else:                                                 # mod
            eventName = "mod"
        #------------------
        #modifiedDate = getSystemModifiedDate(event.pathname)
        modifiedDate = int(time.time())     #use system time for now
        pathname = event.pathname
        isDir = event.dir
        #pathname, eventName, isDir, walk
        for path, watcher in INotifyWatcher.__watchers.iteritems():
            if pathname.startswith(path):
                watcher.__procEvent(pathname, eventName, isDir)

    
    @staticmethod
    def setup(daemonize=False):
        INotifyWatcher.__watchManager = WatchManager()
        ## ThreadedNotifier()  # .start()  .stop()
        #self.notifier = Notifier(self.__watchManager, default_proc_fun=self.__processEvent)
        #self.notifier.loop(daemonize=self.__daemonize, pid_file='/tmp/pyinotify.pid', \
        #          force_kill=True, stdout='/tmp/stdout.txt')
        if daemonize:
            INotifyWatcher.__notifier = Notifier(INotifyWatcher.__watchManager) # timeout=10
            INotifyWatcher.__notifier.loop(daemonize=daemonize, pid_file='/tmp/pyinotify.pid', \
                  force_kill=True, stdout='/tmp/stdout.txt')
        else:
            INotifyWatcher.__notifier = ThreadedNotifier(INotifyWatcher.__watchManager)
            INotifyWatcher.__notifier.start()

    @staticmethod
    def stop():
        INotifyWatcher.__notifier.stop()

    
    def __init__(self, path, fs):
        if self.__watchManager is None:
            self.setup()
        self.__path = path
        self.__fs = fs
        self.__listeners = []
        self.__wd = {}

    
    def addListener(self, listener):
        self.__listeners.append(listener)


    def removeListener(self, listener):
        if self.__listeners.count(listener)>0:
            self.__listeners.remove(listener)
            return True
        return False


    def startWatching(self):
        # to simple - but the basic idea -
        #print self.__path
        self.__wd = self.__watchManager.add_watch(self.__path, self.mask, \
                                    proc_fun=INotifyWatcher.__processEvent, \
                                    rec=True, auto_add=True)
        #print self.__wd
        self.__watchers[self.__path] = self     # ? can we have more than one watcher watching the same path?

    
    def stopWatching(self):
        # to simple - but the basic idea - must to remove items that are being watched by other watchers
        if self.__wd!={}:
            self.__watchManager.rm_watch(self.__wd.values())
            self.__watchers.pop(self.__path)
        self.__wd = {}


    def close(self):
        self.stopWatching()
        self.__listeners = []
        if self.__watchers=={}:
            try:
                self.__notifier.stop()
            except:
                pass


    def __procEvent(self, pathname, eventName, isDir, walk=False):
        # ToDo: as directories are created add them to self.__wd
        print "pathname='%s', %s, '%s'" % (pathname, isDir, eventName)
        if eventName=="create":
            eventName = "mod"
        elif eventName=="moveFrom":
            eventName = "del"
            walk = True
        elif eventName=="moveTo":
            eventName = "mod"
            walk = True
        for listener in self.__listeners:
            try:
                listener(file=pathname, eventTime=time.time(), eventName=eventName, \
                            isDir=isDir, walk=walk)
            except Exception, e:
                print "Error calling FileWatcher listener - %s" % str(e)
                pass



    def __del__(self):
        self.close()






