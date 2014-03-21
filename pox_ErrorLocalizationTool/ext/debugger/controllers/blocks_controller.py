from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.openflow.discovery import *
from pox.lib.addresses import IPAddr


class TestController(EventMixin):

  IN = 1
  OUT = 2
  CHECK = 3
  LOOP = 4
  IDLE = 10
  HARD = 20

  def __init__(self):
    self.listenTo(core.openflow)
    self.listenTo(core.openflow_discovery)
    self.connections = {}
    self.hosts = {}
    self.restore_good_network()

  def _handle_LinkEvent(self, event):
    pass

  def restore_good_network(self):
    self.good_network = "10.0.0.0/24"

  def change_good_network(self):
    self.good_network = "10.0.0.0/23"

  def _handle_PacketIn(self, event):

    #select port on src that is connected to dst
    def select_port(src, dst):
      if src is None or dst is None:
        return None
      for l in core.openflow_discovery.adjacency:
        if l.dpid1 == src and l.dpid2 == dst:
          return l.port1
        elif l.dpid1 == dst and l.dpid2 == src:
          return l.port2
      return None

    #select port to output to
    def select_for_in(dpid, check):
      if dpid == self.IN:
        t = self.OUT
      elif dpid == self.OUT:
        t = self.IN
      else:
        t = None

      if check:
        return select_port(dpid, self.CHECK)
      else:
        return select_port(dpid, t)

    #return port from check to loop
    def check_port():
        return select_port(self.CHECK, self.LOOP)
     
    print "PacketIn on %s:%s" % (event.connection.dpid, event.port)
    packet = event.parse()

    #l2-learning connected hosts
    if packet.src not in self.hosts.keys():
      self.hosts[packet.src] = (event.connection.dpid, event.port)
      print "added ", packet.src, event.connection.dpid, event.port

    #all switches connected
    if len(self.connections.keys()) == 4:
      fm1 = of.ofp_flow_mod()
      fm1.match = of.ofp_match.from_packet(packet, event.port)
      p = None
      
      #flooding to neightbor hosts
      if packet.dst.isMulticast():
        print "flood"
        for host in self.hosts.keys():
          target_dpid, target_port = self.hosts[host]
          print target_dpid, target_port, event.port
          if event.connection.dpid == target_dpid and event.port != target_port:
            print "output ", target_port
            fm1.actions.append(of.ofp_action_output(port = target_port))
            fm1.buffer_id = event.ofp.buffer_id

      #connected to host      
      elif packet.dst in self.hosts:
        target_dpid, target_port = self.hosts[packet.dst]
        #we are directly connected to target host
        if event.connection.dpid == target_dpid and event.port != target_port:
          print "sending to ", event.connection.dpid, target_port
          fm1.actions.append(of.ofp_action_output(port = target_port))
          fm1.idle_timeout = self.IDLE
          fm1.hard_timeout = self.HARD
          fm1.buffer_id = event.ofp.buffer_id
          event.connection.send(fm1)
          return

      #creating path
      if event.connection.dpid == self.IN or event.connection.dpid == self.OUT:
        if event.connection.dpid == self.IN:
          other_side = self.OUT
        else:
          other_side = self.IN
        #from first hop to check|second
        check_needed = self.isCheckNeeded(packet)
        p = select_for_in(event.connection.dpid, check_needed)
        if p != event.port and p is not None:
          fm1.actions.append(of.ofp_action_output(port = p))
          fm1.idle_timeout = self.IDLE
          fm1.hard_timeout = self.HARD
          fm1.buffer_id = event.ofp.buffer_id
          event.connection.send(fm1)

          if check_needed:
            #from check to second
            fm1.match.in_port = check_port()
            fm1.actions = []
            p1 = select_port(self.CHECK, other_side)
            if p1 is not None:
              fm1.actions.append(of.ofp_action_output(port = p1))
              fm1.idle_timeout = self.IDLE
              fm1.hard_timeout = self.HARD
              fm1.buffer_id = -1

              core.openflow.sendToDPID(self.CHECK, fm1)
         
        elif len(fm1.actions) != 0:
          event.connection.send(fm1)
        #event.connection.send(po)
 
      elif event.connection.dpid == self.CHECK:
        #send all packets to loopback
        if event.port != check_port():
          fm2 = of.ofp_flow_mod()
          fm2.match = of.ofp_match.from_packet(packet)
          fm2.match.in_port = event.port
          fm2.actions.append(of.ofp_action_output(port = check_port()))
          fm2.idle_timeout = self.IDLE
          fm2.hard_timeout = self.HARD
          fm2.buffer_id = event.ofp.buffer_id
          event.connection.send(fm2)

      elif event.connection.dpid == self.LOOP:
        #send all packet back to input port
        fm3 = of.ofp_flow_mod()
        fm3.match = of.ofp_match.from_packet(packet, event.port)
        fm3.actions.append(of.ofp_action_output(port = of.OFPP_IN_PORT))
        fm3.idle_timeout = self.IDLE
        fm3.hard_timeout = self.HARD
        fm3.buffer_id = event.ofp.buffer_id
        event.connection.send(fm3)

  def _handle_ConnectionUp(self, event):
    id = event.connection.dpid
    if id == self.OUT:
      self.connections["out"] = event.connection
    elif id == self.CHECK:
      self.connections["check"] = event.connection
    elif id == self.LOOP:
      self.connections["loop"] = event.connection
    elif id == self.IN:
      self.connections["in"] = event.connection

  def isCheckNeeded(self, packet):
    ip = packet.find("ipv4")
    if ip is not None and (ip.srcip.inNetwork(self.good_network)):
      print ip.srcip, " not needed"
      return False
    else:
      return True

def launch():
  core.registerNew(TestController)
