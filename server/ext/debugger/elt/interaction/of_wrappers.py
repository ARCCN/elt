import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr, EthAddr


def instantiate_fm_or_rule(d):
    """
    Instantiate FM or Rule chosen by d[name].
    Then fill it with d.
    """
    if "name" not in d:
        return None
    if d["name"] == "ofp_flow_mod":
        fm = ofp_flow_mod()
        fm.__setstate__(d)
        return fm
    elif d["name"] == "rule":
        r = ofp_rule()
        r.__setstate__(d)
        return r
    else:
        return None


class ofp_flow_mod(of.ofp_flow_mod):
    """
    Wrapper to provide serialization.
    We strip off data.
    """
    def __init__(self, match=None, actions=None, command=None, priority=None):
        if match is not None and not isinstance(match, ofp_match):
            match = ofp_match(match)
        of.ofp_flow_mod.__init__(self, match=match, actions=actions,
                                 command=command, priority=priority)
        self.name = 'ofp_flow_mod'

    @staticmethod
    def from_flow_mod(fm):
        if isinstance(fm, ofp_flow_mod):
            return fm
        if not isinstance(fm, of.ofp_flow_mod):
            return
        flow_mod = ofp_flow_mod(match=fm.match, actions=fm.actions,
                                command=fm.command, priority=fm.priority)
        return flow_mod

    def __setstate__(self, d):
        self.match = ofp_match()
        self.match.__setstate__(d["match"])
        del d["match"]
        self.actions = []
        for a in d["actions"]:
            act = ofp_action(a)
            self.actions.append(act)
        del d["actions"]
        for key, value in d.items():
            setattr(self, key, value)

    def __getstate__(self):
        d = self.__dict__.copy()
        acts = d["actions"]
        d["actions"] = []

        def get_str(x):
            t = None if x is None else x.toStr()
            return t

        for a in acts:
            dic = a.__dict__.copy()
            dic["type"] = a.type
            if "nw_addr" in dic:
                dic["nw_addr"] = get_str(dic["nw_addr"])
            if "dl_addr" in dic:
                dic["dl_addr"] = get_str(dic["dl_addr"])
            d["actions"].append(dic)
        try:
            del d["data"]
            del d["cookie"]
            del d["_xid"]
            del d["_buffer_id"]
        except:
            pass
        return d


class ofp_rule(ofp_flow_mod):
    """
    Rule is much like FlowMod but doesn't contain command.
    """
    def __init__(self, match=None, actions=None, priority=None):
        ofp_flow_mod.__init__(self, match=match, actions=actions,
                              priority=priority)
        self.name = 'rule'

    @staticmethod
    def from_rule(fm):
        if not isinstance(fm, of.ofp_flow_mod):
            return
        rule = ofp_rule(match=fm.match, actions=fm.actions,
                        priority=fm.priority)
        return rule

    def __getstate__(self):
        d = ofp_flow_mod.__getstate__(self)
        if "command" in d:
            del d["command"]
        return d


class ofp_match(of.ofp_match):
    """
    Used to encode fields to text.
    """
    def __init__(self, m=None):
        if m is None:
            of.ofp_match.__init__(self)
            return
        self._locked = False
        for k, v in m.__dict__.items():
            setattr(self, k, v)

    def __setstate__(self, d):
        self._locked = False
        for k, v in d.items():
            if k != 'wildcards':
                setattr(self, k, v)
        if d.get("nw_src", None) is not None:
            self.nw_src = IPAddr(d["nw_src"])
        if d.get("nw_dst", None) is not None:
            self.nw_dst = IPAddr(d["nw_dst"])
        if d.get("dl_src", None) is not None:
            self.dl_src = EthAddr(d["dl_src"])
        if d.get("dl_dst", None) is not None:
            self.dl_dst = EthAddr(d["dl_dst"])
        try:
            if d['wildcards'] != self.wildcards:
                # ip src/dst has mask
                self.wildcards = d['wildcards']
        except:
            pass

    def __getstate__(self):
        d = {}
        for k in self.__dict__.keys():
            if k == "_locked":
                continue
            elif k.startswith('_'):
                d[k[1:]] = getattr(self, k[1:])
            else:
                d[k] = getattr(self, k)

        def get_str(x):
            t = None if x is None else x.toStr()
            return t
        d["nw_src"] = get_str(d["nw_src"])
        d["nw_dst"] = get_str(d["nw_dst"])
        d["dl_src"] = get_str(d["dl_src"])
        d["dl_dst"] = get_str(d["dl_dst"])
        return d


def ofp_action(d):
    """
    Action factory.
    Creates action object with appropriate type.
    Fills it with d.
    """
    cls = of._action_type_to_class[d["type"]]
    act = cls()
    del d["type"]
    act.__dict__ = d.copy()
    if "dl_addr" in d:
        act.dl_addr = EthAddr(d["dl_addr"])
    if "nw_addr" in d:
        act.nw_addr = IPAddr(d["nw_addr"])
    return act
