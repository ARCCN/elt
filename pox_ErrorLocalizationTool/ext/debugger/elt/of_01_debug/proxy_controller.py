from pox.lib.revent import EventMixin

from ..database import DatabaseClient
from ..debuggers import FlowTableController, FakeDebugger
from ..logger import LogClient
from ..util import profile


class ProxyController:

    """
    Main class for debugging CompetitionErrors and error localization.
    Re-raises all FlowTable events.
    Responsible for storing flowmods in Database.
    """

    def __init__(self, **kw):
        self.db = DatabaseClient(mode='w')
        #self.log = LogClient(name="ProxyController")
        self.debuggers = {}
        if "flow_table_controller" in kw:
            self.debuggers[FlowTableController(
                self, kw["flow_table_controller"]
                )] = LogClient(name="Proxy.FlowTable")
            print "Flow Table Controller is up!", kw["flow_table_controller"]
        if "fake_debugger" in kw:
            self.debuggers[FakeDebugger(
                self, mult=kw["fake_debugger"]
                )] = LogClient(name="Proxy.FakeDeb")
            print "Fake Debugger is up!", kw["fake_debugger"]
        self.flowmods = 0

    def close(self):
        f = open('ProxyController.stats', 'w')
        f.write("FlowMods: %d\n" % self.flowmods)
        f.close()

    def add_flow_mod(self, dpid, flow_mod, code_entries):
        """
        Save FlowMod to database.
        Also check for errors on FlowTable model.
        If any, send them to LogServer.
        """

        self.flowmods += 1
        flow_mod.unpack(flow_mod.pack())
        try:
            self.db.add_flow_mod(dpid, flow_mod, code_entries)
        except EOFError:
            self.db.reconnect()

        for d in self.debuggers.keys():
            d.process_flow_mod(dpid, flow_mod, code_entries[0][0])

    def process_flow_removed(self, dpid, flow_rem):
        for d in self.debuggers:
            d.process_flow_removed(dpid, flow_rem)

    def log_event(self, debugger, event):
        self.debuggers[debugger].log_event(event)
