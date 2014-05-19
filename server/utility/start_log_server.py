from ext.debugger.elt.logger.log_server import LogServer
import time

server = LogServer()
while not server.closed:
    time.sleep(0.1)
