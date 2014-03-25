from pox.core import core
import pox.openflow.libopenflow_01 as of
import random
from pox.lib.revent import EventMixin

class Interrupter(EventMixin):

  def __init__(self):
    self.listenTo(core.openflow)
    self.hosts = {}
    self.base = {}

  def _handle_PacketIn(self, event):

    packet = event.parse()

    match = of.ofp_match.from_packet(packet)
    wc = random.choice(range(3))
    if wc > 0:
        match.dl_vlan_pcp = None
    if wc > 1:
        match.dl_vlan = None

    actions = [of.ofp_action_output(port = random.choice(range(1, 4)))]
    priority = random.choice([100, 1000, 10000])
    flow_mod = of.ofp_flow_mod(match=match, actions=actions, priority=priority)
    event.connection.send(flow_mod)

def launch():
  core.registerNew(Interrupter)
