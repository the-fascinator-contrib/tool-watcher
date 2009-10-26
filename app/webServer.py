

import BaseHTTPServer
import os
import sys
import threading
import time



class ServerHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    feeder = None
    httpd = None
    def do_GET(self):
        fromDate = self.headers.getheader("Last-Modified")
        toDate = None
        path = self.path.strip("/")
        parts = path.split("/")
        if fromDate is None and parts[-1].startswith("20"):
            fromDate = parts[-1].replace("%20", " ").replace("+", " ")
        if fromDate is None:
            fromDate = "1970-01-01"
        if parts[0]=="test":
            self.__test(path, fromDate)
        elif parts[0]=="count":
            self.__getCount(parts[1:])
        elif parts[0]=="html":
            self.__getHtmlFeed(fromDate, toDate)
        elif parts[0]=="name":
            self.__name()
        elif parts[0]=="time":
            self.__time()
        elif parts[0]=="shutdown":
            self.shutdown()
        else:
            self.__getJsonFeed(fromDate, toDate)

    def __test(self, path, fromDate):
        print "path='%s', fromDate='%s'" % (path, fromDate)
        self.send_response(200, "OK")
        self.send_header("Content-type", "text/html")
        self.end_headers()
        secs = self.feeder.convertGMTToInteger(fromDate)
        s = "path='%s', fromDate='%s'\n  Secs=%s\n%s"
        data = ""
        if self.path=="/dir":
            data = "dir=" + str(dir(self.httpd))
        s = s % (path, fromDate, secs, data)
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
        def compare(a, b):
            return cmp(a[1], b[1])
        try:
            rows = self.feeder.getFeed(fromDate, toDate, True)
            rows.sort(compare)
            data = ""
            for file, eventTime, eventName, isDir in rows:
                data += "%s, %s, %s, %s\n" % (eventTime, eventName, file, isDir)
            data = BaseHTTPServer._quote_html(data).replace("\n", "<br/>")
            #if True:
            try:
                if rows==[]:
                    t = self.feeder.convertGMTToInteger(fromDate)
                else:
                    t = rows[-1][1]
                lastModified = self.feeder.formatDateTime(t, utc=True)
                data += "<br/>lastModified=%s" % lastModified
            except Exception, e:
                print str(e)
                print "t='%s'" % t
        except Exception, e:
            data = str({"Error": str(e)})
        self.__htmlWrite(data)

    def __getCount(self, parts):
        try:
            path = "/" + "/".join(parts)
            print "getCount path='%s'" % path
            data = "FileCount=%s" % self.feeder.getFileCount(path)
        except Exception, e:
            data = str({"Error": str(e)})
        self.__htmlWrite(data)

    def __name(self):
        name = os.environ.get("COMPUTERNAME", "?")
        self.__htmlWrite("ComputerName='%s', platform='%s'" % (name, sys.platform))

    def __time(self):
        data = "CurrentTime=%s" % self.feeder.formatDateTime()
        data += ", GMT = %s" % self.feeder.formatDateTime(utc=True)
        self.__htmlWrite(data)

    def __htmlWrite(self, data):
        self.send_response(200, "OK")
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(data)

    def shutdown(self):
            print "shutdown requested"
            self.__htmlWrite("Shutdown")
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

    
