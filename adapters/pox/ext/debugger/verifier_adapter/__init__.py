from adapter import Adapter
from pox.core import core

def start_adapter():
    a = Adapter()
    core.openflow.addListeners(a)
    core.register(a)

def launch():
    core.call_when_ready(start_adapter, "openflow", __name__)
