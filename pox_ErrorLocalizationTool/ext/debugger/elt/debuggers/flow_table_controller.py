import json
from modulefinder import ModuleFinder

import pox.openflow.libopenflow_01 as of

from .flow_table import TaggedFlowTable
from ..util import profile


class FlowTableController():

    def __init__(self, proxy, config=None):
        self.proxy = proxy
        self.flow_tables = {}
        self.last_local_id = 0
        self.config = config
        self.apps = {}
        self.apps_rev = {}
        self.read_config()
        self.frm = 0

    def read_config(self):
        """
        We have to split modules by apps.
        We use ModuleFinder to get all imports from module.
        Than we select those not starting with "/usr".
        """
        self.apps = {}
        self.apps_rev = {}
        if (self.config is None or
                not isinstance(self.config, basestring)):
            return
        # map: app -> modules
        f = open(self.config, 'r')
        finder = ModuleFinder()
        apps = None
        try:
            apps = json.load(f)
        except Exception as e:
            print e
        f.close()
        i = 0
        if not isinstance(apps, list):
            return
        for t in apps:
            if not isinstance(t, list):
                continue
            self.apps[i] = set()
            for module in t:
                if not isinstance(module, basestring):
                    continue
                self.apps[i].add(module)
                try:
                    finder.run_script(module)
                    modules = [m.__file__.replace('.pyo', '.py')
                               for m in finder.modules.values()
                               if hasattr(m, "__file__") and
                                  isinstance(m.__file__, basestring) and
                                  not m.__file__.startswith('/usr')]
                    self.apps[i].update(modules)
                except Exception as e:
                    print e
            i += 1

        # Reverse map: module -> apps
        for i, modules in self.apps.items():
            for module in modules:
                if module not in self.apps_rev:
                    self.apps_rev[module] = set()
                self.apps_rev[module].add(i)

    def get_apps(self, module):
        return self.apps_rev.get(module, set())

    def process_flow_mod(self, dpid, flow_mod, module):
        """
        Check for errors on FlowTable model.
        """
        flow_mod.flags |= of.OFPFF_SEND_FLOW_REM

        if dpid not in self.flow_tables:
            self.flow_tables[dpid] = TaggedFlowTable(dpid, nexus=self)

        self.flow_tables[dpid].process_flow_mod(
            flow_mod, self.get_apps(module))

    def process_flow_removed(self, dpid, flow_rem):
        #TODO: Something with VLAN's
        #TODO: OVS changes priority
        if dpid not in self.flow_tables:
            return
        self.frm += 1
        self.flow_tables[dpid].process_flow_removed(flow_rem)

    def handle_CompetitionError(self, event):
        self.proxy.log_event(self, event)
