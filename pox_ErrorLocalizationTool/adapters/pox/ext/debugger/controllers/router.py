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


class Router(EventMixin):

  def __init__(self):
    self.listenTo(core.openflow)

  def _handle_PacketIn(self, event):
    if event.dpid != 1:
        return
    packet = event.parse()
    try:
        ip = packet.find('ipv4')
        if ip is None or ip.find('udp') is not None:
            raise Exception()
        if ip.srcip.inNetwork(our_network, 24):
            self.send_out_from_our_network(event)
        elif ip.dstip.inNetwork(our_network, 24):
            self.send_to_our_network(event)
    except Exception as e:
        if str(e) != "":
            print 'Router', e
        pass

  def send_out_from_our_network(self, event):
    actions = [of.ofp_action_output(port=outer_network_port)]
    match = of.ofp_match(dl_type=2048, nw_src=our_network)
    event.connection.send(of.ofp_flow_mod(match=match, actions=actions, buffer_id=event.ofp.buffer_id))

  def send_to_our_network(self, event):
    actions = [of.ofp_action_output(port=our_network_port)]
    match = of.ofp_match(dl_type=2048, nw_dst=(our_network, 24))
    fm = of.ofp_flow_mod(match=match, actions=actions, buffer_id=event.ofp.buffer_id)
    event.connection.send(fm)

  def change_port(self):
    global our_network_port, our_network_port_2
    t = our_network_port_2
    our_network_port_2 = our_network_port
    our_network_port = t
    match = of.ofp_match(dl_type=2048, nw_dst=(our_network, 24))
    actions = [of.ofp_action_output(port=our_network_port)]
    fm = of.ofp_flow_mod(match=match, actions=actions, command=of.OFPFC_MODIFY)
    core.openflow.sendToDPID(1, fm)


def launch():
  core.registerNew(Router)
