from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.openflow.discovery import *

sender = LLDPSender()

class LLDP_Switch(EventMixin):
  def __init__(self, connection, ports):
    self.connection = connection
    self.ports = ports
    sender.addSwitch(connection.dpid, [(p.port_no, p.hw_addr) for p in ports])
    self.listenTo(connection)
  
  def _handle_PacketIn(self, event):
    print "PacketIn on %s:%s" % (event.connection.dpid, event.port)


class LLDP_Test(EventMixin):
  def __init__(self):
    self.listenTo(core.openflow)

  def _handle_ConnectionUp(self, event):
    sw = LLDP_Switch(event.connection, event.ofp.ports)

def launch():
  core.registerNew(LLDP_Test)
