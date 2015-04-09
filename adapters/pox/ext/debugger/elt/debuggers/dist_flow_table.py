from subprocess import Popen
import socket, sys
import json
from pprint import pprint

import pox.openflow.libopenflow_01 as of

from .flowmod_message import *
from ..interaction import ofp_flow_mod, Instantiator, ConnectionFactory
from ..util import profile


JAR_PATH = "/home/lantame/SDN/ELT/hazelcast_flow_table/hazelcast_flow_table.jar"


class DistFlowTable(object):
    def __init__(self, cid=0):
        self.log = open("dist_" + str(cid) + ".log", "w")
        self.skt = list(socket.socketpair(socket.AF_UNIX))
        self.popen = Popen(["java", "-jar", JAR_PATH],
                           stdin=self.skt[1], stdout=self.skt[1], stderr=self.log)
        self.factory = ConnectionFactory(instantiator=Instantiator(
            module=(__name__.rsplit('.', 1)[0] + ".flowmod_message")))
        self.skt[0] = self.factory.create_connection(self.skt[0])
        self.ignore = False
        # self.msg_log = open("messages_log.in", "w")

    #@profile
    def process_flow_mod(self, dpid, flow_mod, apps, cid=None):
        if self.ignore:
            return []
        # print '--------\n', apps, '\n-------\n'
        if cid is not None:
            cid = [cid]
        msg = FlowModMessage(ofp_flow_mod.from_flow_mod(flow_mod),
                             dpid, TableEntryTag(apps, cid))
        # print "NEW MESSAGE"
        # m = self.skt[0].dumps(msg)
        # self.msg_log.write(m)
        self.skt[0].send(msg)
        result = None
        while not result:
            try:
                result = self.skt[0].recv()
            except:
                import traceback
                traceback.print_exc()
                return []
        # TODO: Normal processing.
        # TODO: Do we need apps in error messages?
        # TODO: Multiple error messages.
        # Guess CompetitionErrorMessage is a bad option.
        # print "RESULT"
        # if not isinstance(result, basestring):
        #     pprint(json.loads(self.skt[0].dumps(result)))
        return result.errors

    def process_flow_removed(self, dpid, flow_rem):
        if self.ignore:
            return []
        errors = self.process_flow_mod(dpid, ofp_flow_mod(
            match=flow_rem.match,
            actions=[],
            command=of.OFPFC_DELETE_STRICT,
            priority=flow_rem.priority), [])
        # print "Flow removed:", len(errors), "errors"
        return []

    def close(self):
        self.ignore = True
        print "Closing sockets."
        try:
            self.skt[0].shutdown(socket.SHUT_RDWR)
            self.skt[1].shutdown(socket.SHUT_RDWR)
        except:
            import traceback
            traceback.print_exc()
        self.log.close()
        # self.msg_log.close()

