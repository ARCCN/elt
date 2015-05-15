from ..database import DatabaseClient
from ..debuggers import FlowTableController, FakeDebugger, DistFlowTableController
from ..logger import LogClient
from ..util import app_logging, set_cid_prefix


log = app_logging.getLogger('ProxyController')


class ProxyController(object):

    """
    Main class for debugging CompetitionErrors and error localization.
    Re-raises all FlowTable events.
    Responsible for storing flowmods in Database.
    """

    def __init__(self, **kw):
        self.flowmods = 0
        self.db = DatabaseClient(mode='w')
        if "cid" in kw:
            self.cid = int(kw["cid"])
            set_cid_prefix("_%d_" % self.cid)
        else:
            self.cid = 0
        log.info("We are controller #%d" % self.cid)
        self.debuggers = {}
        if "dist_flow_table_controller" in kw:
            self.debuggers[DistFlowTableController(
                self, kw["dist_flow_table_controller"]
                )] = LogClient(name="Proxy.DistFT")
            log.info("Dist Flow Table Controller is up! %s" % (
                kw["dist_flow_table_controller"]))
        if "flow_table_controller" in kw:
            self.debuggers[FlowTableController(
                self, kw["flow_table_controller"]
                )] = LogClient(name="Proxy.FlowTable")
            log.info("Flow Table Controller is up! %s" % (
                kw["flow_table_controller"]))
        if "fake_debugger" in kw:
            self.debuggers[FakeDebugger(
                self, mult=kw["fake_debugger"]
                )] = LogClient(name="Proxy.FakeDeb")
            log.info("Fake Debugger is up! %s" % kw["fake_debugger"])
        # Dump events.
        # self.dump_files = {}
        # for l in self.debuggers.values():
        #     self.dump_files[l.name] = open(l.name + ".dmp", "w")

    def get_cid(self):
        return self.cid

    def close(self):
        f = open('ProxyController.stats', 'w')
        f.write("FlowMods: %d\n" % self.flowmods)
        f.close()
        for debugger, logger in self.debuggers.items():
            try:
                debugger.close()
            except:
                pass
            # self.dump_files[logger.name].close()

    def add_flow_mod(self, dpid, flow_mod, code_entries):
        """
        Save FlowMod to database.
        Also check for errors on FlowTable model.
        If any, send them to LogServer.
        """
        # print "FlowMod for", self.cid
        self.flowmods += 1
        flow_mod.unpack(flow_mod.pack())
        try:
            self.db.add_flow_mod(dpid, flow_mod, code_entries, self.cid)
        except EOFError:
            self.db.reconnect()

        for d in self.debuggers.keys():
            events = d.process_flow_mod(dpid, flow_mod, code_entries[0][0])
            if isinstance(events, list):
                for e in events:
                    self.log_event(d, e)
                    # self.dump_files[self.debuggers[d].name].write(
                    #         self.db.connection.dumps(e)+"\n")

    def process_flow_removed(self, dpid, flow_rem):
        for d in self.debuggers:
            events = d.process_flow_removed(dpid, flow_rem)
            if isinstance(events, list):
                for e in events:
                    self.log_event(d, e)
                    # self.dump_files[self.debuggers[d].name].write(
                    #         self.db.connection.dumps(e)+"\n")

    def log_event(self, debugger, event):
        self.debuggers[debugger].log_event(event)
