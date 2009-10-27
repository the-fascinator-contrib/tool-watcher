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

""" Config modules to process config file written in json format
@requires: - python_simplejson OR 
           - common/json2_5.py 
"""
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
        """ Default dictionary class """
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
            """ Set attribute name and value
            @param name: attribute name
            @type name: String
            @param valu: attribute value
            @type name: String
            """  
            self[name] = value

        def __delattr__(self, name):
            """ Delete specified attribute 
            @param name: attribute name
            @type name: String 
            """
            self.pop(name)
            
    

    def __init__(self, fileSystem, configFileName="config.json", configFileSearchPaths=["."]):
        """ Config constructor class. 
        Usage: Config(fileSystem, configFileName="config.json", configFileSearchPaths=["."])
        @param filesystem: filesystem object
        @type filesystem: FileSystem
        @param configFileName: the config file path, defaulted to config.json
        @type configFileName: String
        @param configFileSearchPaths: search path for config file, defaulted to ["."]
        @type configFileSearchPaths: list       
        """
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
        """ Reload config file """
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
        """ add reloadWatcher callback function """
        self.__reloadWatchers.append(callback)

    def removeReloadWatcher(self, callback):
        """ remove reloadWatcher callback function """
        try:
            self.__reloadWatchers.remove(callback)
            return True
        except:
            return False
        
    @property
    def configFile(self):
        """ Config file """
        return self.__configFile

    @property
    def settings(self):
        """ Config settings Dictionary """
        return self.__settings

    def __getConfigData(self):
        """ Get config file content """
        data = self.__fileSystem.readFile(self.__configFile)
        return data
    
    def keys(self):
        """ Return list of keys defined in config file """
        return self.__settings.keys()
    
    def get(self, name, default=None):
        """ Get value of specified key-name from config file
        @param name: key in the config
        @type name: String
        @param default: default value if the key not found, defaulted to None
        @type: String
        """
        return self.__settings.get(name, default)

    def __getitem__(self, name):
        """ Get item based on speficied key-name 
        @param name: key in the config
        @type name: Sring
        @return: requested item value
        @rtype: String 
        """
        return self.__settings.get(name)
    
    def __getattr__(self, name):
        """ Get attribute based on specified attribute name
        @param name: attribute name in the config
        @type name: Sring
        @return: requested attribute value
        @rtype: String  
        """
        return self.__settings(name)

    def __call__(self, name, default=None):
        return self.__settings(name, default)

    


class FileSystem(object):
    """ FileSystem class """
    # Methods
    #   join(*args)     -> string
    #   absPath(path)   -> string
    #   isFile(file)    -> True|False
    #   readFile(file)  -> data|None

    import os

    @staticmethod
    def join(*args):
        """ Join multiple path
        @param args: list of paths
        @type args: list
        @return: the joined file path
        @rtype: String
        """
        return FileSystem.os.path.join(*args)

    @staticmethod
    def absPath(path):
        """ Get the absolute path of the specified path 
        @param path: file path
        @type path: String
        @return: absolute path of the specified path
        @rtype: String
        """
        return FileSystem.os.path.abspath(path)

    @staticmethod
    def isFile(file):
        """ Check if it's a file
        @param file: file path
        @type file: String
        @return: True if it's a file, otherwise False
        @rtype: boolean  
        """
        return FileSystem.os.path.isfile(file)

    @staticmethod
    def readFile(file):
        """ Read file content 
        @param file: file path
        @type file: String
        @return: content of the specified file
        @rytpe: String
        """
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


