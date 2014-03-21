#!/usr/bin/python

import time
import sys
import code
from ext.debugger.debug_proxy import DBChecker

def main():
    checker = DBChecker()
    sys.ps1 = "DBC>"
    sys.ps2 = "..."
    l = dict(locals())
    code.interact('Ready.', local=l)
    checker.finish()

if __name__ == "__main__":
    main()
