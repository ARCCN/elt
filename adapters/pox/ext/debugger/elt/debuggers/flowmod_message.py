from ..interaction import ofp_flow_mod, ofp_rule
from ..message_server import Message
from ..network_error import Entry
import competition_errors

class TableEntryTag(object):

    def __init__(self, apps=None, nodes=None):
        self.apps = set(apps) if apps is not None else set()
        self.nodes = set(nodes) if nodes is not None else set()

    def __getstate__(self):
        d = {}
        if len(self.apps) > 0:
            d["apps"] = list(self.apps)
        if len(self.nodes) > 0:
            d["nodes"] = list(self.nodes)
        return d

    def __setstate__(self, d):
        if "apps" in d:
            self.apps = set(d["apps"])
        if "nodes" in d:
            self.nodes = set(d["nodes"])


class FlowModMessage(Message):
    def __init__(self, flow_mod=None, dpid=None, tag=None):
        Message.__init__(self)
        self.flow_mod = flow_mod
        self.dpid = dpid
        self.tag = tag

    def __getstate__(self):
        d = Message.__getstate__(self)
        if self.flow_mod:
            d["flow_mod"] = self.flow_mod
        if self.dpid:
            d["dpid"] = self.dpid
        if self.tag:
            d["tag"] = self.tag
        return d

    def __setstate__(self, d):
        Message.__setstate__(self, d)
        if "flow_mod" in d:
            self.flow_mod = ofp_flow_mod()
            self.flow_mod.__setstate__(d["flow_mod"])
        if "dpid" in d:
            self.dpid = d["dpid"]
        if "tag" in d:
            self.tag = TableEntryTag()
            self.tag.__setstate__(d["tag"])


class CompetitionErrorMessage(Message):
    def __init__(self):
        Message.__init__(self)
        self.errors = []

    def __getstate__(self):
        d = Message.__getstate__(self)
        d["errors"] = self.errors
        return d

    def fmm_to_entry(self, fmm):
        if fmm.flow_mod.command == -1:
            # rule
            return Entry(ofp_rule.from_rule(fmm.flow_mod), int(fmm.dpid))
        else:
            # flow_mod message
            cid = None
            try:
                cid = fmm.tag.nodes.pop() if len(fmm.tag.nodes) == 1 else None
                fmm.tag.nodes.add(cid)
            except:
                pass
            return Entry(fmm.flow_mod, int(fmm.dpid), cid)

    def __setstate__(self, d):
        Message.__setstate__(self, d)
        self.errors = []
        try:
            if "errors" in d:
                for error in d["errors"]:
                    if "name" in error:
                        if not isinstance(error["key"], FlowModMessage):
                            err = FlowModMessage()
                            err.__setstate__(error["key"])
                            error["key"] = err
                        err_list = []
                        for d_err in error["value"]:
                            if not isinstance(d_err, FlowModMessage):
                                err = FlowModMessage()
                                err.__setstate__(d_err)
                                d_err = err
                            err_list.append(d_err)
                        error["value"] = err_list

                        error["key"] = self.fmm_to_entry(error["key"])
                        error["value"] = [self.fmm_to_entry(x) for x in error["value"]]

                        c = getattr(competition_errors, error["name"])
                        self.errors.append(c(error["key"], error["value"]))

        except:
            import traceback
            traceback.print_exc()

