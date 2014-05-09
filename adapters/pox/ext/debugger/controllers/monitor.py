from pox.core import core
import pox.openflow.libopenflow_01 as of
import random
from pox.lib.revent import EventMixin
from pox.lib.addresses import IPAddr
from pox.lib.packet import *
import code

our_network = IPAddr('10.0.0.0')
server_port = 4
our_network_port = 2
our_network_port_2 = 3
outer_network_port = 1



class Monitor(EventMixin):

  def __init__(self):
      self.listenTo(core.openflow)

  def _handle_PacketIn(self, event):
      packet = event.parse()
      try:
          if (packet.find('dhcp') is None and
              packet.find('ipv6') is None and
              packet.find('udp') is None and
              not packet.dst.isMulticast()
             ):
              print 'PacketIn on %s' % event.dpid
              while packet is not None and not isinstance(packet, basestring):
                  print packet
                  packet = packet.next
      except:
          pass

  def output_ping(self):
      eth = ethernet()
      eth.type = ethernet.IP_TYPE
      ip = ipv4(srcip=IPAddr("10.0.1.1"), dstip=IPAddr("10.0.0.1"))
      ip.protocol = ipv4.ICMP_PROTOCOL
      e = icmp(type=0, code=0)
      e.next = None
      ip.payload = e
      eth.payload = ip
      po = of.ofp_packet_out(actions=[of.ofp_action_output(port=1)], data=eth)
      core.openflow.sendToDPID(2, po)

  def output_http(self):
      eth = ethernet()
      eth.type = ethernet.IP_TYPE
      ip = ipv4(srcip=IPAddr("10.0.1.1"), dstip=IPAddr("10.0.0.255"))
      ip.protocol = ipv4.TCP_PROTOCOL
      tp = tcp(srcport=10000, dstport=80, seq=0, ack=0, off=5, win=1)
      ip.payload = tp
      eth.payload = ip
      po = of.ofp_packet_out(actions=[of.ofp_action_output(port=1)], data=eth)
      core.openflow.sendToDPID(2, po)



def launch():
  core.registerNew(Monitor)
