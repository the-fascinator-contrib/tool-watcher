import sys

sys.path.append("../common")
sys.path.append("../jsonfeed")
sys.path.append("../config")

from filesystem import FileSystem
from config import Config
from jsonfeed import JsonFeed

import BaseHTTPServer, datetime


class PasteServer(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        self.fromDate = self.headers.getheader("Last-Modified")
        self.toDate = None
        
        self.__getFeed()
    
    def __getFeed(self):
        fs = FileSystem(".")
        json = JsonFeed(db, fs=fs, fromDate=self.fromDate, toDate=self.toDate)
        lastModifiedFile = json.lastModifiedTimeStamp()
        self.send_header("Content-type", "application/json")
        self.send_header("Last-Modified", lastModifiedFile)
        self.wfile.write(json.getFeed())

if __name__ == "__main__":
    fs = FileSystem(".")
    config = Config(fileSystem=fs)
    db = None
    if config.db:
        dbPath = "../db/%s" % config.db
        sys.path.append(dbPath)
        dbLib = "%sdb" % config.db
        __import__(dbLib)
        db = sys.modules[dbLib].Database
    db = db()
    global db
    server = BaseHTTPServer.HTTPServer((config.host,config.port), PasteServer)
    server.serve_forever()
    
