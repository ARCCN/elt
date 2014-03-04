import random

from pox.lib.revent import EventMixin

from .competition_errors import *
from .flow_table import TaggedFlowTable


class FlowTableController():

    def __init__(self, proxy):
        self.proxy = proxy
        self.flow_tables = {}
        self.last_local_id = 0

    def process_flow_mod(self, dpid, flow_mod):
        """
        Check for errors on FlowTable model.
        """
        self.last_local_id += 1
        local_id = self.last_local_id

        if dpid not in self.flow_tables:
            self.flow_tables[dpid] = TaggedFlowTable(dpid, nexus=self)
            #self.listenTo(self.flow_tables[dpid])

        if local_id % 1000 == 0:
            print len(self.flow_tables[dpid]._table)

        #    print ("%lf %lf" % (timeit.timeit(functools.partial(
        #        self.flow_tables[dpid].process_flow_mod,
        #        flow_mod, local_id, None), number=1),
        #        len(self.flow_tables[dpid]._table)))
        #else:
        self.flow_tables[dpid].process_flow_mod(flow_mod, local_id, None)

    def process_flow_removed(self, dpid, flow_rem):
        #TODO: Something with VLAN's
        #TODO: OVS changes priority
        if dpid not in self.flow_tables:
            return
        self.flow_tables[dpid].process_flow_removed(flow_rem)

    def handle_CompetitionError(self, event):
        self.proxy.log_event(self, event)


class FakeDebugger():

    def __init__(self, proxy, mult=0.1):
        self.proxy = proxy
        self.mult = mult

    def get_times(self):
        if self.mult > 1.0:
            return int(self.mult)
        if self.mult < 0.0:
            return 0
        r = random.random()
        if r < self.mult:
            return 1
        return 0

    def process_flow_mod(self, dpid, flow_mod):
        #if flow_mod.command != 0:
        #    return
        t = self.get_times()
        for i in xrange(t):
            self.proxy.log_event(self, FakeError(dpid, flow_mod))

    def process_flow_removed(self, dpid, flow_rem):
        pass
