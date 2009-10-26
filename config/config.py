
try:
    from json import loads
    #from json import dumps
except:
    from json2_5 import loads
from types import DictType


class Config(object):
    """
     Constructor:
       Config(fileSystem, configFileName="config.json", configFileSearchPaths=["."]):
     Properties:
       settings            (default None dictionary)
       configFile          (the configuration file that is being used)
       .x                   config value for x
     Methods:
       reload()
       addReloadWatcher(callback)      ( callback method notify(config) )
       removeReloadWatcher(callback)
       get(key, default=None)
       ("key1" [,"default"])   -> value or defaultValue  (shortcut method)      (__call__)
    """
    class DefaultDict(dict):
        def __missing__(self, key):
            return None

        def getDefaultDict(self, name):
            return Config.DefaultDict(self.get(name, {}))

        def __call__(self, name, default=None):
            """ select a element via dot '.' notation 
                e.g. key1.key2.key3 -> key3.value """
            #data = self.get(name, default)
            #if type(data) is DictType:
            #    data = Config.DefaultDict(data)
            sector = name
            d = self
            names = sector.split(".")
            last = names.pop()
            for name in names:
                d = d.get(name, {})
                if type(d) is not DictType:
                    d = {}
                    break
            data = d.get(last, default)
            if type(data) is DictType:
                data = Config.DefaultDict(data)
            return data

        def __getattr__(self, name):
            #return self.get(name)
            """ select a element via dot '.' notation
                e.g. key1.key2.key3 -> key3.value """
            #data = self.get(name, default)
            #if type(data) is DictType:
            #    data = Config.DefaultDict(data)
            default = None
            sector = name
            d = self
            names = sector.split(".")
            last = names.pop()
            for name in names:
                d = d.get(name, {})
                if type(d) is not DictType:
                    d = {}
                    break
            data = d.get(last, default)
            if type(data) is DictType:
                data = Config.DefaultDict(data)
            return data

        def __setattr__(self, name, value):
            self[name] = value

        def __delattr__(self, name):
            self.pop(name)
            
    

    def __init__(self, fileSystem, configFileName="config.json", configFileSearchPaths=["."]):
        """Config(fileSystem, configFileName="config.json", configFileSearchPaths=["."])"""
        self.__fileSystem = fileSystem
        self.__settings = Config.DefaultDict()
        self.__configFileSearchPaths = configFileSearchPaths
        self.__configFileName = configFileName
        self.__configFile = None
        self.__data = None
        self.__reloadWatchers = []
        # find the configFilePath
        for path in configFileSearchPaths:
            configFile = fileSystem.join(path, configFileName)
            configFile = fileSystem.absPath(configFile)
            if fileSystem.isFile(configFile):
                self.__configFile = configFile
                break;
        if self.__configFile is None:
            print "Warning: no configFile '%s' found!" % configFileName
        self.reload()

    def reload(self):
        #print "reload()"
        data = self.__getConfigData()
        if data==self.__data:
            return
        self.__data = data
        try:
            #d = eval(data)
            d = loads(data)
            self.__settings.clear()
            self.__settings.update(d)
        except Exception, e:
            msg = "Error loading configFile '%s' - '%s'" % (self.__configFile, str(e))
            raise Exception(msg)
        for watcher in self.__reloadWatchers:
            try:
                watcher(self)
            except: pass

    def addReloadWatcher(self, callback):
        self.__reloadWatchers.append(callback)

    def removeReloadWatcher(self, callback):
        try:
            self.__reloadWatchers.remove(callback)
            return True
        except:
            return False
        
    @property
    def configFile(self):
        return self.__configFile

    @property
    def settings(self):
        return self.__settings

    def __getConfigData(self):
        data = self.__fileSystem.readFile(self.__configFile)
        return data
    
    def keys(self):
        return self.__settings.keys()
    
    def get(self, name, default=None):
        return self.__settings.get(name, default)

    def __getitem__(self, name):
        return self.__settings.get(name)
    
    def __getattr__(self, name):
        return self.__settings(name)

    def __call__(self, name, default=None):
        return self.__settings(name, default)

    


class FileSystem(object):
    # Methods
    #   join(*args)     -> string
    #   absPath(path)   -> string
    #   isFile(file)    -> True|False
    #   readFile(file)  -> data|None

    import os

    @staticmethod
    def join(*args):
        return FileSystem.os.path.join(*args)

    @staticmethod
    def absPath(path):
        return FileSystem.os.path.abspath(path)

    @staticmethod
    def isFile(file):
        return FileSystem.os.path.isfile(file)

    @staticmethod
    def readFile(file):
        if file is None:
            return None
        data = None
        try:
            f = open(file, "rb")
            data = f.read()
            f.close()
        except:
            pass
        return data


