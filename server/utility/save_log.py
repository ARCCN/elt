import sys
from ext.debugger.elt import LogClient

c = LogClient(connect=True)
if len(sys.argv) > 1:
    c.log_dir = sys.argv[1]
c.save_log()
