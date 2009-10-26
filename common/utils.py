
import datetime
import time

try:
    from json import loads, dumps
    #from json import dumps
except:
    from json2_5 import loads, dumps


class Utils(object):
    def __init__(self):
        pass

    
    def formatDateTime(self, timeStamp=None, utc=False):
        if timeStamp is None:
            timeStamp = time.time()
        format = "%Y-%m-%d %H:%M:%S" #for standard sqlite format
        if utc:
            format = "%a, %d %b %Y %H:%M:%S GMT"
        dt = datetime.datetime.fromtimestamp(timeStamp).strftime(format)
        return dt


    def convertGMTToInteger(self, timeStr):
        try:
            if timeStr.lower().find("gmt")!=-1:
                format = "%a, %d %b %Y %H:%M:%S GMT"
            else:
                c = timeStr.count(":")
                if c==0:
                    format = "%Y-%m-%d"
                elif c==1:
                    format = "%Y-%m-%d %H:%M"
                else:
                    format = "%Y-%m-%d %H:%M:%S"
            mytime = time.strptime(timeStr, format)
            return int(time.mktime(mytime))
        except Exception, e:
            print str(e)
            print "  timeStr='%s' format='%s'" % (timeStr, format)


    def convertToJson(self, obj):
        return dumps(obj)


    def convertFromJson(self, json):
        return loads(json)






