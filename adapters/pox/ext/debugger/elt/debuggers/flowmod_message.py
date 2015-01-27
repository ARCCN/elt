from ..interaction import ofp_flow_mod
from ..message_server import Message


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
    def __init__(self, msg=None, masked=None, modified=None,
                 undefined=None, deleted=None):
        self.msg = msg
        self.masked = set(masked) if masked is not None else set()
        self.modified = set(modified) if modified is not None else set()
        self.undefined = set(undefined) if undefined is not None else set()
        self.deleted = set(deleted) if deleted is not None else set()

    def __getstate__(self):
        d = Message.__getstate__(self)
        if self.msg:
            d["msg"] = self.msg
        for field in ["masked", "modified", "undefined", "deleted"]:
            if len(getattr(self, field)) > 0:
            d[field] = list(getattr(self, field))

    def __setstate__(self, d):
        Message.__setstate__(self, d)
        if "msg" in d:
            self.msg = FlowModMessage()
            self.msg.__setstate__(self, d["msg"])
        for field in ["masked", "modified", "undefined", "deleted"]:
            if field in d:
                setattr(self, field, set())
                for m in d[field]:
                    fmm = FlowModMessage()
                    fmm.__setstate__(m)
                    getattr(self, field).add(fmm)

