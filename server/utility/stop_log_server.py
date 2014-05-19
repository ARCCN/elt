from ext.debugger.elt.logger import LogClient

c = LogClient(connect=False)
c.reconnect()
if c.connected:
    c.close()
