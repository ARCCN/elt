import socket
import select
import threading
import os
import sys
import exceptions
from errno import EAGAIN, ECONNRESET

from pox.lib.recoco.recoco import Task, Select
import pox.openflow.libopenflow_01 as of
from database import Database
import pox.lib.packet as pkt
from pox.core import core
from pox.lib.revent import EventMixin
from openflow_events import *
from connections import MessageIn, BaseConnection, \
    SwitchConnection, ControllerConnection
from naive_logger import log
from discovery import *

listener = None

class ConnectionPair():
  def __init__(self, s, c, dpid = None):
    self.switch = s
    self.controller = c
    self.dpid = dpid

  def send(self, data):
    return self.switch.send(data)

db = None
proxy = None
discovery = None

class Proxy(EventMixin):

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

    PacketOut, 
    Hello, 
    FlowMod,
    PortMod,
    FeaturesRequest,
    FeaturesReply,
    EchoRequest,
    EchoReply,
    BarrierRequest,
    StatsRequest,
    SwitchConfig
  ])

  def __init__(self, target_port = 6634, target_address = "0.0.0.0"):
    self.target_port = target_port
    self.target_address = target_address
    self.connections = {}
    self.max_index = 0
    self.matches = {}
    self.waiting_packets_checked = time.gmtime()
    self.waiting_packets = {}
    core.register('proxy', self)
    self.listenTo(core.proxy)

  def create_pair(self, new_sock):
    self.max_index += 1
    newcon = SwitchConnection(new_sock, self.max_index)
    log.debug("switch connection" + str(newcon))
    try:
      control = ControllerConnection(self.target_port, self.target_address, self.max_index)
      log.debug("controller connection" + str(control))
      self.listenTo(newcon)
      self.listenTo(control)
      pair = ConnectionPair(newcon, control)
      self.connections[self.max_index] = pair
      return pair
    except Exception as e:
      log.debug(str(e))
      return None
    
  def remove(self, connection):
    if isinstance(connection, BaseConnection):
      return self.connections.pop(connection.ID, None)

  def _handle_MessageIn(self, event):
    self.process_message(event.connection, event.ofp)

  def _handle_StatsIn(self, event):
    self.process_stats(event.connection, event.ofp)

  def process_message(self, connection, msg):
    """
    Send an event to listeners
    NOTE: We are dependent on not-copying message during processing
          We have single instance of ResendController for all listeners
          Also we will resend the result message after pipeline of listeners.
    """
    if isinstance(connection, BaseConnection):
      event = ofp_to_OFEvent(msg)
      if event is not None:
        #Collect full stats reply
        if event == RawStatsReply:
          connection._incoming_stats_reply(msg)      
        resend = ResendController()
        self.raiseEventNoErrors(event, self.connections[connection.ID], msg, resend)
        if resend.resend_needed():
          self.resend_message(connection, msg)
                
  def process_stats(self, connection, parts):
    if isinstance(connection, BaseConnection):
      stats = ofp_to_OFStats(parts)
      if stats is not None:
        self.raiseEventNoErrors(stats, self.connections[connection.ID], parts)

  def resend_message(self, connection, msg):
      message = msg.__class__.__name__
      result = self.connections[connection.ID]
      if result.switch is connection:
        result.controller.send(msg)
        log.info("%-20s \t %s \t->\t %s" % (message, connection, result.controller))
      elif result.controller is connection:
        result.switch.send(msg)
        log.info("%-20s \t %s \t->\t %s" % (message, connection, result.switch)) 

  def sendToDPID(self, dpid, packet, switch = True):
    for conID, pair in self.connections.iteritems():
      if pair.dpid == dpid:
        try:
          if switch == True:
            pair.switch.send(packet)
          else:
            pair.controller.send(packet)
        except:
          pass
        break

  def send_message(self, connection, msg):
    connection.send(msg)
    
  def _handle_ConnectionDown(self, event):
    self.raiseEventNoErrors(event)

  def _handle_FlowMod(self, event):
    #We are going to resend this PacketIn
    self.check_waiting_packets(event.dpid, event.ofp.buffer_id)
    #To prevent duplicated actions
    #TODO: smth with overlapping FlowMods and duplicated matches
    #Also multiple PacketIns for a single packet and header change
    #during processing
    if len([action for action in event.ofp.actions if \
      isinstance(action, of.ofp_action_output) and \
      action.port == of.OFPP_CONTROLLER]) == 0:
      log.info("Adding debug-force")
      event.ofp.actions.insert(0, of.ofp_action_output(\
              port = of.OFPP_CONTROLLER))
    else:
      dpid = event.dpid
      if event.ofp.match not in self.matches[dpid]:
        self.matches[dpid].append(event.ofp.match)
        log.info("matches for dpid %s : %s" % (dpid, len(self.matches[dpid])))
    event.ofp.flags |= of.OFPFF_SEND_FLOW_REM
    log.debug("FlowMod: %s" % (event.ofp))
    event.resend.resend()


  def store_and_wait(self, ofp, dpid, in_port, src_dpid, src_port, buffer_id):
    self.waiting_packets[(dpid, buffer_id)] = (time.time(), ofp, dpid, in_port, src_dpid, src_port)

  def check_waiting_packets(self, dpid = None, buffer_id = None):
    #This PacketIn is going to be resend.
    #Prevent from duplication
    if buffer_id != -1 and buffer_id is not None \
            and (dpid, buffer_id) in self.waiting_packets:
      #print "Deleted info about %s:%s" % (str(dpid), str(self.waiting_packets[dpid, buffer_id][3]))
      del self.waiting_packets[(dpid, buffer_id)]

    #Delete unused packets
    #And store PacketIn in Database
    cur_time = time.time()
    if cur_time > self.waiting_packets_checked:
      for key, val in self.waiting_packets.items():
        if cur_time - val[0] > 2:
          data = val
          db.add_history(packet=pkt.ethernet(data[1].data), \
                     dpid=data[2], in_port=data[3], \
                     src_dpid=data[4], src_port=data[5], t=time.gmtime(data[0]))
          log.debug("PacketIN on %s:%s : %s Data: %s" % \
                (data[2], data[3],\
                 data[1] , pkt.ethernet(data[1].data)))

          del self.waiting_packets[key]

    self.waiting_packets_checked = cur_time

  def _handle_PacketIn(self, event):
    try:
      src = core.proxy_discovery.get_other_end(event.dpid, event.ofp.in_port)
      if src is None:
        dpid, port = None, None
      else:
        dpid, port = src
    except Exception as e:
      log.error(str(e))
      
    new_match = of.ofp_match.from_packet(\
                pkt.ethernet(event.ofp.data), event.ofp.in_port)
    if event.ofp.reason == of.OFPR_NO_MATCH or \
        len([match for match in self.matches[event.dpid] \
        if match.matches_with_wildcards(new_match)]) > 0:
      if event.ofp.reason == of.OFPR_NO_MATCH: 
        log.debug("NO MATCH")
      #We will store info if there is no response
      self.store_and_wait(event.ofp, \
                     event.dpid, event.ofp.in_port,\
                     dpid, port, event.ofp.buffer_id) 
    else:
      db.add_history(packet=pkt.ethernet(event.ofp.data), \
                     dpid=event.dpid, in_port=event.ofp.in_port, \
                     src_dpid=dpid, src_port=port, t=time.gmtime())

      event.resend.no_resend()
      log.info("Didn't send to controller")

  def _handle_PacketOut(self, event):
    log.debug("PacketOut on %s : %s" % \
        (event.dpid, event.ofp))
    log.debug("Data: %s" % (pkt.ethernet(event.ofp.data)))
    for action in event.ofp.actions:
        if action.port == of.OFPP_CONTROLLER:
            self.check_waiting_packets(event.dpid, event.ofp.buffer_id)
            break
    event.resend.resend()

  def _handle_FeaturesReply(self, event):
    #Learning real DPIDs
    self.connections[event.connection.switch.ID].dpid = event.ofp.datapath_id
    self.matches[event.ofp.datapath_id] = []
    self.raiseEventNoErrors(ConnectionUp, event.connection, \
            event.ofp, event.resend)
    event.resend.resend()

  def _handle_FlowRemoved(self, event):
    dpid = event.dpid
    try:
      self.matches[dpid].remove(event.ofp.match)
    except:
      log.debug("No such matches")
    log.debug("FlowRemoved: %s" % (event.ofp))
    log.info("matches for dpid %s : %s" % (dpid, len(self.matches[dpid])))
    event.resend.resend()

class ProxyTask(Task):
  def __init__(self, port = 6633, address = '0.0.0.0', 
               target_port = 6634, target_address = "0.0.0.0"):
    global proxy, db, discovery
    
    db = Database()
    db.clear()
    proxy = Proxy(target_port, target_address)
    discovery = Discovery(install_flow=True, init_sender=True)
    Task.__init__(self)
    self.port = int(port)
    self.address = address
    self.target_port = int(target_port)
    self.target_address = target_address
    core.register(self, 'ProxyTask')
    self.start()

  def run(self):
    self.sockets = []
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind((self.address, self.port))
    listener.listen(10000)
    self.sockets.append(listener)
    print("Listening on %s:%s" % (self.address, self.port))
    
    con = None
    while (True):
      try:
        while True:
          con = None
          rlist, wlist, elist = yield Select(self.sockets, [], self.sockets, 5)
          #log.debug("read " + str(len(rlist)) + ", ex " + str(len(elist)))
          if len(rlist) == 0 and len(wlist) == 0 and len(elist) == 0:
            """
            try:
              timer_callback()
            except:
              print "[Timer]", sys.exc_info
            continue
            """
            #if not core.running: break
            pass
          
          for con in elist:
            if con is listener:
              raise RuntimeError("Error on listener socket")
            else:
              try:
                self.remove_connection(con)
              except Exception as e:
                log.error(str(e))
              
          for con in rlist:
            if con is listener:
              new_sock = listener.accept()[0]
              print("Connection accepted")
              
              #if pox.openflow.debug.pcap_traces:
                #new_sock = wrap_socket(new_sock)
              new_sock.setblocking(0)
              try:
                self.create_pair(new_sock)
              except Exception as e:
                log.error(str(e))
              
            else:
              #We will work as a timer!
              core.proxy.check_waiting_packets()
              if not con.read():
                try:
                  log.debug("Bad reading from " + str(con))
                  self.remove_connection(con)
                except Exception as e:
                  log.error(str(e))
                
      except exceptions.KeyboardInterrupt:
        break
      except Exception as e:
        log.error(str(e))
        doTraceback = True
        if sys.exc_info()[0] is socket.error:
          if sys.exc_info()[1][0] == ECONNRESET:
            con.info("Connection reset")
            doTraceback = False

        if doTraceback:
          log.debug("Exception reading connection " + str(con))

        if con is listener:
          log.error("Exception on OpenFlow listener.  Aborting.")
          break
        try:
          self.remove_connection(con)
        except Exception as e:
          log.error(str(e))
      
  def create_pair(self, socket):
    #log.debug("create_pair")
    result = proxy.create_pair(socket)
    if result is not None:
      self.sockets.append( result.switch )
      self.sockets.append( result.controller )
      log.debug(str(result.switch) + " connected with " + str(result.controller))
      log.debug("Sockets: " + str(len(self.sockets)))

  def remove_connection(self, con):
    result = proxy.remove(con)
    if result is not None:
      try:
        result.switch.close()
      except:
        pass
      try:
        result.controller.close()
      except:
        pass
      self.sockets.remove(result.switch)
      self.sockets.remove(result.controller)

