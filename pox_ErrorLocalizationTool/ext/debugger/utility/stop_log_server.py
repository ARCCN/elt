from ext.debugger.elt import LogClient

c = LogClient(connect=False)
c.reconnect()
if c.connected:
    c.close()
