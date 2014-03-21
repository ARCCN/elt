from ext.debugger.pox_proxy import DatabaseClient

c = DatabaseClient(connect=False)
c.reconnect()
if c.connected:
    c.close()
