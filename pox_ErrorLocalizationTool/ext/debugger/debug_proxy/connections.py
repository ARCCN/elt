import socket
import os
import sys
import exceptions
from errno import EAGAIN, ECONNRESET

from pox.openflow.of_01 import deferredSender, Connection, unpackers
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

class BaseConnection (Connection):
  """
  A Connection object represents a single TCP session with an
  openflow-enabled switch.
  If the switch reconnects, a new connection object is instantiated.
  """
  _eventMixin_events = set([
    MessageIn,
    StatsIn
  ])

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

  def close (self):
    if not self.disconnected:
      self.info("closing connection")
    else:
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

  def read (self):
    """
    Read data from this connection.  Generally this is just called by the
    main OpenFlow loop below.

    Note: This function will block if data is not available.
    """
    d = self.sock.recv(2048)
    if len(d) == 0:
      return False
    self.buf += d
    buf_len = len(self.buf)


    offset = 0
    while buf_len - offset >= 8: # 8 bytes is minimum OF message size
      # We pull the first four bytes of the OpenFlow header off by hand
      # (using ord) to find the version/length/type so that we can
      # correctly call libopenflow to unpack it.

      ofp_type = ord(self.buf[offset+1])

      if ord(self.buf[offset]) != of.OFP_VERSION:
        if ofp_type == of.OFPT_HELLO:
          # We let this through and hope the other side switches down.
          pass
        else:
          log.warning("Bad OpenFlow version (0x%02x) on connection %s"
                      % (ord(self.buf[offset]), self))
          return False # Throw connection away

      msg_length = ord(self.buf[offset+2]) << 8 | ord(self.buf[offset+3])

      if buf_len - offset < msg_length: break

      new_offset,msg = unpackers[ofp_type](self.buf, offset)
      assert new_offset - offset == msg_length
      offset = new_offset

    if offset != 0:
      self.buf = self.buf[offset:]
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

    if ofp.is_last_reply:
      s = self._previous_stats
      self._previous_stats = []

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
