import json
from modulefinder import ModuleFinder

import pox.openflow.libopenflow_01 as of

from .dist_flow_table import DistFlowTable
from ..util import app_logging


log = app_logging.getLogger("DistFlowTableController")


class DistFlowTableController(object):

    def __init__(self, proxy, config=None):
        self.proxy = proxy
        self.flow_table = DistFlowTable()
        self.last_local_id = 0
        self.config = config
        self.apps = {}
        self.apps_rev = {}
        self.read_config()
        from pprint import pprint
        pprint(self.apps)

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

        finder = ModuleFinder()
        # map: app -> modules
        apps = None
        with open(self.config, 'r') as f:
            apps = json.load(f)
        if apps is None:
            log.debug("Apps are empty. Try setting modules in config: %s" % (
                self.config))
        f.close()
        i = 0
        if not isinstance(apps, list):
            return
        for t in apps:
            if not isinstance(t, list):
                continue
            self.apps[str(i)] = set()
            for module in t:
                if not isinstance(module, basestring):
                    continue
                self.apps[str(i)].add(module)
                try:
                    finder.run_script(module)
                    modules = [m.__file__.replace('.pyo', '.py')
                               for m in finder.modules.values()
                               if (hasattr(m, "__file__") and
                                   isinstance(m.__file__, basestring) and
                                   not m.__file__.startswith('/usr'))]
                    self.apps[str(i)].update(modules)
                except Exception as e:
                    log.debug(str(e))
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
        # TODO: Deal with exact matches in OF 1.0.
        print "Process FM", module
        flow_mod.flags |= of.OFPFF_SEND_FLOW_REM
        return self.flow_table.process_flow_mod(
            dpid, flow_mod, self.get_apps(module))

    def process_flow_removed(self, dpid, flow_rem):
        return self.flow_table.process_flow_removed(dpid, flow_rem)

    def close(self):
        self.flow_table.close()