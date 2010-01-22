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

""" FileSystem utility module to support watcher
@requires: os
"""

import os


class FileSystem(object):
    def __init__(self, cwd="."):
        """ Constructor method
        @param cwd: Current working directory, defaulted to "."
        @type cwd: String
        """  
        self.__cwd = "."
        
    def __str__(self):
        """ Get the current working directory
        @return: Current working directory
        @rtype: String
        """
        return self.__cwd
    
    def absPath(self, path="."):
        """ Get absolute path of the file
        @param path: file path
        @type path: String
        @return: absolute path of a file
        @rtype: String  
        """
        return self.absolutePath(path)
    def absolutePath(self, path="."):
        """ Get absolute path of the file
        @param path: file path
        @type path: String
        @return: absolute path of a file
        @rtype: String  
        """
        return os.path.abspath(self.join(self.__cwd, path)).replace("\\", "/")

    def isDir(self, path):
        """ Check if the path is a directory
        @param path: file path
        @type path: String
        @return: True if it's a directory, otherwise False
        @rtype: boolean   
        """
        return self.isDirectory(path)
    def isDirectory(self, path):
        """ Check if the path is a directory
        @param path: file path
        @type path: String
        @return: True if it's a directory, otherwise False
        @rtype: boolean   
        """
        absPath = self.absolutePath(path)
        return os.path.isdir(absPath)
        
    def isFile(self, path):
        """ Check if the path is a file
        @param path: file path
        @type path: String
        @return: True if it's a file, otherwise False
        @rtype: boolean   
        """
        absPath = self.absolutePath(path)
        return os.path.isfile(absPath)
    
    def delete(self, path):
        """ Delete file/directory based on specified path
        @param path: file path
        @type path: String
        """
        if self.isFile(path):
            os.remove(path)
        else:
            absPath = self.absolutePath(path)
            self.__removeDirectory(absPath)
            
    def __removeDirectory(self, dir):
        """ Delete directory and it's subdirectories and files based on specified path
        @param path: file path
        @type path: String
        """
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
        """ Copy a file or directory 
        @param fromPath: source file/directory path
        @type fromPath: String
        @param toPath: destination file/directory path
        @type toPath: String  
        """
        fromAbsPath = self.absolutePath(fromPath)
        toAbsPath = self.absolutePath(toPath)
        if self.isFile(fromPath):
            self.__copyFile(fromAbsPath, toAbsPath)
        if self.isDirectory(fromPath):
            self.__copyDirectory(fromAbsPath, toAbsPath)
            
    def __copyDirectory(self, fromAbsPath, toAbsPath):
        """ Copy a directory and it's content 
        @param fromPath: source directory path
        @type fromPath: String
        @param toPath: destination directory path
        @type toPath: String  
        """
        if not os.path.exists(toAbsPath):
            os.makedirs(toAbsPath)
        for item in os.listdir(fromAbsPath):
            itemPath = os.path.join(fromAbsPath, item)
            if self.isFile(itemPath):
                self.__copyFile(itemPath, os.path.join(toAbsPath, item))
            else:
                self.__copyDirectory(itemPath, os.path.join(toAbsPath, item))
        
    def __copyFile(self, fromAbsPath, toAbsPath):
        """ Copy a file  
        @param fromPath: source file path
        @type fromPath: String
        @param toPath: destination file path
        @type toPath: String  
        """
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
        """ Copy a file or directory 
        @param fromPath: source file/directory path
        @type fromPath: String
        @param toPath: destination file/directory path
        @type toPath: String  
        """
        fromAbsPath = self.absolutePath(fromPath)
        toAbsPath = self.absolutePath(toPath)
        os.rename(fromAbsPath, toAbsPath)
    
    def join(self, *args):
        """ Join file paths
        @param args: list of file path to be joined
        @type args: list
        @return: joined path
        @rtype: String
        """
        return os.path.join(*args).replace("\\", "/")

    def getModifiedTime(self, file):
        """ Get file or directory modified time
        @param file: file/dictionary path
        @type file: String
        @return: modified time
        @rtype: integer  
        """
        try:
            mt = os.stat(file)[8]
        except:
            mt = 0
        return mt

    def walker(self, path, func):
        """ Get a list of files/directories from the specified path
            @param path: path to walk
            @type path: String
            @param func: callback function that take (path, dirs, files)
            @type func: python function
            Note: path will always end with a '/'
            Note: dirs can be modified to filter the walking of directories
            @return: tuple of (path, list of directories, list of files)
            @rtype: (String, list, list)
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
        """ Read content of the specified path
        @param path: file path
        @type path: String
        @return path: content of the file
        @return path: String
        """
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
        """ Write content to the file
        @param path: file path
        @type path: String
        @param data: content of the file to be written
        @type data: String
        """
        self.__makeParent(path)
        f = None
        try:
            f = open(self.absolutePath(path), "wb")
            f.write(data)
        finally:
            if f is not None:
                f.close()
                
    def __makeParent(self, path):
        """ Create parents of the file or directories
        @param path: file or directories path
        @type path: String
        @return: True if successfully creating a parent directory
        @raise exception: False if the parent directory is a file   
        """
        path = self.split(path)[0]
        if self.isDirectory(path)==True:
            return False
        if self.isFile(path):
            raise Exception("Cannot make directory '%s', already exists as a file!" % path)
        self.makeDirectory(path)
        return True
    
    def makeDirectory(self, path):
        """ Create directory
        @param path: directory path to be created
        @type path: String
        """
        absPath = self.absolutePath(path)
        if not os.path.exists(absPath):
            os.makedirs(absPath)
    
    def split(self, path):
        """ Split file path
        @param path: file or directory name to be splitted
        @type path: String  
        @return: tuple of (path, filename or last directory name)
        @rtype: (String, String)
         """
        return os.path.split(path)
        
    
