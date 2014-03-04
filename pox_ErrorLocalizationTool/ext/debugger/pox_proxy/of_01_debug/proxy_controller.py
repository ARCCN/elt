from pox.lib.revent import EventMixin

from ..database import DatabaseClient
from ..competition_errors import *
from ..debuggers import FlowTableController, FakeDebugger
from ..logger import LogClient
from ..util import profile


class ProxyController(EventMixin):

    """
    Main class for debugging CompetitionErrors and error localization.
    Re-raises all FlowTable events.
    Responsible for storing flowmods in Database.
    """

    _eventMixin_events = set([
        FlowMasked,
        FlowDeleted,
        FlowModified,
        FlowUndefined
    ])

    def __init__(self, **kw):
        EventMixin.__init__(self)
        self.db = DatabaseClient(mode='w')
        self.log = LogClient(name="ProxyController")
        self.debuggers = {}
        self.debuggers[FlowTableController(self)] = LogClient(name="Proxy.FlowTable")
        mult = float(kw.get("mult", 0.1))
        self.debuggers[FakeDebugger(self, mult=mult)] = LogClient(name="Proxy.FakeDeb")
        #core.register("flow_mod_proxy", self)
        self.flowmods = 0
       # self.f = open('ProxyController.stats', 'w')

    def close(self):
        #self.f.close()
        pass

    def add_flow_mod(self, dpid, flow_mod, code_entries):
        """
        Save FlowMod to database.
        Also check for errors on FlowTable model.
        If any, send them to LogServer.
        """

        self.flowmods += 1
        #self.f.write('FlowMods: %d\n' % self.flowmods)
        #self.f.flush()
        flow_mod.unpack(flow_mod.pack())
        try:
            self.db.add_flow_mod(dpid, flow_mod, code_entries)
        except EOFError:
            self.db.reconnect()

        for d in self.debuggers.keys():
            d.process_flow_mod(dpid, flow_mod)

    def process_flow_removed(self, dpid, flow_rem):
        for d in self.debuggers:
            d.process_flow_removed(dpid, flow_rem)

    def log_event(self, debugger, event):
        self.debuggers[debugger].log_event(event)
