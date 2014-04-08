from pox.core import core
import pox.openflow.libopenflow_01 as of
import random
from pox.lib.revent import EventMixin
from pox.lib.addresses import IPAddr

our_network = IPAddr('10.0.0.0')
server_port = 4
our_network_port = 2
our_network_port_2 = 3
outer_network_port = 1


class Server(EventMixin):

  def __init__(self):
    self.listenTo(core.openflow)

  def _handle_PacketIn(self, event):
    if event.dpid != 1:
        return
    packet = event.parse()
    try:
        if (packet.find('ipv4').dstip.inNetwork(our_network, 24) and
                packet.find('tcp').dstport == 80):
            self.send_to_server(event)
    except:
        pass

  def send_to_server(self, event):
    actions = [of.ofp_action_output(port=server_port)]
    match = of.ofp_match(dl_type=2048, nw_dst=(our_network, 24),
                         nw_proto=of.ipv4.TCP_PROTOCOL, tp_dst=80)
    fm = of.ofp_flow_mod(match=match, actions=actions, buffer_id=event.ofp.buffer_id)
    #print fm
    event.connection.send(fm)


def launch():
  core.registerNew(Server)
