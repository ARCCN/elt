from ext.debugger.elt import DatabaseClient

c = DatabaseClient(connect=False)
c.reconnect()
if c.connected:
    c.close()
