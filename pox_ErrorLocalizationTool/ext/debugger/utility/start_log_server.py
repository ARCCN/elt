from ext.debugger.pox_proxy import LogServer
import time

server = LogServer()
while not server.closed:
    time.sleep(0.1)
