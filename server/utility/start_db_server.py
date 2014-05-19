from ext.debugger.elt.database import DatabaseServer
import time

server = DatabaseServer()
while not server.closed:
    time.sleep(0.1)
