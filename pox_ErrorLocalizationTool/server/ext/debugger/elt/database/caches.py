from collections import OrderedDict

from .database_utility import get_action_params
from ..util import ip_to_uint, eth_to_int


class LimitedSizeDict(OrderedDict):

    """ Our cache will be of finite size. """

    def __init__(self, *args, **kwds):
        self.size_limit = kwds.pop("size_limit", None)
        OrderedDict.__init__(self, *args, **kwds)
        self._check_size_limit()

    def __setitem__(self, key, value):
        OrderedDict.__setitem__(self, key, value)
        self._check_size_limit()

    def _check_size_limit(self):
        if self.size_limit is not None:
            while len(self) > self.size_limit:
                self.popitem(last=False)


class TableCache(object):

    """
    Base class for caching a table.
    Accepts find(key) and add(key, value).
    All the keys are converted using convert_key(key).
    """

    def __init__(self, size=1000):
        self.size = size
        self.dict = LimitedSizeDict(size_limit=size)
        self.hit = 0
        self.miss = 0

    def find(self, key):
        x = self.dict.get(self.convert_key(key))
        if x is None:
            self.miss += 1
        else:
            self.hit += 1
        return x

    def add(self, key, value):
        self.dict[self.convert_key(key)] = value

    def convert_key(self, key):
        """
        We only need to reimplement this function
        to produce a right key from parameter.
        It is applied to all the input keys.
        """
        return key


class ActionsCache(TableCache):

    def convert_key(self, action):
        return get_action_params(action)


class CodeEntriesCache(TableCache):
    pass


class CodePatternsToCodeEntriesCache(TableCache):

    def convert_key(self, codeentry_IDs):
        return tuple(codeentry_IDs)


class ActionPatternsToActionsCache(TableCache):

    def convert_key(self, action_IDs):
        return tuple(action_IDs)


class FlowModParamsCache(TableCache):

    def convert_key(self, flow_mod):
        return (flow_mod.command, flow_mod.idle_timeout, flow_mod.hard_timeout,
                flow_mod.priority, None, flow_mod.out_port, flow_mod.flags)


class FlowMatchCache(TableCache):

    def __init__(self):
        TableCache.__init__(self, 5000)

    def convert_key(self, match):
        return (match.wildcards, match.in_port, eth_to_int(match.dl_src),
                eth_to_int(match.dl_dst), match.dl_vlan, match.dl_vlan_pcp,
                match.dl_type, match.nw_tos, match.nw_proto,
                ip_to_uint(match.nw_src), ip_to_uint(match.nw_dst),
                match.tp_src, match.tp_dst)
