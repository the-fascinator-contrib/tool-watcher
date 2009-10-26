



class Feeder(object):
    # Constructor:
    #   Feeder(utils, controller)
    def __init__(self, utils, controller):
        self.__utils = utils
        self.__controller = controller


    def getFeed(self, fromDate, toDate=None, includeDir=False):
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
        return self.__controller._getRecordsCount(startingWithPath)


    def formatDateTime(self, timeStamp=None, utc=False):
        return self.__utils.formatDateTime(timeStamp, utc)


    def convertGMTToInteger(self, timeStr):
        return self.__utils.convertGMTToInteger(timeStr)


    def convertToJson(self, data):
        return self.__utils.convertToJson(data)





