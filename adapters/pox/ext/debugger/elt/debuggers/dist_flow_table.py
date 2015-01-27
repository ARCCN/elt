from subprocess import Popen
import socket

from .flowmod_message import *
from ..interaction import ofp_flow_mod, Instantiator, ConnectionFactory


class DistFlowTable(object):
    def __init__(self):
        self.skt = socket.socketpair(socket.AF_UNIX)
        self.popen = Popen(["java", "-jar", "org.elt.hazelcast_adapter"],
                           stdin=skt[0], stdout=skt[1])
        self.factory = ConnectionFactory(instantiator=Instantiator(
            module=(__name__.rsplit('.', 1)[1] + ".flowmod_message")))
        for i in range(2):
            self.skt[i] = self.factory.create_connection(self.skt[i])


    def process_flow_mod(self, flow_mod, dpid, apps):
        msg = FlowModMessage(ofp_flow_mod.from_flow_mod(flow_mod),
                             dpid, TableEntryTag(apps))
        self.skt[0].send(msg)
        result = self.skt[1].recv()
        # TODO: Normal processing.
        # TODO: Do we need apps in error messages?
        # TODO: Multiple error messages.
        # Guess CompetitionErrorMessage is a bad option.
        print self.skt[0].dumps(result)



