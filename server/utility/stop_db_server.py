from ext.debugger.elt.database import DatabaseClient

c = DatabaseClient(connect=False)
c.reconnect()
if c.connected:
    c.close()
