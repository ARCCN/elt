#!/bin/bash

''''echo -n
export OPT="-u -O"
export FLG=""

if [ -x pypy/bin/pypy ]; then
  exec pypy/bin/pypy $OPT "$0" $FLG "$@"
fi

if [ "$(type -P python2.7)" != "" ]; then
  exec python2.7 $OPT "$0" $FLG "$@"
fi
exec python $OPT "$0" $FLG "$@"
'''

import socket
import select
import threading
import os
import sys
import exceptions
from errno import EAGAIN, ECONNRESET
import time

from ext.debugger.debug_proxy import ProxyTask
import pox.lib.recoco as recoco

scheduler = None
task = None

curargs = {}

def process_args():
  for arg in sys.argv[1:]:
    arg = arg[2:].split("=", 1)
    if len(arg) == 1: arg.append(True)
    curargs[arg[0]] = arg[1]
  if "port" not in curargs:
    curargs["port"] = 6633
  if "address" not in curargs:
    curargs["address"] = "0.0.0.0"
  if "target_port" not in curargs:
    curargs["target_port"] = 6632



def main():
  process_args()
  try:
    scheduler = recoco.Scheduler(daemon = True)
    task = ProxyTask(curargs['port'], curargs['address'], \
            target_port=curargs['target_port'])
    while (True):
      time.sleep(5)
  except Exception as e:
    print(str(e))

if __name__ == '__main__':
  main()
