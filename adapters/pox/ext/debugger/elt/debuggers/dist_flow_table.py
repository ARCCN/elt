from subprocess import Popen
import socket, sys
import json
from pprint import pprint

from .flowmod_message import *
from ..interaction import ofp_flow_mod, Instantiator, ConnectionFactory


class DistFlowTable(object):
    def __init__(self):
        self.skt = list(socket.socketpair(socket.AF_UNIX))
        self.popen = Popen(["java", "-jar", "/home/lantame/SDN/ELT/hazelcast_adapter/hazelcast_adapter.jar"],
                           stdin=self.skt[1], stdout=self.skt[1], stderr=open("dist.log", "w"))
        self.factory = ConnectionFactory(instantiator=Instantiator(
            module=(__name__.rsplit('.', 1)[0] + ".flowmod_message")))
        self.skt[0] = self.factory.create_connection(self.skt[0])

    def process_flow_mod(self, dpid, flow_mod, apps):
        print '--------\n', apps, '\n-------\n'
        msg = FlowModMessage(ofp_flow_mod.from_flow_mod(flow_mod),
                             dpid, TableEntryTag(apps))
        print "NEW MESSAGE"
        print self.skt[0].dumps(msg)
        self.skt[0].send(msg)
        result = None
        while not result:
            result = self.skt[0].recv()
        # TODO: Normal processing.
        # TODO: Do we need apps in error messages?
        # TODO: Multiple error messages.
        # Guess CompetitionErrorMessage is a bad option.
        print "RESULT"
        if not isinstance(result, basestring):
            pprint(json.loads(self.skt[0].dumps(result)))
        return result.errors

    def process_flow_removed(self, dpid, flow_rem):
        pass

    def close(self):
        print "Closing sockets."
        try:
            self.skt[0].shutdown(socket.SHUT_RDWR)
            self.skt[1].shutdown(socket.SHUT_RDWR)
        except:
            import traceback
            traceback.print_exc()

