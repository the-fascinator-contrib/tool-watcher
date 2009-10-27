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

""" Utility module for the watcher 
@requires: - datetime, time
           - python_simplejson OR 
           - common/json2_5.py 
"""
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
        """ Get the formatted datetime """
        if timeStamp is None:
            timeStamp = time.time()
        format = "%Y-%m-%d %H:%M:%S" #for standard sqlite format
        if utc:
            format = "%a, %d %b %Y %H:%M:%S GMT"
        dt = datetime.datetime.fromtimestamp(timeStamp).strftime(format)
        return dt


    def convertGMTToInteger(self, timeStr):
        """ Convert the specified datetime to integer in seconds """
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
        """ Convert obj to json file """
        return dumps(obj)


    def convertFromJson(self, json):
        """ Convert specified json object to obj """
        return loads(json)






