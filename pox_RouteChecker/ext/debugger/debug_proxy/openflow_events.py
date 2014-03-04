# Copyright 2011 James McCauley
#
# This file is part of POX.
#
# POX is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# POX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with POX.  If not, see <http://www.gnu.org/licenses/>.

"""
This is the main OpenFlow module.
 .connection - a reference to the switch connection that caused the event
    CHANGED: reference to ConnectionPair from debug_proxy
 .dpid - the DPID of the switch that caused the event
 .ofp - the OpenFlow message that caused the event (from libopenflow)

One of the more complicated aspects of OpenFlow is dealing with stats
replies, which may come in multiple parts (it shouldn't be that that
difficult, really, but that hasn't stopped it from beind handled wrong
wrong more than once).  In POX, the raw events are available, but you will
generally just want to listen to the aggregate stats events which take
care of this for you and are only fired when all data is available.
"""

from pox.lib.revent import *
import pox.openflow.libopenflow_01 as of
from pox.lib.packet.ethernet import ethernet

class ResendController:
  """
  Message has an instance of this class inside.
  It hepls to collect information about whether
  this message needs to be resent or not.
  """
  def __init__(self):
    self._resend = None
  
  def resend(self):
    if self._resend is None:
      self._resend = True
    else:
      self._resend |= True

  def no_resend(self):
    if self._resend is None:
      self._resend = False
    else:
      self._resend |= False

  def resend_needed(self):
    if self._resend is None:
      return True
    else:
      return self._resend
  
  def __str__(self):
    return "Resend: " + str(self._resend)


class OFEvent (Event):
  """
  Base class for our proxy openflow events.
  Connection is instance of ConnectionPair
  resend is instance of ResendController
  """
  def __init__(self, connection, ofp, resend = None):
    Event.__init__(self)
    self.connection = connection
    self.dpid = connection.dpid
    self.ofp = ofp
    self.resend = resend


  def __str__(self):
    return str(self.connection) +'\n' + str(self.dpid) + '\n' \
            + str(self.ofp) + '\n' + str(self.resend)
  
class ConnectionUp (OFEvent):
  """
  Connection raised when the connection to an OpenFlow switch has been
  established.
  """
  def __init__ (self, connection, ofp, resend = None):
    OFEvent.__init__(self, connection, ofp, resend)

class ConnectionDown (Event):
  """
  Connection raised when the connection to an OpenFlow switch has been
  lost.
  """
  def __init__ (self, connection):
    self.connection = connection

class PortStatus (OFEvent):
  """
  Fired in response to port status changes.
  added (bool) - True if fired because a port was added
  deleted (bool) - True if fired because a port was deleted
  modified (bool) - True if fired because a port was modified
  port (int) - number of port in question
  """
  def __init__ (self, connection, ofp, resend = None):
    OFEvent.__init__(self, connection, ofp, resend)
    self.modified = ofp.reason == of.OFPPR_MODIFY
    self.added = ofp.reason == of.OFPPR_ADD
    self.deleted = ofp.reason == of.OFPPR_DELETE
    self.port = ofp.desc.port_no

class FlowRemoved (OFEvent):
  """
  Raised when a flow entry has been removed from a flow table.
  This may either be because of a timeout or because it was removed
  explicitly.
  Properties:
  idleTimeout (bool) - True if expired because of idleness
  hardTimeout (bool) - True if expired because of hard timeout
  timeout (bool) - True if either of the above is true
  deleted (bool) - True if deleted explicitly
  """
  def __init__ (self, connection, ofp, resend = None):
    OFEvent.__init__(self, connection, ofp, resend)
    self.idleTimeout = False
    self.hardTimeout = False
    self.deleted = False
    self.timeout = False
    if ofp.reason == of.OFPRR_IDLE_TIMEOUT:
      self.timeout = True
      self.idleTimeout = True
    elif ofp.reason == of.OFPRR_HARD_TIMEOUT:
      self.timeout = True
      self.hardTimeout = True
    elif ofp.reason == of.OFPRR_DELETE:
      self.deleted = True

class RawStatsReply (OFEvent):
  def __init__ (self, connection, ofp, resend = None):
    OFEvent.__init__(self, connection, ofp, resend)
    # Raw ofp message(s)

def _processStatsBody(body, obj):
  r = []
  t = obj.__class__
  remaining = len(body)
  while remaining:
    obj = t()
    body = obj.unpack(body)
    assert len(body) < remaining
    remaining = len(body)
    r.append(obj)
  return r


class StatsReply (OFEvent):
  """ Abstract superclass for all stats replies """
  def __init__ (self, connection, parts):
    OFEvent.__init__(self, connection, parts, None)
    #Processed
    self.stats = None

class SwitchDescReceived (StatsReply):
  def __init__(self, connection, parts):
    StatsReply.__init__(self, connection, parts)
    self.stats = of.ofp_desc_stats()
    self.stats.unpack(parts[0].body)

class FlowStatsReceived (StatsReply):
  def __init__(self, connection, parts):
    StatsReply.__init__(self, connection, parts)
    self.stats = []
    for part in parts:
      self.stats += _processStatsBody(part.body, of.ofp_flow_stats())

class AggregateFlowStatsReceived (StatsReply):
  def __init__(self, connection, parts):
    StatsReply.__init__(self, connection, parts)
    self.stats = of.ofp_aggregate_stats_reply()
    self.stats.unpack(parts[0].body)

class TableStatsReceived (StatsReply):
  def __init__(self, connection, parts):
    StatsReply.__init__(self, connection, parts)
    self.stats = []
    for part in parts:
      self.stats += _processStatsBody(part.body, of.ofp_table_stats())

class PortStatsReceived (StatsReply):
  def __init__(self, connection, parts):
    StatsReply.__init__(self, connection, parts)
    self.stats = []
    for part in parts:
      self.stats += _processStatsBody(part.body, of.ofp_port_stats())

class QueueStatsReceived (StatsReply):
  def __init__(self, connection, parts):
    StatsReply.__init__(self, connection, parts)
    self.stats = []
    for part in parts:
      self.stats += _processStatsBody(part.body, of.ofp_queue_stats())

class PacketIn (OFEvent):
  """
  Fired in response to PacketIn events
  port (int) - number of port the packet came in on
  data (bytes) - raw packet data
  parsed (packet subclasses) - pox.lib.packet's parsed version
  """
  def __init__ (self, connection, ofp, resend = None):
    OFEvent.__init__(self, connection, ofp, resend)
    self.port = ofp.in_port
    self.data = ofp.data
    self._parsed = None

  def parse (self):
    if self._parsed is None:
      self._parsed = ethernet(self.data)
    return self._parsed

  @property
  def parsed (self):
    """
    The packet as parsed by pox.lib.packet
    """
    return self.parse()

class ErrorIn (OFEvent):
  def __init__ (self, connection, ofp, resend = None):
    OFEvent.__init__(self, connection, ofp, resend)
    self.xid = ofp.xid

  def asString (self):
    return self.ofp.show()

class BarrierIn (OFEvent):
  """
  Fired in response to a barrier reply
  xid (int) - XID of barrier request
  """
  def __init__ (self, connection, ofp, resend = None):
    OFEvent.__init__(self, connection, ofp, resend)
    self.xid = ofp.xid

class PacketOut (OFEvent):
  
  def __init__ (self, connection, ofp, resend = None):
    OFEvent.__init__(self, connection, ofp, resend)
    self.data = ofp.data
    self._parsed = None
  
  def parse (self):
    if self._parsed is None:
      self._parsed = ethernet(self.data)
    return self._parsed

  @property
  def parsed (self):
    """
    The packet as parsed by pox.lib.packet
    """
    return self.parse()



class FlowMod (OFEvent):
  def __init__ (self, connection, ofp, resend = None):
    OFEvent.__init__(self, connection, ofp, resend)

class PortMod (OFEvent):
  def __init__ (self, connection, ofp, resend = None):
    OFEvent.__init__(self, connection, ofp, resend)

class StatsRequest (OFEvent):
  def __init__ (self, connection, ofp, resend = None):
    OFEvent.__init__(self, connection, ofp, resend)

class FeaturesRequest (OFEvent):
  def __init__ (self, connection, ofp, resend = None):
    OFEvent.__init__(self, connection, ofp, resend)

class FeaturesReply (OFEvent):
  def __init__ (self, connection, ofp, resend = None):
    OFEvent.__init__(self, connection, ofp, resend)

class Hello (OFEvent):
  def __init__ (self, connection, ofp, resend = None):
    OFEvent.__init__(self, connection, ofp, resend)

class EchoRequest (OFEvent):
  def __init__ (self, connection, ofp, resend = None):
    OFEvent.__init__(self, connection, ofp, resend)

class EchoReply (OFEvent):
  def __init__ (self, connection, ofp, resend = None):
    OFEvent.__init__(self, connection, ofp, resend)

class BarrierRequest (OFEvent):
  def __init__ (self, connection, ofp, resend = None):
    OFEvent.__init__(self, connection, ofp, resend)

class SwitchConfig (OFEvent):
  def __init__ (self, connection, ofp, resend = None):
    OFEvent.__init__(self, connection, ofp, resend)
    
def ofp_to_OFEvent(msg):
  if isinstance(msg, of.ofp_hello):
    return Hello
  elif isinstance(msg, of.ofp_port_status):
    return PortStatus
  elif isinstance(msg, of.ofp_flow_mod):
    return FlowMod
  elif isinstance(msg, of.ofp_port_mod):
    return PortMod
  elif isinstance(msg, of.ofp_packet_in):
    return PacketIn
  elif isinstance(msg, of.ofp_flow_removed):
    return FlowRemoved
  elif isinstance(msg, of.ofp_features_request):
    return FeaturesRequest
  elif isinstance(msg, of.ofp_features_reply):
    return FeaturesReply
  elif isinstance(msg, of.ofp_error):
    return ErrorIn
  elif isinstance(msg, of.ofp_packet_out):
    return PacketOut
  elif isinstance(msg, of.ofp_echo_request):
    return EchoRequest
  elif isinstance(msg, of.ofp_echo_reply):
    return EchoReply
  elif isinstance(msg, of.ofp_barrier_request):
    return BarrierRequest
  elif isinstance(msg, of.ofp_barrier_reply):
    return BarrierIn
  elif isinstance(msg, of.ofp_stats_request):
    return StatsRequest
  elif isinstance(msg, of.ofp_stats_reply):
    return RawStatsReply
  elif isinstance(msg, of.ofp_switch_config):
    return SwitchConfig
  else:
    return None

def ofp_to_OFStats(parts):
  if parts[0].type == of.OFPST_DESC:
    return SwitchDescReceived    
  elif parts[0].type == of.OFPST_FLOW:
    return FlowStatsReceived
  elif parts[0].type == of.OFPST_AGGREGATE:
    return AggregateFlowStatsReceived
  elif parts[0].type == of.OFPST_TABLE:
    return TableStatsReceived
  elif parts[0].type == of.OFPST_PORT:
    return PortStatsReceived
  elif parts[0].type == of.OFPST_QUEUE:
    return QueueStatsReceived
  else:
    return None
