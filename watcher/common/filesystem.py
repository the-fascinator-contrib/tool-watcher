import os, datetime, time

class FileSystem(object):
    def __init__(self, cwd="."):
        self.__cwd = "."
        
    def __str__(self):
        return self.__cwd
    
    def absPath(self, path="."):
        return self.absolutePath(path)
    def absolutePath(self, path="."):
        return os.path.abspath(self.join(self.__cwd, path)).replace("\\", "/")
    
    def isDirectory(self, path):
        absPath = self.absolutePath(path)
        return os.path.isdir(absPath)
        
    def isFile(self, path):
        absPath = self.absolutePath(path)
        return os.path.isfile(absPath)
    
    def delete(self, path):
        if self.isFile(path):
            os.remove(path)
        else:
            absPath = self.absolutePath(path)
            self.__removeDirectory(absPath)
            
    def __removeDirectory(self, dir):
        if os.path.exists(dir):
            files = os.listdir(dir)
            for file in files:
                    file = dir + "/" + file
                    if os.path.isdir(file):
                        self.__removeDirectory(file)
                    else:
                        os.remove(file)
            os.rmdir(dir)
    
    def copy(self, fromPath, toPath):
        """ copy a file or directory """
        fromAbsPath = self.absolutePath(fromPath)
        toAbsPath = self.absolutePath(toPath)
        if self.isFile(fromPath):
            self.__copyFile(fromAbsPath, toAbsPath)
        if self.isDirectory(fromPath):
            self.__copyDirectory(fromAbsPath, toAbsPath)
            
    def __copyDirectory(self, fromAbsPath, toAbsPath):
        if not os.path.exists(toAbsPath):
            os.makedirs(toAbsPath)
        for item in os.listdir(fromAbsPath):
            itemPath = os.path.join(fromAbsPath, item)
            if self.isFile(itemPath):
                self.__copyFile(itemPath, os.path.join(toAbsPath, item))
            else:
                self.__copyDirectory(itemPath, os.path.join(toAbsPath, item))
        
    def __copyFile(self, fromAbsPath, toAbsPath):
        parent = os.path.split(toAbsPath)[0]
        if not os.path.exists(parent):
            self.__makeParent(toAbsPath)
            assert os.path.isdir(parent)
        f = None
        data = None
        try:
            f = open(fromAbsPath, "rb")
            data = f.read()
        finally:
            if f is not None:
                f.close()
                f = None
        try:
            f = open(toAbsPath, "wb")
            f.write(data)
        finally:
            if f is not None:
                f.close()
        
    def rename(self, fromPath, toPath):
        fromAbsPath = self.absolutePath(fromPath)
        toAbsPath = self.absolutePath(toPath)
        os.rename(fromAbsPath, toAbsPath)
    
    def join(self, *args):
        return os.path.join(*args).replace("\\", "/")
    
    def walker(self, path, func):
        """ path = path to walk
            func = callback function that take (path, dirs, files)
            Note: path will always end with a '/'
            Note: dirs can be modified to filter the walking of directories
        """
        absPath = self.absolutePath(path)
        if not absPath.endswith("/"):
            absPath += "/"
        
        for dirPath, dirs, files in os.walk(absPath):
            dirPath = dirPath.replace("\\", "/")
            if not dirPath.endswith("/"):
                dirPath += "/"
            p = self.join(path, dirPath[len(absPath):])
            func(p, dirs, files)
    
    def readFile(self, path):
        absPath = self.absolutePath(path)
        data = None
        try:
            f = None
            try:
                f = open(absPath, "rb")
                data = f.read()
            finally:
                if f is not None:
                    f.close()
        except:
            pass
        if data is None and self.__fakeFiles.has_key(absPath):
            data = self.__fakeFiles[absPath]
        return data
      
    def writeFile(self, path, data):
        self.__makeParent(path)
        f = None
        try:
            f = open(self.absolutePath(path), "wb")
            f.write(data)
        finally:
            if f is not None:
                f.close()
                
    def __makeParent(self, path):
        path = self.split(path)[0]
        if self.isDirectory(path)==True:
            return False
        if self.isFile(path):
            raise Exception("Cannot make directory '%s', already exists as a file!" % path)
        self.makeDirectory(path)
        return True
    
    def makeDirectory(self, path):
        absPath = self.absolutePath(path)
        if not os.path.exists(absPath):
            os.makedirs(absPath)
    
    def split(self, path):
        return os.path.split(path)
    
    #should not be here
    def formatDateTime(self, timeStamp, utc=False):
        format = "%Y-%m-%d %H:%M:%S" #for standard sqlite format
        if utc:
            format = "%a, %d %b %Y %H:%M:%S GMT"
        dt = datetime.datetime.fromtimestamp(timeStamp).strftime(format)
        return dt
    
    def convertGMTToFloat(self, timeStr):
        format = "%a, %d %b %Y %H:%M:%S GMT"
        mytime = time.strptime(timeStr, format)
        return time.mktime(mytime)
        
    