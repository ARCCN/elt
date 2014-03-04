import socket
import os
import sys
import exceptions
from errno import EAGAIN, ECONNRESET

from pox.openflow.of_01 import deferredSender, classes
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import EventMixin, Event
from naive_logger import log

class MessageIn( Event ):
  def __init__(self, connection, ofp):
    Event.__init__(self)
    self.connection = connection
    self.ofp = ofp

class StatsIn( Event ):
  def __init__(self, connection, parts):
    Event.__init__(self)
    self.connection = connection
    self.ofp = parts

class BaseConnection (EventMixin):
  """
  A Connection object represents a single TCP session with an
  openflow-enabled switch.
  If the switch reconnects, a new connection object is instantiated.
  """
  """
  _eventMixin_events = set([
    ConnectionUp,
    ConnectionDown,
    PortStatus,
    FlowRemoved,
    PacketIn,
    ErrorIn,
    BarrierIn,
    RawStatsReply,
    SwitchDescReceived,
    FlowStatsReceived,
    AggregateFlowStatsReceived,
    TableStatsReceived,
    PortStatsReceived,
    QueueStatsReceived,
    FlowRemoved,
  ])
  """
  _eventMixin_events = set([
    MessageIn                          
  ])
  # Globally unique identifier for the Connection instance
  #ID = 0

  def msg (self, m):
    #print str(self), m
    log.debug(str(self) + " " + str(m))
  def err (self, m):
    #print str(self), m
    log.error(str(self) + " " + str(m))
  def info (self, m):
    #print str(self), m
    log.info(str(self) + " " + str(m))

  def __init__ (self, sock = None, ID = None):
    self._previous_stats = []

    #self.ofnexus = _dummyOFNexus
    self.sock = sock
    self.buf = ''
    self.ID = ID
    # TODO: dpid and features don't belong here; they should be eventually
    # be in topology.switch
    #self.dpid = None
    #self.features = None
    self.disconnected = False
    self.connect_time = None

    #self.send(of.ofp_hello())

    #TODO: set a time that makes sure we actually establish a connection by
    #      some timeout

  def fileno (self):
    return self.sock.fileno()

  def close (self):
    if not self.disconnected:
      self.info("closing connection")
    else:
      #self.msg("closing connection")
      pass
    try:
      self.sock.shutdown(socket.SHUT_RDWR)
    except:
      pass
    try:
      self.sock.close()
    except:
      pass

  def disconnect (self):
    """
    disconnect this Connection (usually not invoked manually).
    """
    if self.disconnected:
      self.err("already disconnected!")
    self.msg("disconnecting")
    self.disconnected = True
    try:
      self.sock.shutdown(socket.SHUT_RDWR)
    except:
      pass
    if self.dpid != None:
      self.raiseEventNoErrors(ConnectionDown, self)

  def send (self, data):
    """
    Send raw data to the switch.

    Generally, data is a bytes object.  If not, we check if it has a pack()
    method and call it (hoping the result will be a bytes object).  This
    way, you can just pass one of the OpenFlow objects from the OpenFlow
    library to it and get the expected result, for example.
    """
    if self.disconnected: return
    if type(data) is not bytes:
      if hasattr(data, 'pack'):
        data = data.pack()

    if deferredSender.sending:
      log.debug("deferred sender is sending!")
      deferredSender.send(self, data)
      return
    try:
      l = self.sock.send(data)
      if l != len(data):
        self.msg("Didn't send complete buffer.")
        data = data[l:]
        deferredSender.send(self, data)
    except socket.error as (errno, strerror):
      if errno == EAGAIN:
        self.msg("Out of send buffer space.  " +
                 "Consider increasing SO_SNDBUF.")
        deferredSender.send(self, data)
      else:
        self.msg("Socket error: " + strerror)
        self.disconnect()

  def read (self):
    """
    Read data from this connection.  Generally this is just called by the
    main OpenFlow loop below.

    Note: This function will block if data is not available.
    """
    #log.debug("Reading from " + str(self))
    d = self.sock.recv(2048)
    if len(d) == 0:
      return False
    self.buf += d
    l = len(self.buf)
    while l > 4:
      if ord(self.buf[0]) != of.OFP_VERSION:
        log.debug("Bad OpenFlow version (" + str(ord(self.buf[0])) +
                    ") on connection " + str(self))
        return False
      # OpenFlow parsing occurs here:
      ofp_type = ord(self.buf[1])
      packet_length = ord(self.buf[2]) << 8 | ord(self.buf[3])
      if packet_length > l: break
      msg = classes[ofp_type]()
      #log.debug("RECEIVED " + msg.__class__.__name__)
      # msg.unpack implicitly only examines its own bytes, and not trailing
      # bytes 
      msg.unpack(self.buf)
      self.buf = self.buf[packet_length:]
      l = len(self.buf)
      #proxy.process_message(self, msg)
      self.raiseEventNoErrors(MessageIn, self, msg)
    return True

  def _incoming_stats_reply (self, ofp):
    # This assumes that you don't receive multiple stats replies
    # to different requests out of order/interspersed.
    more = (ofp.flags & 1) != 0
    if more:
      if ofp.type not in [of.OFPST_FLOW, of.OFPST_TABLE,
                                of.OFPST_PORT, of.OFPST_QUEUE]:
        log.error("Don't know how to aggregate stats message of type " +
                  str(ofp.type))
        self._previous_stats = []
        return
      
    if len(self._previous_stats) != 0:
      if ((ofp.xid == self._previous_stats[0].xid) and
          (ofp.type == self._previous_stats[0].type)):
        self._previous_stats.append(ofp)
      else:
        log.error("Was expecting continued stats of type %i with xid %i, " +
                  "but got type %i with xid %i" %
                  (self._previous_stats_reply.xid,
                    self._previous_stats_reply.type,
                    ofp.xid, ofp.type))
        self._previous_stats = [ofp]
    else:
      self._previous_stats = [ofp]

    if not more:
      #handler = statsHandlerMap.get(self._previous_stats[0].type, None)
      s = self._previous_stats
      self._previous_stats = []
      #if handler is None:
      #  log.warn("No handler for stats of type " +
        #         str(self._previous_stats[0].type))
      #  return
      #handler(self, s)

      #TODO: Special messages for stats
      self.raiseEventsNoErrors(StatsIn, self, s)

  def __str__ (self):
    return "[Con-base " + str(self.ID) + "]"

class SwitchConnection (BaseConnection):
  def __init__(self, sock = None, ID = None):
    BaseConnection.__init__(self, sock, ID)
    
  def __str__ (self):
    return "[Con-switch " + str(self.ID) + "]"
  
class ControllerConnection(BaseConnection):
  def __init__(self, port = 6634, address = "0.0.0.0", ID = None):
    sock = socket.create_connection((address, port))
    BaseConnection.__init__(self, sock, ID)
    
  def __str__ (self):
    return "[Con-controller " + str(self.ID) + "]"
