import random

from .competition_errors import FakeError


class FakeDebugger():

    def __init__(self, proxy, mult=0.1):
        self.proxy = proxy
        if isinstance(mult, basestring):
            mult = float(mult)
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

    def process_flow_mod(self, dpid, flow_mod, _):
        t = self.get_times()
        for _ in xrange(t):
            self.proxy.log_event(self, FakeError(dpid, flow_mod))

    def process_flow_removed(self, dpid, flow_rem):
        pass
