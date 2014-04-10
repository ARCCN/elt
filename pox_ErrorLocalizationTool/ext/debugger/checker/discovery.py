"""
Slightly modified POX's openflow.discovery module.
"""

from pox.lib.revent               import *
from pox.lib.recoco               import Timer
from pox.lib.packet.ethernet      import LLDP_MULTICAST, NDP_MULTICAST
from pox.lib.packet.ethernet      import ethernet
from pox.lib.packet.lldp          import lldp, chassis_id, port_id, end_tlv
from pox.lib.packet.lldp          import ttl, system_description
import pox.openflow.libopenflow_01 as of
from pox.lib.util                 import dpidToStr
from pox.core import core
from naive_logger import log

import struct
import array
import socket
import time
import copy
from collections import *

LLDP_TTL             = 120 # currently ignored
LLDP_SEND_CYCLE      = 5.0
TIMEOUT_CHECK_PERIOD = 5.0
LINK_TIMEOUT         = 10.0


class LLDPSender (object):
  """
  Cycles through a list of packets, sending them such that it completes the
  entire list every LLDP_SEND_CYCLE.
  """

  SendItem = namedtuple("LLDPSenderItem",
                      ('dpid','portNum','packet'))

  #NOTE: This class keeps the packets to send in a flat list, which makes
  #      adding/removing them on switch join/leave or (especially) port
  #      status changes relatively expensive. This could easily be improved.

  def __init__ (self):
    self._packets = []
    self._timer = None

  def addSwitch (self, dpid, ports):
    """ Ports are (portNum, portAddr) """
    self._packets = [p for p in self._packets if p.dpid != dpid]

    for portNum, portAddr in ports:
      if portNum > of.OFPP_MAX:
        # Ignore local
        continue
      #print dpid, portNum, portAddr
      self._packets.append(LLDPSender.SendItem(dpid, portNum,
       self.create_discovery_packet(dpid, portNum, portAddr)))
    self._setTimer()

  def delSwitch (self, dpid):
    self._packets = [p for p in self._packets if p.dpid != dpid]
    self._setTimer()

  def delPort (self, dpid, portNum):
    self._packets = [p for p in self._packets
                     if p.dpid != dpid or p.portNum != portNum]
    self._setTimer()

  def addPort (self, dpid, portNum, portAddr):
    if portNum > of.OFPP_MAX: return
    self.delPort(dpid, portNum)
    self._packets.append(LLDPSender.SendItem(dpid, portNum,
     self.create_discovery_packet(dpid, portNum, portAddr)))
    self._setTimer()

  def _setTimer (self):
    if self._timer: self._timer.cancel()
    self._timer = None
    if len(self._packets) != 0:
      self._timer = Timer(LLDP_SEND_CYCLE / len(self._packets),
                          self._timerHandler, recurring=True)

  def _timerHandler (self):
    """
    Called by a timer to actually send packet.
    Picks the first packet off the queue, sends it, and puts it back on the
    end of the queue.
    """
    item = self._packets.pop(0)
    self._packets.append(item)
    #NOTE: Changed from original core.openflow
    core.proxy.sendToDPID(item.dpid, item.packet, True)

  def create_discovery_packet (self, dpid, portNum, portAddr):
    """ Create LLDP packet """

    discovery_packet = lldp()

    cid = chassis_id()
    # Maybe this should be a MAC.  But a MAC of what?  Local port, maybe?
    cid.fill(cid.SUB_LOCAL, bytes('dpid:' + hex(long(dpid))[2:-1]))
    discovery_packet.add_tlv(cid)

    pid = port_id()
    pid.fill(pid.SUB_PORT, str(portNum))
    discovery_packet.add_tlv(pid)

    ttlv = ttl()
    ttlv.fill(LLDP_TTL)
    discovery_packet.add_tlv(ttlv)

    sysdesc = system_description()
    sysdesc.fill(bytes('dpid:' + hex(long(dpid))[2:-1]))
    discovery_packet.add_tlv(sysdesc)

    discovery_packet.add_tlv(end_tlv())

    eth = ethernet()
    eth.src = portAddr
    eth.dst = NDP_MULTICAST
    eth.set_payload(discovery_packet)
    eth.type = ethernet.LLDP_TYPE
    po = of.ofp_packet_out(action = of.ofp_action_output(port=of.OFPP_IN_PORT),
                           in_port=portNum, data = eth.pack())
    return po.pack()

  def working(self):
    if self._packets == []:
      return False
    return True


class LinkEvent (Event):
  def __init__ (self, add, link):
    Event.__init__(self)
    self.link = link
    self.added = add
    self.removed = not add

  def portForDPID (self, dpid):
    if self.link.dpid1 == dpid:
      return self.link.port1
    if self.link.dpid2 == dpid:
      return self.link.port2
    return None




class Discovery (EventMixin):
  """
  Component that attempts to discover topology.
  Works by sending out LLDP packets
  discovery application for topology inference
  """

  _eventMixin_events = set([
    LinkEvent,
  ])

  _core_name = "proxy_discovery" # we want to be core.proxy_discovery

  Link = namedtuple("Link",("dpid1","port1","dpid2","port2"))

  def __init__ (self, install_flow = True, explicit_drop = True,
                init_sender = False):
    self.explicit_drop = explicit_drop
    self.install_flow = install_flow
    self.init_sender = init_sender

    self._dps = set()
    self.adjacency = {} # From Link to time.time() stamp
    if self.init_sender:
      self._sender = LLDPSender()
    Timer(TIMEOUT_CHECK_PERIOD, self._expireLinks, recurring=True)

    if core.hasComponent("proxy"):
      self.listenTo(core.proxy)
    else:
      # We'll wait for PROXY (not openflow) to come up
      self.listenTo(core)
    core.register("proxy_discovery", self)

  def _handle_ComponentRegistered (self, event):
    if event.name == "proxy":
      self.listenTo(core.proxy)
      return EventRemove # We don't need this listener anymore

  def _handle_ConnectionUp (self, event):
    """ On datapath join, create a new LLDP packet per port """
    assert event.dpid not in self._dps

    #We dont want to show our presence so installing
    #flow must be commented for now
    if self.install_flow:
      log.debug("Installing flow for %s" % (dpidToStr(event.dpid)))
      msg = of.ofp_flow_mod(match = of.ofp_match(dl_type = ethernet.LLDP_TYPE,
                                                    dl_dst = NDP_MULTICAST))
      msg.actions.append(of.ofp_action_output(port = of.OFPP_CONTROLLER))
      event.connection.switch.send(msg)

    self._dps.add(event.dpid)
    log.debug("ConnectionUp " + str(event.ofp))
    if self.init_sender:
      self._sender.addSwitch(event.dpid, [(p.port_no, p.hw_addr)
                                        for p in event.ofp.ports])

  def _handle_ConnectionDown (self, event):
    """ On datapath leave, delete all associated links """
    assert event.dpid in self._dps

    self._dps.remove(event.dpid)
    if self.init_sender:
      self._sender.delSwitch(event.dpid)

    deleteme = []
    for link in self.adjacency:
      if link.dpid1 == event.dpid or link.dpid2 == event.dpid:
        deleteme.append(link)

    self._deleteLinks(deleteme)

  def _handle_PortStatus (self, event):
    '''
    Update the list of LLDP packets if ports are added/removed

    Add to the list of LLDP packets if a port is added.
    Delete from the list of LLDP packets if a port is removed.
    '''
    # Only process 'sane' ports
    if event.port <= of.OFPP_MAX and self.init_sender:
      if event.added:
        self._sender.addPort(event.dpid, event.port, event.ofp.desc.hw_addr)
      elif event.deleted:
        self._sender.delPort(event.dpid, event.port)

  def _expireLinks (self):
    '''
    Called periodially by a timer to expire links that haven't been
    refreshed recently.
    '''
    curtime = time.time()

    deleteme = []
    for link,timestamp in self.adjacency.iteritems():
      if curtime - timestamp > LINK_TIMEOUT:
        deleteme.append(link)
        log.info('link timeout: %s.%i -> %s.%i' %
                 (dpidToStr(link.dpid1), link.port1,
                  dpidToStr(link.dpid2), link.port2))

    if deleteme:
      self._deleteLinks(deleteme)

  def _handle_PacketIn (self, event):
    """ Handle incoming lldp packets.  Use to maintain link state """
    packet = event.parsed

    if packet.type != ethernet.LLDP_TYPE: return
    if packet.dst != NDP_MULTICAST: return

    if not packet.next:
      log.error("lldp packet could not be parsed")
      return

    assert isinstance(packet.next, lldp)

    if self.explicit_drop:
      if event.ofp.buffer_id != -1:
        log.debug("Dropping LLDP packet %i" % (event.ofp.buffer_id))
        msg = of.ofp_packet_out()
        msg.buffer_id = event.ofp.buffer_id
        msg.in_port = event.port
        #Switch!
        #event.connection.switch.send(msg)

    lldph = packet.next
    if  len(lldph.tlvs) < 3 or \
      (lldph.tlvs[0].tlv_type != lldp.CHASSIS_ID_TLV) or\
      (lldph.tlvs[1].tlv_type != lldp.PORT_ID_TLV) or\
      (lldph.tlvs[2].tlv_type != lldp.TTL_TLV):
      log.error("lldp_input_handler invalid lldp packet")
      return

    def lookInSysDesc():
      r = None
      for t in lldph.tlvs[3:]:
        if t.tlv_type == lldp.SYSTEM_DESC_TLV:
          # This is our favored way...
          for line in t.next.split('\n'):
            if line.startswith('dpid:'):
              try:
                return int(line[5:], 16)
              except:
                pass
          if len(t.next) == 8:
            # Maybe it's a FlowVisor LLDP...
            try:
              return struct.unpack("!Q", t.next)[0]
            except:
              pass
          return None

    originatorDPID = lookInSysDesc()

    if originatorDPID == None:
      # We'll look in the CHASSIS ID
      if lldph.tlvs[0].subtype == chassis_id.SUB_LOCAL:
        if lldph.tlvs[0].id.startswith('dpid:'):
          # This is how NOX does it at the time of writing
          try:
            originatorDPID = int(lldph.tlvs[0].id.tostring()[5:], 16)
          except:
            pass
      if originatorDPID == None:
        if lldph.tlvs[0].subtype == chassis_id.SUB_MAC:
          # Last ditch effort -- we'll hope the DPID was small enough
          # to fit into an ethernet address
          if len(lldph.tlvs[0].id) == 6:
            try:
              s = lldph.tlvs[0].id
              originatorDPID = struct.unpack("!Q",'\x00\x00' + s)[0]
            except:
              pass

    if originatorDPID == None:
      log.warning("Couldn't find a DPID in the LLDP packet")
      return

    # if chassid is from a switch we're not connected to, ignore
    if originatorDPID not in self._dps:
      log.info('Received LLDP packet from unconnected switch')
      return

    # grab port ID from port tlv
    if lldph.tlvs[1].subtype != port_id.SUB_PORT:
      log.warning("Thought we found a DPID, but packet didn't have a port")
      return # not one of ours
    originatorPort = None
    if lldph.tlvs[1].id.isdigit():
      # We expect it to be a decimal value
      originatorPort = int(lldph.tlvs[1].id)
    elif len(lldph.tlvs[1].id) == 2:
      # Maybe it's a 16 bit port number...
      try:
        originatorPort  =  struct.unpack("!H", lldph.tlvs[1].id)[0]
      except:
        pass
    if originatorPort is None:
      log.warning("Thought we found a DPID, but port number didn't " +
                  "make sense")
      return

    if (event.dpid, event.port) == (originatorDPID, originatorPort):
      log.error('Loop detected; received our own LLDP event')
      return

    #print 'LLDP packet in from',chassid,' port',str(portid)

    link = Discovery.Link(originatorDPID, originatorPort, event.dpid,
                          event.port)

    if link not in self.adjacency:
      self.adjacency[link] = time.time()
      print('link detected: %s.%i -> %s.%i' %
               (dpidToStr(link.dpid1), link.port1,
                dpidToStr(link.dpid2), link.port2))
      self.raiseEventNoErrors(LinkEvent, True, link)
    else:
      # Just update timestamp
      self.adjacency[link] = time.time()

    if self.init_sender and self._sender.working():
      event.resend.no_resend()
    return EventHalt # Probably nobody else needs this event

  def _deleteLinks (self, links):
    for link in links:
      del self.adjacency[link]
      self.raiseEvent(LinkEvent, False, link)


  def isSwitchOnlyPort (self, dpid, port):
    """ Returns True if (dpid, port) designates a port that has any
    neighbor switches"""
    for link in self.adjacency:
      if link.dpid1 == dpid and link.port1 == port:
        return True
      if link.dpid2 == dpid and link.port2 == port:
        return True
    return False

  def print_adjacency(self):
    for link in self.adjacency:
      print "%s:%s ---- %s:%s" % (str(link.dpid1), str(link.port1),
                                  str(link.dpid2), str(link.port2))

  def get_other_end(self, dpid, port):
    for link in self.adjacency:
      if link.dpid1 == dpid and link.port1 == port:
        return (link.dpid2, link.port2)
      elif link.dpid2 == dpid and link.port2 == port:
        return (link.dpid1, link.port1)
    return None

  def _handle_PacketOut(self, event):
    packet = event.parsed

    if packet.type != ethernet.LLDP_TYPE: return
    if packet.dst != NDP_MULTICAST: return

    self._sender.delSwitch(event.dpid)

def launch (explicit_drop = False, install_flow = True):
  explicit_drop = str(explicit_drop).lower() == "true"
  install_flow = str(install_flow).lower() == "true"
  core.registerNew(Discovery, explicit_drop=explicit_drop,
                   install_flow=install_flow)