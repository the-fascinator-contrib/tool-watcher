#main app

import sys

sys.path.append("../common")
sys.path.append("../config")
sys.path.append("../queue")
from filesystem import FileSystem
from config import Config
from queue import *

class Watcher(object):
    def __init__(self):
        self.__fs = FileSystem(".")
        self.__config = Config(fileSystem=self.__fs)
        
        self.__eventWatcherClass = None
        self.__db = None
        
        self.watcher = None
        self.db = None
        self.queue = None
        
        self._setup()
        
    def _setup(self):
        if self.__config.platform:
            fsWatcherPath = "../fswatcher/%s" % self.__config.platform
            sys.path.append(fsWatcherPath)
            watchLib = "%sWatcher" % self.__config.platform
            __import__(watchLib)
            self.__eventWatcherClass = sys.modules[watchLib].EventWatcherClass
            
        if self.__config.db:
            dbPath = "../db/%s" % self.__config.db
            sys.path.append(dbPath)
            dbLib = "%sdb" % self.__config.db
            __import__(dbLib)
            self.__db = sys.modules[dbLib].Database
        
        if self.__db and self.__eventWatcherClass:
            #setup db
            self.db = self.__db()
            
            #setup queue
            self.queue = Queue(self.db, self.__fs)
             
            #setup Watcher        
            self.watcher = self.__eventWatcherClass(self.__config, fs=self.__fs)

            self.watcher.addListener(self.queue.put)
        
            
if __name__ == "__main__":
    watcher = Watcher()