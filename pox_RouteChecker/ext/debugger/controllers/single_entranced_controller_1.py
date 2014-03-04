from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.openflow.discovery import *
from pox.lib.addresses import IPAddr
import random
from collections import namedtuple


class TestController(EventMixin):

  def __init__(self):
    self.listenTo(core.openflow)
    #self.listenTo(core.openflow_discovery)
    #self.connections = {}
    self.hosts = {}
    #self.restore_good_network()

    next_hop = namedtuple('next_hop', 'forward cyclic cyclic_pred')
    self.in_hops = {
            10:next_hop([4],        [11],       [23]), 
            11:next_hop([51],       [21, 31],   []),
            21:next_hop([51, 4],    [22],       [23]),
            22:next_hop([4],        [23],       []),
            23:next_hop([4],        [21, 10],   []),
            31:next_hop([51, 4],    [32],       [33]),
            32:next_hop([4],        [33],       []),
            33:next_hop([4],        [31, 10],   []),
            4 :next_hop([51],       [],         []),
            51:next_hop([],         [52],       [54]),
            52:next_hop([],         [53],       [54]), 
            53:next_hop([],         [54],       []), 
            54:next_hop([],         [51, 52],   [])
            }
    self.out_hops = {
            54:next_hop([51, 52],   [],         []),
            53:next_hop([52, 54],   [],         []),
            52:next_hop([51],       [],         []),
            51:next_hop([4],        [],         []),
            4:next_hop([10],        [],         []), 
            10:next_hop([],         [],         [])
            }

    self.drop_stats = {}

  def _handle_PacketIn(self, event):

    def get_other(dpid, port):
      for l in core.openflow_discovery.adjacency:
        if l.dpid1 == dpid and l.port1 == port:
          return (l.dpid2, l.port2)
        elif l.dpid2 == dpid and l.port2 == port:
          return (l.dpid1, l.port1)
      return None

    def get_port(src, dst):
      for l in core.openflow_discovery.adjacency:
        if l.dpid1 == src and l.dpid2 == dst:
          return l.port1
        elif l.dpid1 == dst and l.dpid2 == src:
          return l.port2
      return None

    def is_input(packet):
      ip = packet.find("ipv4")
      if ip is not None:
        nw_dst = ip.dstip
      else:
        arp = packet.find("arp")
        if arp is not None:
          nw_dst = arp.protodst
        else:
          return False
      if nw_dst.inNetwork('10.0.1.0/24'):
        return True
      return False


    #select port on src that is connected to dst
    def select_port(packet, dpid, port):
      source = get_other(dpid, port)
      if source is None:
        src = 'Input'
      else:
        src = source[0]
      ports = None
      if is_input(packet):
        if src in self.in_hops[dpid][2]:
          ports = self.in_hops[dpid][0]
        else:
          ports = self.in_hops[dpid][0] + self.in_hops[dpid][1]
      else:
        if src in self.out_hops[dpid][2]:
          ports = self.out_hops[dpid][0]
        else:
          ports = self.out_hops[dpid][0] + self.out_hops[dpid][1]
     
      if ports is None or ports == []:
        return None
      target_dpid = random.choice(ports)
      target_port = get_port(dpid, target_dpid)

      return target_port
      
    packet = event.parse()

    #l2-learning connected hosts
    if packet.src not in self.hosts.keys():
      self.hosts[packet.src] = (event.connection.dpid, event.port)

    #all switches connected
    if True:
      po = of.ofp_packet_out()
      po.buffer_id = event.ofp.buffer_id
      po.in_port = event.port
      p = None
      
      #flooding to neightbor hosts
      if packet.dst.isMulticast():
        for host in self.hosts.keys():
          target_dpid, target_port = self.hosts[host]
          if event.connection.dpid == target_dpid and event.port != target_port:
              po.actions.append(of.ofp_action_output(port = target_port))

      #connected to host      
      elif packet.dst in self.hosts:
        target_dpid, target_port = self.hosts[packet.dst]
        #we are directly connected to target host
        if event.connection.dpid == target_dpid and event.port != target_port:
          #print "sending to ", event.connection.dpid, target_port
          po.actions.append(of.ofp_action_output(port = target_port))
          event.connection.send(po)
          return

      if packet.type == 0x88cc:
        return
      out_port = select_port(packet, event.connection.dpid, event.port)
      if out_port is None:
        pass
      else:
        po.actions.append(of.ofp_action_output(port=out_port))
      if packet.find("ipv4") is not None:
        if random.random() < 0.1:
          po.actions = []
          print "drop", packet.find("ipv4").srcip, '->', \
            packet.find("ipv4").dstip, 'at', event.connection.dpid
          addr = (packet.find('ipv4').srcip, packet.find('ipv4').dstip)
          if addr not in self.drop_stats:
            self.drop_stats[addr] = {}
          if event.connection.dpid not in self.drop_stats[addr]:
            self.drop_stats[addr][event.connection.dpid] = 0
          self.drop_stats[addr][event.connection.dpid] += 1
      event.connection.send(po)
        
  def print_drop_stats(self):
    for addr, dic in self.drop_stats.items():
      print '\n', addr, '\n'
      for dpid, count in dic.items():
        print '\t', dpid, ': ', count

def launch():
  core.registerNew(TestController)
