from .component_launcher import ComponentLauncher
from pox.core import core

def launch():
    core.registerNew(ComponentLauncher)
