from pyinotify import EventsCodes, ThreadedNotifier, Notifier, WatchManager, ProcessEvent, WatchManagerError
import os, time
from stat import *

class EventWatcherClass(object):
    FLAGS = EventsCodes.ALL_FLAGS
    mask  = FLAGS['IN_DELETE'] | FLAGS['IN_CREATE'] | \
            FLAGS['IN_MOVED_FROM'] | FLAGS['IN_MODIFY'] | \
            FLAGS['IN_MOVED_TO'] | FLAGS['IN_ATTRIB'] | FLAGS['IN_IGNORED'] | FLAGS['IN_MOVE_SELF']
    
    def __init__(self, config, fs):
        self.__config = config
        self.__listeners = []
        self.__fs = fs
        self.__watchManager = WatchManager()
        self.configFilePath = self.__config.configFilePath
        self.cp = CustomProcess(self, self.__listener, self.configFilePath)
        
        self.__daemonize = self.__config.daemon
        
        self.dirToBeWatched = []
        self.wm = None
    
    def __getDirToBeWatched(self):
        self.dirToBeWatched = self.__config.watchDirs
        if self.dirToBeWatched == []:
            self.dirToBeWatched.append(os.path.expanduser("/tmp"))  #watching /tmp directory by default
            
        #also watch the config file
        self.configFile = self.__config.configFilePath
        if self.configFile not in self.dirToBeWatched:
            self.dirToBeWatched.append(self.configFile)
    
    def __processWatchedDir(self, stopWatchDir=[]):
        self.__getDirToBeWatched()
        for dir in self.dirToBeWatched:
            if dir.rstrip("/") != self.configFilePath.rstrip("/"):
                if self.__fs.isDirectory(dir):
                    #modifiedDate = os.stat(dir)[ST_MTIME] #when a file start being watched, use the current system time
                    modifiedDate = time.time() 
                    detail = ("file://" + dir, int(modifiedDate), "start", True)
                    self.__listener(eventDetail=detail, initialization=True)
                else:
                    print 'fail to add dir to watched, the dir %s might not exist' % dir
                    
        for dir in stopWatchDir:
            if dir.rstrip("/") != self.configFilePath.rstrip("/"):
                if self.__fs.isDirectory(dir):
                    #modifiedDate = os.stat(dir)[ST_MTIME] #when a file start being watched, use the current system time
                    modifiedDate = time.time() 
                    detail = ("file://" + dir, int(modifiedDate), "stop", True)
                    self.__listener(eventDetail=detail, initialization=True)
                else:
                    print 'fail to add dir to watched, the dir %s might not exist' % dir 
            
            
    def __startWatcher(self):
        self.notifier = Notifier(self.__watchManager, default_proc_fun=self.cp)
        self.resetDirToBeWatched()
        self.notifier.loop(daemonize=self.__daemonize, pid_file='/tmp/pyinotify.pid', \
                  force_kill=True, stdout='/tmp/stdout.txt')
        
    def resetDirToBeWatched(self, configChanged=False):
        if configChanged:
            oldDirToBeWatched = self.dirToBeWatched
            oldDirToBeWatched.sort()                
            #reload the config file
            self.__config.reload()
            self.__getDirToBeWatched()
            stopWatchDir = []
            if oldDirToBeWatched != self.dirToBeWatched.sort():
                stopWatchDir = [item for item in oldDirToBeWatched if not item in self.dirToBeWatched]
            self.__processWatchedDir(stopWatchDir)
        if self.wm and self.wm.values():
            self.wm = self.__watchManager.rm_watch(self.wm.values())
        self.wm = self.__watchManager.add_watch(self.dirToBeWatched, self.mask, rec=True, auto_add=True)
#        self.wm = self.__watchManager.add_watch(self.__dirToBeWatched, self.mask, rec=True, 
#                                          auto_add=True, quiet=False, exclude_filter=self.excl)
    
    def addListener(self, listener):
        self.__listeners.append(listener)
        self.__processWatchedDir()
        self.__startWatcher()

    def removeListener(self, listener):
        if self.__listeners.count(listener)>0:
            self.__listeners.remove(listener)
            return True
        return False

    def __listener(self, *args, **kwargs):
        for listener in self.__listeners:
            try:
                listener(*args, **kwargs)
            except Exception, e:
                print str(e)
                pass
    
class CustomProcess(ProcessEvent):
    #event structure:
    #<Event dir=False mask=0x2 maskname=IN_MODIFY name=file10 path=/home/octalina/workspace/watcher/watchDir 
    #pathname=/home/octalina/workspace/watcher/watchDir/file10 wd=1 >
    def __init__(self, eventWatcher, listener, configFilePath):
        self.eventWatcher = eventWatcher
        self.__listener = listener
        self.configFilePath = configFilePath
    
    def getSystemModifiedDate(self, filePath):
        if os.path.exists(filePath):
            return os.stat(filePath)[ST_MTIME]
        return 0
    
    def process_IN_CREATE(self, event):
        self.__callingModEvent(event)

    def process_IN_MODIFY(self, event):
        self.__callingModEvent(event)

    def process_IN_ATTRIB(self, event):
        self.__callingModEvent(event)
        
    def process_IN_DELETE(self, event):
        self.__callingDelEvent(event)
    
    def process_IN_MOVED_TO(self, event):
        self.__callingModEvent(event)
    def process_IN_MOVED_FROM(self, event):
        self.__callingDelEvent(event)
        
    def __callingDelEvent(self, event):
        self.__processEachEvents("del", event)
    def __callingModEvent(self, event):
        self.__processEachEvents("mod", event)

    def __processEachEvents(self, eventName, event):
        if event.pathname.rstrip("/") == self.configFilePath.rstrip("/"):
            self.eventWatcher.resetDirToBeWatched(configChanged=True)
        else:
            #modifiedDate = self.getSystemModifiedDate(event.pathname)
            #use system time for now
            modifiedDate = int(time.time())
            dirProcess = False
            dirRename = False
            if event.maskname.find("IN_ISDIR")>-1:
                dirProcess = True
                if event.maskname.find("IN_MOVED")>-1:
                    dirRename = True
            
            detail = ("file://" + event.pathname, modifiedDate, eventName, dirProcess)
            #print "pathName: %s, eventName: %s, maskName: %s, modifiedTime: %s, isDir: %s, dirRename: %s" % (event.pathname, eventName, event.maskname, modifiedDate, dirProcess, dirRename)
            self.__listener(eventDetail=detail, renameDir=dirRename)
        
#        self.excl = None
#        if self.__exclFile and self.__exclFileName:
#            self.excl = ExcludeFilter({self.__exclFileName: self.__exclFile})
