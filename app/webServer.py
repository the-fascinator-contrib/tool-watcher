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

import BaseHTTPServer
import os
import sys
import threading
import time
from urllib import unquote



class ServerHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    feeder = None
    httpd = None
    def do_GET(self):
        fromDate = self.headers.getheader("Last-Modified")
        toDate = None
        path = unquote(self.path).replace("+", " ")
        fromDate, toDate, cmd = self.__getFromPath(path, fromDate)

        if cmd=="test":
            self.__test(path, fromDate, toDate)
        elif cmd=="count":
            self.__getCount()
        elif cmd=="html":
            self.__getHtmlFeed(fromDate, toDate)
        elif cmd=="text":
            self.__getTextFeed(fromDate, toDate)
        elif cmd=="name":
            self.__name()
        elif cmd=="time":
            self.__time()
        elif cmd=="shutdown":
            self.shutdown()
        else:
            self.__getJsonFeed(fromDate, toDate)

    def __getFromPath(self, path, fromDate):
        toDate = None
        cmd = None
        parts = path.split("/")
        for part in parts:
            if part=="":
                continue
            if part[0].isdigit():
                if fromDate is None:
                    fromDate = part
                elif toDate is None:
                    toDate = part
            elif part.isalpha():
                if cmd is None:
                    cmd = part
        if fromDate is None:
            fromDate = "1970-01-01"
        return fromDate, toDate, cmd

    def __test(self, path, fromDate, toDate):
        self.send_response(200, "OK")
        self.send_header("Content-type", "text/html")
        self.end_headers()
        s = "TEST path='%s', fromDate='%s', toDate='%s'" % (path, fromDate, toDate)
        s += "\n"
        if fromDate is not None:
            try:
                secs = self.feeder.convertGMTToInteger(fromDate)
            except:
                secs = "?"
            s += ("fromDate='%s'  Secs=%s\n" % (fromDate, secs))
        if toDate is not None:
            try:
                secs = self.feeder.convertGMTToInteger(toDate)
            except:
                secs = "?"
            s += ("toDate='%s'  Secs=%s\n" % (toDate, secs))
        print s
        s = s.replace("\n", "<br/>")
        self.wfile.write(s)

    def __getJsonFeed(self, fromDate, toDate):
        #lastModifiedFile = self.feeder.lastModifiedTimeStamp()
        def compare(a, b):
            return cmp(a[1], b[1])
        try:
            lastModified = self.feeder.formatDateTime(time.time(), utc=True)
            rows = self.feeder.getFeed(fromDate, toDate)
            rows.sort(compare)
            if rows==[]:
                t = self.feeder.convertGMTToInteger(fromDate)
            else:
                t = rows[-1][1]
            lastModified = self.feeder.formatDateTime(t, utc=True)
            data = rows
            # change to a dictionary of dictionaries  e.g. {file:{time:.., state:...}, ...}
            data = dict([(f, {"time":t, "state":s}) for f, t, s in rows])
            try:
                data =self.feeder.convertToJson(data)
            except Exception, e:
                print "__getJsonFeed   %s" % str(e)
                data = str(data)
        except Exception, e:
            data = str({"Error": str(e)})
        self.send_response(200, "OK")
        self.send_header("Content-type", "application/json")
        #self.send_header("Content-type", "text/html")
        self.send_header("Last-Modified", lastModified)
        self.end_headers()
        self.wfile.write(data)


    def __getHtmlFeed(self, fromDate, toDate):
        data = self.__getFeedText(fromDate, toDate)
        self.__write(data, contentType="text/html")

    def __getTextFeed(self, fromDate, toDate):
        data = self.__getFeedText(fromDate, toDate)
        self.__write(data, contentType="text/plain")

    def __getFeedText(self, fromDate, toDate):
        def compare(a, b):
            return cmp(a[1], b[1])
        try:
            rows = self.feeder.getFeed(fromDate, toDate, True)
            rows.sort(compare)
            data = ""
            for file, eventTime, eventName, isDir in rows:
                data += "%s, %s, %s, %s\n" % (eventTime, eventName, file, isDir)
            data = BaseHTTPServer._quote_html(data)
            #if True:
            try:
                if rows==[]:
                    lastModified = fromDate
                    #lastModified = self.feeder.formatDateTime(fromDate, utc=True)
                else:
                    lastModified = rows[-1][1]
                data += "\nlastModified = %s" % lastModified
            except Exception, e:
                print str(e)
                print "t='%s'" % t
        except Exception, e:
            data = str({"Error": str(e)})
        return data

    def __getCount(self, path="/"):
        try:
            print "getCount path='%s'" % path
            data = "FileCount=%s" % self.feeder.getFileCount(path)
        except Exception, e:
            data = str({"Error": str(e)})
        self.__write(data)

    def __name(self):
        name = os.environ.get("COMPUTERNAME", "?")
        self.__write("ComputerName='%s', platform='%s'" % (name, sys.platform))

    def __time(self):
        data = "CurrentTime=%s" % self.feeder.formatDateTime()
        data += ", GMT = %s" % self.feeder.formatDateTime(utc=True)
        self.__write(data)

    def __write(self, data, contentType="text/html"):
        self.send_response(200, "OK")
        self.send_header("Content-type", contentType)
        self.end_headers()
        self.wfile.write(data)

    def shutdown(self):
            print "shutdown requested"
            self.__write("Shutdown")
            def shutdown():
                try:
                    self.httpd.shutdown()
                except:
                    pass
            threading.Timer(0.2, shutdown).start()



def webServe(host, port, feeder):
    ServerHandler.feeder = feeder       ####################
    httpd = BaseHTTPServer.HTTPServer( (host, port), ServerHandler)
    ServerHandler.httpd = httpd
    running = [False]
    def shutdown():
        if running[0]:
            try:
                httpd.shutdown()
            except Exception, e:
                print str(e)
                print " try pressing Ctrl+C a couple of times to shutdown"
    
    def serve():
        running[0] = True
        httpd.serve_forever()
        running[0] = False
    threading.Thread(target=serve, name="webServer").start()
    return shutdown

    
