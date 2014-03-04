from ext.debugger.pox_proxy.database import *

c = DatabaseClient()
if c.connected:
    c.close()
