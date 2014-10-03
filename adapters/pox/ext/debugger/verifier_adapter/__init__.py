from adapter import Adapter
from pox.core import core

def start_adapter():
    core.openflow.addListeners(Adapter())

def launch():
    core.call_when_ready(start_adapter, "openflow", __name__)
