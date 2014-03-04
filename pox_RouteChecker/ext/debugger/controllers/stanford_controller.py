from pox.core import core
from pox.lib.packet import tcp, udp, icmp
import pox.openflow.libopenflow_01 as of
from pox.openflow.discovery import *
from pox.lib.addresses import IPAddr
import random
from collections import namedtuple

base_entry = namedtuple('base_entry', 'src_ip dst_ip tp_src tp_dst')

def get_srcip(packet):
      nw_src = None
      ip = packet.find("ipv4")
      if ip is not None:
        nw_src = ip.srcip
      else:
        arp = packet.find("arp")
        if arp is not None:
          nw_src = arp.protosrc
      return nw_src

def get_dstip(packet):
      nw_dst = None
      ip = packet.find("ipv4")
      if ip is not None:
        nw_dst = ip.dstip
      else:
        arp = packet.find("arp")
        if arp is not None:
          nw_dst = arp.protodst
      return nw_dst

class TestController(EventMixin):
      
  def __init__(self):
    self.listenTo(core.openflow)
    self.listenTo(core.openflow_discovery)
    self.hosts = {}

    self.routes = {
            ("10.0.0.0/24", "10.0.1.0/24") : [(2, 1, 4)], 
            ("10.0.0.0/24", "10.0.2.0/24") : [(2, 1, 5, 6)],
            ("10.0.0.0/24", "10.0.3.0/24") : [(2, 1, 4, 7)],
            
            ("10.0.1.0/24", "10.0.0.0/24") : [
                                              (4, 7, 4, 1, 2),
                                              (4, 7, 6, 4, 1, 2),
                                              (4, 7, 6, 5, 1, 2),
                                             ],
            ("10.0.1.0/24", "10.0.2.0/24") : [(4, 6)],
            ("10.0.1.0/24", "10.0.3.0/24") : [(4, 7)],
            
            ("10.0.2.0/24", "10.0.0.0/24") : [
                                            (6, 7, 6, 5, 1, 2),
                                            (6, 7, 4, 1, 2),
                                            (6, 7, 6, 4, 1, 2),
                                            ],
            ("10.0.2.0/24", "10.0.1.0/24") : [(6, 4)],
            ("10.0.2.0/24", "10.0.3.0/24") : [(6, 7)],
            
            ("10.0.3.0/24", "10.0.0.0/24") : [(7, 4, 1, 2)],
            ("10.0.3.0/24", "10.0.1.0/24") : [(7, 4)],
            ("10.0.3.0/24", "10.0.2.0/24") : [(7, 6)],

            }  

    self.additional = {
            ("10.0.1.0/24", "10.0.0.0/24") : [(4, 1, 2)],
            ("10.0.2.0/24", "10.0.0.0/24") : [(6, 5, 1, 2), (6, 4, 1, 2)]
            }
    
    self.networks = [
            ("10.0.0.0/24", 2),
            ("10.0.1.0/24", 4),
            ("10.0.2.0/24", 6),
            ("10.0.3.0/24", 7)
            ]

    self.base = {}

  def get_routes(self, packet, main=True):

    tp_src = tp_dst = None
    srcip = get_srcip(packet)
    dstip = get_dstip(packet)
    
    if main:
        for key, value in self.routes.items():
            nw_src, nw_dst = key
            if srcip.inNetwork(nw_src) and dstip.inNetwork(nw_dst):
                return value
    else:
        for key, value in self.additional.items():
            nw_src, nw_dst = key
            if srcip.inNetwork(nw_src) and dstip.inNetwork(nw_dst):
                return value


    return []


  def _handle_PacketIn(self, event):

    def get_port(src, dst):
      for l in core.openflow_discovery.adjacency:
        if l.dpid1 == src and l.dpid2 == dst:
          return l.port1
        elif l.dpid1 == dst and l.dpid2 == src:
          return l.port2
      return None


    def get_next_hops(routes, dpid, src_dpid, check_adjacency=True):
        if src_dpid is None:
            return set([route[1] for route in routes \
                if route[0] == dpid and not \
                ( check_adjacency and get_port(dpid, route[1]) is None ) ])
        else:
            result = set()
            for route in routes:
                for i in range(1, len(route) - 1):
                    if route[i] == dpid and route[i-1] == src_dpid:
                        if not (check_adjacency and get_port(dpid, route[i+1]) is None) :
                            result.add(route[i+1])
            return result

    def get_neighbors(dpid):
        result = {}
        for l in core.openflow_discovery.adjacency:
            if l.dpid1 == dpid:
                result[l.dpid2] = l.port1
            elif l.dpid2 == dpid:
                result[l.dpid1] = l.port2
        return result


    def get_other(dpid, port):
      for l in core.openflow_discovery.adjacency:
        if l.dpid1 == dpid and l.port1 == port:
          return (l.dpid2, l.port2)
        elif l.dpid2 == dpid and l.port2 == port:
          return (l.dpid1, l.port1)
      return None

   
    def get_proto(packet):
        ip = packet.find('ipv4')
        if ip is None:
            arp = packet.find('arp')
            if arp is None:
                lldp = packet.find('lldp')
                if lldp is None:
                    return "unknown non-ip"
                else:
                    return 'lldp'
            else:
                return 'arp'
        else:
            tp = ip.next
            if isinstance(tp, tcp):
                return 'tcp'
            elif isinstance(tp, udp):
                return 'udp'
            elif isinstance(tp, icmp):
                return 'icmp'
            else:
                return 'unknown ip'


      
    packet = event.parse()

    #l2-learning connected hosts
    if packet.src not in self.hosts.keys():
        self.hosts[packet.src] = (event.connection.dpid, event.port)

    po = of.ofp_packet_out()
    po.buffer_id = event.ofp.buffer_id
    po.in_port = event.port

    fm = of.ofp_flow_mod()
    fm.buffer_id = event.ofp.buffer_id
    fm.in_port = event.port

    srcip = get_srcip(packet)
    dstip = get_dstip(packet)
    
    if packet.type == 0x88cc:
        #LLDP
        return

    #Our custom routing
    if srcip is None or dstip is None:
        event.connection.send(po)
        return

    #Directly connected?
    for network, switch in self.networks:
        if dstip.inNetwork(network):
            if switch == event.connection.dpid:
                if packet.dst.isMulticast() or packet.dst not in self.hosts:
                    po.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
                    event.connection.send(po)
                    return
                else:
                    fm.match = of.ofp_match.from_packet(packet, event.port)
                    fm.actions.append(of.ofp_action_output\
                            (port=self.hosts[packet.dst][1]))
                    event.connection.send(fm)
                    return
            else:
                break

    #Our packet has srcip and dstip
    routes = self.get_routes(packet, main=True)
    source = get_other(event.connection.dpid, event.port)
    if source is not None:
        source_dpid = source[0]
    else:
        source_dpid = None

    next_hops = get_next_hops(routes,event.connection.dpid, \
            source_dpid, check_adjacency=True)
    if len(next_hops) == 0:
        #No next hops - adjacency filtered?
        routes = self.get_routes(packet, main=False)
        next_hops = get_next_hops(routes, event.connection.dpid, \
                source_dpid, check_adjacency=True)
        if len(next_hops) == 0:
            #At least we tried
            event.connection.send(po)
            return
    if len(next_hops) == 1:
        #Single route - hard flow
        for hop in next_hops:
            out_port = get_port(event.connection.dpid, hop)
            print srcip, dstip, event.connection.dpid, "fm to", hop, get_proto(packet), packet.src, packet.dst
        if out_port is None:
            print "adjacency error"
            return
        fm.match = of.ofp_match.from_packet(packet, event.port)
        fm.hard_timeout=10
        if out_port == event.port:
            fm.actions.append(of.ofp_action_output(port=of.OFPP_IN_PORT))
        else:
            fm.actions.append(of.ofp_action_output(port=out_port))
        event.connection.send(fm)
        return
    else:
        #Multiple routes - random choice
        hop =  random.choice(list(next_hops))
        print srcip, dstip, event.connection.dpid, "po to", hop, get_proto(packet), packet.src, packet.dst
        out_port = get_port(event.connection.dpid, hop)
        if out_port is None:
            print "adjacency error"
            return
        if out_port == event.port:  
            po.actions.append(of.ofp_action_output(port=of.OFPP_IN_PORT))
        else:
            po.actions.append(of.ofp_action_output(port=out_port))
        event.connection.send(po)
        return
        
def launch():
  core.registerNew(TestController)
