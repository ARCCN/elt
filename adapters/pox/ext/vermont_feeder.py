from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.recoco import Timer
from datetime import datetime
from pox.openflow.discovery import Discovery
from pox.lib.util import dpid_to_str
from pox.lib.addresses import *
from pox.lib.packet import ethernet
import time
# import Looper as topo
import os
import sys
import subprocess
import urllib2
import json
import argparse
import io
import time
import math
import threading
import thread

sys.path.append("/home/lantame/SDN/ELT/netver/nest/")

import io_wrapper as io
import openflow_network as ofn
import openflow_table as oft
import openflow_fields as off
import convenience as con

import httplib

class TopologyManager(object):
    server = ""
    switches = []
    links = []

    def add_switch(self, dpid):
    	self.switches.append(dpid)

    def add_link(self, src_dpid, dst_dpid, src_port, dst_port):
    	self.links.append([src_dpid, dst_dpid, src_port, dst_port])

    def remove_switch(self, dpid):
        try:
    	    self.switches.remove(dpid)
        except:
            pass

    def remove_link(self, src_dpid, dst_dpid, src_port, dst_port):
    	self.links.remove([src_dpid, dst_dpid, src_port, dst_port])

    def createOFNetwork(self):
    	lock.acquire()
        network = ofn.Network()
        for sw in self.switches:
            raw_dpid = sw
            switch = ofn.Switch(ID=raw_dpid, dpid=raw_dpid)
            network.add_node(switch)
        for link in self.links:
            network.add_link(link[0], link[2], link[1], link[3], True)

        PATTERN_FIELDS = (
        ('port', off.OF_in_port),

        ('eth_src', off.OF_eth),
        ('eth_dst', off.OF_eth),
        ('eth_type', off.OF_eth_type),

        ('vlan', off.OF_vlan),

        ('ip_src', off.OF_ip),
        ('ip_dst', off.OF_ip),

        ('ip_proto', off.OF_ip_proto),

        ('tp_src', off.OF_tp_port),
        ('tp_dst', off.OF_tp_port)
        )

        oft.Pattern.set_structure(PATTERN_FIELDS)
    	lock.release()
        return network

    def make_msg(self, network):
        return io.serialize(network)

def _send(conn, msg):
    # print(len(msg))
    # prelude message body with its length
    msg_buffer = struct.pack("!H", len(msg)) + msg
    bytes_to_send = len(msg_buffer)
    # print(len(msg_buffer))
    while bytes_to_send > 0:
    	sent = conn.send(msg_buffer)
        if sent == 0:
            raise RuntimeError("socket connection broken")
	msg_buffer = msg_buffer[sent:]
        bytes_to_send -= sent

def vermont_listener(ip_addr, port):
	sock = socket.socket()
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind((ip_addr, port))

	while True:
	    sock.listen(1)
	    conn, addr = sock.accept()
	    print 'connected:', addr
	    while True:
	        data = conn.recv(2048)
	        if not data:
	            break
           	net = topo.createOFNetwork()
	        _send(conn, topo.make_msg(net))
	        print "done"
	    conn.close()
	    print 'disconnected:', addr

log = core.getLogger()
topo = TopologyManager()
lock = threading.Lock()

class vermont_feeder (EventMixin):

	def __init__(self):

		def startup():
			core.openflow.addListeners(self, priority=0)
			core.openflow_discovery.addListeners(self)

		core.call_when_ready(startup, ('openflow','openflow_discovery'))
		thread.start_new_thread( vermont_listener, ("127.0.0.1", 3636))
		print "READY"

	def _handle_ConnectionUp(self, event):
		topo.add_switch(event.connection.dpid)


	def _handle_ConnectionDown(self, event):
		topo.remove_switch(event.connection.dpid)

	def _handle_LinkEvent(self, event):
		if event.added:
			topo.add_link(event.link.dpid1, event.link.dpid2, event.link.port1, event.link.port2)
		elif not event.added:
			topo.remove_link(event.link.dpid1, event.link.dpid2, event.link.port1, event.link.port2)


def launch():
	core.registerNew(vermont_feeder)

