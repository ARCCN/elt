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
    #self.listenTo(core.openflow_discovery)
    self.hosts = {}

    self.in_routes = [
            (1, 2, 4), 
            (1, 2, 3, 4), 
            #(1, 2, 3, 2, 4),
            (1, 3, 4),
            (1, 3, 2, 4)
            #(1, 3, 2, 3, 4)
            ]
    self.out_routes = [route[::-1] for route in self.in_routes]

    #Where not to send multicasts
    self.forbidden = {
            #src_ip source dest
            "10.0.0.0/24": [(4, 2),
                            (4, 3),
                            (2, 1),
                            (3, 1),
                            (2, 3),
                            (3, 2)], 
            "10.0.1.0/24": [(1, 2),
                            (1, 3),
                            (2, 4),
                            (3, 4),
                            (2, 3),
                            (3, 2)]
            }    
    self.base = {}

  def get_routes(self, packet):
    def select_routes(srcip):
        if not isinstance(srcip, IPAddr):
            return []
        if srcip.inNetwork('10.0.0.0/24'):
            return random.sample(self.in_routes,
                    random.randrange(1, len(self.in_routes)))
        elif srcip.inNetwork('10.0.1.0/24'):
            return random.sample(self.out_routes,
                    random.randrange(1, len(self.out_routes)))
        else:
            return []


    tp_src = tp_dst = None
    srcip = get_srcip(packet)
    dstip = get_dstip(packet)
    ip = packet.find('ipv4')
    if ip is not None:
        tp = ip.next
        if isinstance(tp, udp) or isinstance(tp, tcp):
            tp_src = tp.srcport
            tp_dst = tp.dstport
        elif isinstance(tp, icmp):
            tp_src = tp.type
            tp_dst = tp.code
    entry = base_entry(srcip, dstip, tp_src, tp_dst)
    if entry not in self.base:
        self.base[entry] = select_routes(srcip)
        if entry[2] is not None:
            print entry
            for route in self.base[entry]:
                print route

    return self.base[entry]


  def _handle_PacketIn(self, event):

    def get_next_hops(routes, dpid, src_dpid):
        if src_dpid is None:
            return set([route[1] for route in routes if route[0] == dpid])
        else:
            result = set()
            for route in routes:
                for i in range(1, len(route) - 1):
                    if route[i] == dpid and route[i-1] == src_dpid:
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

    def get_port(src, dst):
      for l in core.openflow_discovery.adjacency:
        if l.dpid1 == src and l.dpid2 == dst:
          return l.port1
        elif l.dpid1 == dst and l.dpid2 == src:
          return l.port2
      return None

    

      
    packet = event.parse()

    #l2-learning connected hosts
    if packet.src not in self.hosts.keys():
        self.hosts[packet.src] = (event.connection.dpid, event.port)

    po = of.ofp_packet_out()
    po.buffer_id = event.ofp.buffer_id
    po.in_port = event.port

    srcip = get_srcip(packet)
    dstip = get_dstip(packet)
    if srcip is not None and packet.dst.isMulticast():
        #Test whether this packet is forbidden
        for address, links in self.forbidden.items():
            if srcip.inNetwork(address):
                #print srcip, 'inNetwork', address
                source = get_other(event.connection.dpid, event.port)
                if source is not None:
                    source_dpid = source[0]
                else:
                    source_dpid = None
                if (source_dpid, event.connection.dpid) in links:
                    #print srcip, "packet", source_dpid, "->", event.connection.dpid, "forbidden"
                    event.connection.send(po)
                    return


    if packet.dst.isMulticast():
        '''
        #To hosts
        for host in self.hosts.keys():
            target_dpid, target_port = self.hosts[host]
            if event.connection.dpid == target_dpid and event.port != target_port:
                po.actions.append(of.ofp_action_output(port=target_port))
        #To switches
        for neighbor, port in get_neighbors(event.connection.dpid).items():
            srcip = get_srcip(packet)
            if srcip is not None:
                for address, links in self.forbidden.items():
                    if srcip.inNetwork(address):
                        if (event.connection.dpid, neighbor) not in links:
                            po.actions.append(of.ofp_action_output(port=port))
        '''
        #print "flood at", event.connection.dpid
        po.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
        event.connection.send(po)
        return

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
        #LLDP
        return

    #Our custom routing
    if srcip is None or dstip is None:
        event.connection.send(po)
        return

    #Our packet has srcip and dstip
    routes = self.get_routes(packet)
    source = get_other(event.connection.dpid, event.port)
    if source is not None:
        source_dpid = source[0]
    else:
        source_dpid = None

    next_hops = get_next_hops(routes, event.connection.dpid, source_dpid)
    if len(next_hops) == 0:
        #No next hops
        event.connection.send(po)
        return
    next_hop = random.choice(list(next_hops))
    #print "selected", next_hop, "from", next_hops, "at", \
    #    event.connection.dpid, '\n'
    out_port = get_port(event.connection.dpid, next_hop)
    if out_port is None:
        #print 'Adjacency error. No port from', event.connection.dpid, 'to', next_hop
        event.connection.send(po)
        return
    po.actions.append(of.ofp_action_output(port=out_port))
    event.connection.send(po)
        
def launch():
  core.registerNew(TestController)
