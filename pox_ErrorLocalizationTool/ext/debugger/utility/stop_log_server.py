from ext.debugger.pox_proxy.logger import *

c = LogClient()
if c.connected:
    c.close()
