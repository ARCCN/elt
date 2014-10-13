from .component_launcher import ComponentLauncher
from pox.core import core, ComponentRegistered


def _handle_ComponentRegistered(event):
    global registered
    registered.append(event)


def launch():
    core.registerNew(ComponentLauncher, registered)


registered = []
core.addListener(ComponentRegistered, _handle_ComponentRegistered)



