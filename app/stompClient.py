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


import stomp
import os


class StompClient(object):
    def __init__(self, config, utils):
        self.__config = config
        self.__utils = utils
        self.start()
    
    def start(self):
        """ Connect to stomp server """
        print "Connecting to STOMP server..."
        host = self.__config.messaging.get("host")
        port = self.__config.messaging.get("port")
        self.__stomp = stomp.Connection(host_and_ports = [ (host, port) ],
                                        reconnect_sleep_initial = 15.0,
                                        reconnect_sleep_increase = 0.0,
                                        reconnect_sleep_max = 15.0)
        self.__stomp.set_listener("main", StompListener(self))
        self.__stomp.start()
        self.__stomp.connect()
    
    def stop(self):
        if self.__stomp is not None:
            print "Disconnecting from STOMP server..."
            self.__stomp.stop()
    
    def queueUpdate(self, file, eventName):
        print "Queuing '%s' for '%s'" % (eventName, file)
        try:
            configFile = self.__config.messaging.get("configFile")
            if configFile is None:
                print "No messaging configFile defined!"
            else:
                fp = open(configFile)
                jsonConf = self.__utils.convertFromJson(fp.read())
                fp.close()
                jsonConf["source"] = "watcher"
                jsonConf["configDir"] = os.path.split(configFile)[0]
                jsonConf["configFile"] = configFile
                jsonConf["oid"] = file
                if eventName == "del":
                    jsonConf["deleted"] = "true"
                jsonStr = self.__utils.convertToJson(jsonConf)
                self.__stomp.send(jsonStr, destination="/queue/ingest")
        except Exception, e:
            msg = "Error in queueUpdate(file='%s', eventName='%s') - '%s'"
            msg = msg % (file, eventName, str(e))



class StompListener(stomp.ConnectionListener):
    def __init__(self, client):
       self.__client = client
    
    def on_connecting(self, host_and_port):
        print "Connecting to %s:%s" % host_and_port
    
    def on_connected(self, headers, body):
        print "Connected: %s (%s)" % (headers, body)
    
    def on_disconnected(self, headers, body):
        print "Disconnected, attempting to reconnect..."
        self.__client.start()




