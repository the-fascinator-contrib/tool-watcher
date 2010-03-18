
import clr
from System import AsyncCallback
from System.Net import HttpListener, HttpListenerException
from System.Text import Encoding
from System.Threading import Thread, ThreadStart
from threading import Thread as PyThread
import os
import sys
import time
from urllib import unquote



class WebServer2(object):
    def __init__(self, host="*", port=9000):
        self.serverThread = None
        self.pagesServed = 0
        self._serve = False
        self._listener = None
        self._serverThread = None
        self.failed = False
        self.failedReason = None
        self._host = host
        self._port = 9000
        self.text="""<html>
  <head><title>Testing a simple .net server</title></head>
  <body>
    <h1>Simple Server</h1>
    %s
  </body>
</html>"""
    
    @property
    def isServing(self):
        return self._serve
    def getIsServing(self):
        return self._serve
    
    def handleRequest(self, result):
        listener = result.AsyncState
        try:
            context = listener.EndGetContext(result) # allow the next request to be handled
        except:
            # exception when the thread has been aborted
            return
        self.pagesServed += 1
        request = context.Request
        response = context.Response
        rawUrl = request.RawUrl
        #if rawUrl=="/stop":
        #    self.stop()
        if rawUrl=="/shutdown":
            self.close()
        #text = getTextFromRequest(request)
        text, headers = self.getText(request)
        buffer = Encoding.UTF8.GetBytes(text)
        response.ContentLength64 = buffer.Length
        #response.AddHeader("Content-type", contentType)
        for k, v in headers.iteritems():
            response.AddHeader(k, v)
        output = response.OutputStream
        output.Write(buffer, 0, buffer.Length)
        output.Close()
    

    def getText(self, request):
        # request object:
        #   .AcceptTypes, .ContentEncoding, .ContentLength64, .ContentType, .Cookies, .HasEntityBody,
        #   .Headers, .HttpMethod, .InputStream, .IsAuthenticated, .IsLocal, .IsSecureConnection,
        #   .QueryString, .RawUrl, .Url, .UrlReferrer, .UserAgent, .UserHostAddress, .UserHostName
        #   NOTE: QueryString is a NameValueCollection object.
        #       RawUrl - includes everything from the root path including the querystring
        #       Url - is the hole url parameter including the querystring
        headers = {}
        for k in request.Headers.AllKeys:
            headers[k] = request.Headers[k]
        queryStrings = {}
        for k in request.QueryString.Keys:
            queryStrings[k] = request.QueryString[k]
        rawUrl = request.RawUrl
        path = rawUrl.split("?")[0].split("#")[0]
        data = "<div>URL Requested: %s<hr/>Number of Pages Served: %s</div>" % (rawUrl, self.pagesServed)
        data += "<div>PATH=%s</div>" % path
        data += ("<div>QueryString=%s, Url=%s, HttpMethod=%s</div>" % (queryStrings, request.Url, request.HttpMethod))
        try:
            for k, v in queryStrings.iteritems():
                data += ("<div>%s=%s</div>" % (k, v))
            data +=  "<div>-- Headers=%s</div>" % str(headers)
        except Exception, e:
            data += "ERROR:" + str(e)
        return self.text % data, {"Content-type":"text/html"}
    

    def _serveForever(self):
        self._serve = True
        self._listener = HttpListener()
        prefix = "http://%s:%s/" % (self._host, self._port)
        self._listener.Prefixes.Add(prefix)
        try:
            self._listener.Start()
            self.failed = False
            self.failedReason = None
        except HttpListenerException, e:
            #raise Exception("Starting server failed - %s" % str(e))
            self.failed = True
            self.failedReason = str(e)
            return
        while self._serve:
            result = self._listener.BeginGetContext(AsyncCallback(self.handleRequest), self._listener)
            result.AsyncWaitHandle.WaitOne()
        time.sleep(0.1)
        self._listener.Close()
    

    def startServing(self):
        self._serve = True
        if False:    # Python Threading
            t = PyThread(target=self._serveForever)
            t.start()
        else:       # .NET Threading
            t = Thread(ThreadStart(lambda: self._serveForever()))
            t.Start()
        self._serverThread = t
        return t    


    def stop(self):
        """ will stop serving on the next request! """
        self._serve = False
    

    def close(self):
        self._serve = False
        time.sleep(0.1)
        self._listener.Close()
        #abort()
        #self._serverThread = None        

    def abort(self):
        if self._serverThread is not None:
            if hasattr(self._serverThread, "Abort"):
                self._serverThread.Abort()
                return True
        return False

    #def __del__(self):
    #    self.close()




def webServe(host, port, feeder):
    def getFromPath(path, fromDate):
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

    def getJsonFeed(fromDate, toDate):
        #lastModifiedFile = feeder.lastModifiedTimeStamp()
        def compare(a, b):
            return cmp(a[1], b[1])
        try:
            lastModified = feeder.formatDateTime(time.time(), utc=True)
            rows = feeder.getFeed(fromDate, toDate)
            rows.sort(compare)
            if rows==[]:
                t = feeder.convertGMTToInteger(fromDate)
            else:
                t = rows[-1][1]
            try:
                lastModified = feeder.formatDateTime(t, utc=True)
            except:
                i = feeder.convertGMTToInteger(t)
                t = feeder.formatDateTime(i, utc=True)
                lastModified = t
            data = rows
            # change to a dictionary of dictionaries  e.g. {file:{time:.., state:...}, ...}
            data = dict([(f, {"time":t, "state":s}) for f, t, s in rows])
            try:
                data = feeder.convertToJson(data)
            except Exception, e:
                print "getJsonFeed   %s" % str(e)
                data = str(data)
        except Exception, e:
            print str(e)
            data = str({"Error": str(e)})
        return data, "application/json", lastModified

    def getHtmlFeed(fromDate, toDate):
        data = getFeedText(fromDate, toDate)
        return data, "text/html"

    def getTextFeed(fromDate, toDate):
        data = getFeedText(fromDate, toDate)
        return data, "text/plain"

    def getFeedText(fromDate, toDate):
        def compare(a, b):
            return cmp(a[1], b[1])
        try:
            rows = feeder.getFeed(fromDate, toDate, True)
            rows.sort(compare)
            data = ""
            for file, eventTime, eventName, isDir in rows:
                data += "%s, %s, %s, %s\n" % (eventTime, eventName, file, isDir)
            data = quoteHtml(data)
            #if True:
            try:
                if rows==[]:
                    lastModified = fromDate
                    #lastModified = feeder.formatDateTime(fromDate, utc=True)
                else:
                    lastModified = rows[-1][1]
                data += "\nlastModified = %s" % lastModified
            except Exception, e:
                print str(e)
                print "t='%s'" % t
        except Exception, e:
            data = str({"Error": str(e)})
        return data

    def quoteHtml(s):
        s = s.replace("&", "&amp;")
        s = s.replace("'", "&apos;").replace('"', "&quot;")
        s = s.replace("<", "&lt;").replace(">", "&gt;")
        return s

    def getText(request):
        data = "--Text--"
        contentType = "text/plain"
        lastModified = None
        headers = {}
        for k in request.Headers.AllKeys:
            headers[k] = request.Headers[k]
        queryStrings = {}
        for k in request.QueryString.Keys:
            queryStrings[k] = request.QueryString[k]
        rawUrl = request.RawUrl
        path = rawUrl.split("?")[0].split("#")[0]
        path = unquote(path.replace("+", " "))

        fromDate = headers.get("Last-Modified", "")
        toDate = None
        fromDate, toDate, cmd = getFromPath(path, fromDate)

        try:
            if cmd=="test":
                data = "TEST path='%s', fromDate='%s', toDate='%s'\n" % (path, fromDate, toDate)
            elif cmd=="count":
                data = "FileCount=%s\n" % feeder.getFileCount(path)
            elif cmd=="html":
                data, contentType = getHtmlFeed(fromDate, toDate)
            elif cmd=="text":
                data, contentType = getTextFeed(fromDate, toDate)
            elif cmd=="name":
                data = "ComputerName='%s', platform='%s'" % (os.environ.get("COMPUTERNAME", "?"), sys.platform)
            elif cmd=="time":
                data = "CurrentTime=%s" % feeder.formatDateTime()
                data += ", GMT = %s" % feeder.formatDateTime(utc=True)
            elif cmd=="shutdown":
                #shutdown()
                data = "shutdown"
            else:
                data, contentType, lastModified = getJsonFeed(fromDate, toDate)
        except Exception, e:
            data = "ERROR: %s" % str(e)
            print data

        headers["Content-type"] = contentType
        if lastModified:
            headers["Last-Modified"] = lastModified
        return data, headers

    s = WebServer2(host=host, port=port)
    s.getText = getText
    s.startServing()
    time.sleep(.2)
    if s.failed:
        print "Failed to start the server. Reason:%s" % self.failedReason
    else:
        print "Serving on http://%s:%s" % (host, port)
    return s


def test():
    import sys
    print "--TESTING--"
    s = WebServer2()
    s.startServing()
    s.exit = sys.exit
    return s

if __name__ == "__main__":
    s = test()







