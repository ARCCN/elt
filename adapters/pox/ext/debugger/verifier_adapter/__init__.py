from adapter import Adapter
from pox.core import core

def launch():
    core.openflow.addListener(Adapter())
