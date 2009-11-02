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

""" Feeder Module to get Json feed """

class Feeder(object):
    def __init__(self, utils, controller):
        """ Constructor method for Feeder class
        Feeder(utils, controller)
        """
        self.__utils = utils
        self.__controller = controller


    def getFeed(self, fromDate, toDate=None, includeDir=False):
        """ Get Feed from specified date
        @param fromDate: from the specified date
        @type fromDate: String
        @param toDate: to specified date, defaulted to None
        @type toDate: String
        @param includeDir: to include directory, defaulted to false     
        @type includeDir: boolean 
        @return: list of rows
        @rtype: list
        """
        # fromDate and toDate will be string arguments
        fromDate = self.convertGMTToInteger(fromDate)
        if toDate is not None:
            toDate = self.convertGMTToInteger(toDate)
        rows = self.__controller.getRecordsFromDate(fromDate, toDate)
        if includeDir==False:
            # filter out directory entries
            rows = [[f, t, n] for f, t, n, isDir in rows if isDir==False]
        else:
            rows = [list(r) for r in rows]
        for row in rows:
            file = row[0]
            if file.startswith("/"):
                file = "file://" + file
            else:
                file = "file:///" + file
            row[0] = file
            row[1] = int(row[1])        # To convert from Int64(IronPython) to just long
        return rows


    def getFileCount(self, startingWithPath=""):
        """ Get number of files
        @param startingWithPath: filter the file count query with startingWithPath, defaulted to ""
        @type param: String
        @return: total number of files
        @rtype: integer 
        """
        return self.__controller._getRecordsCount(startingWithPath)


    def formatDateTime(self, timeStamp=None, utc=False):
        """ Format the timeStamp
        @param timeStamp: timeStamp to be formatted, defaulted to None
        @type timeStamp: String
        @param utc: utc format, defaulted to false
        @type utc: boolean   
        @return: Formated timestamp
        @rtype: String
        """
        return self.__utils.formatDateTime(timeStamp, utc)


    def convertGMTToInteger(self, timeStr):
        """ Convert the timeStamp to integer in number in seconds
        @param timeStr: time to be converted
        @type timeStr: String
        @return: formatted time stamp
        @rtype: String
        """
        return self.__utils.convertGMTToInteger(timeStr)


    def convertToJson(self, data):
        """ Convert the data to json
        @param data: data to be converted
        @type data: String
        @return: Converted data 
        @rtype: Json object  
        """
        return self.__utils.convertToJson(data)





