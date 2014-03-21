from ext.debugger.pox_proxy import LogClient

c = LogClient(connect=False)
c.reconnect()
if c.connected:
    c.close()
