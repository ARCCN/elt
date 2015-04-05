from ..interaction import ofp_flow_mod, ofp_rule, instantiate_fm_or_rule


def show_entry(entry):
    return ("priority=%s, cookie=%x, idle_timeoout=%d, hard_timeout=%d," +
            " match=%s, actions=%s buffer_id=%s") % (
        entry.priority, entry.cookie, entry.idle_timeout, entry.hard_timeout,
        entry.match, repr(entry.actions), str(entry.buffer_id))


class Entry(object):
    """
    FlowMod/Rule + dpid of target switch.
    """
    def __init__(self, data=None, dpid=None, cid=None):
        self.data = data
        self.dpid = dpid
        self.cid = cid
        if hasattr(data, "name"):
            self.name = data.name

    def __setstate__(self, d):
        self.dpid = d.get("dpid")
        self.cid = d.get("cid")
        self.data = instantiate_fm_or_rule(d.get("data"))
        if hasattr(self.data, "name"):
            self.name = self.data.name

    @staticmethod
    def create_flow_mod(dpid, match, actions, command, priority, cid=None):
        return Entry(ofp_flow_mod(match, actions, command, priority), dpid, cid)

    @staticmethod
    def create_rule(dpid, match, actions, priority):
        return Entry(ofp_rule(match, actions, priority), dpid)


class EntryGroup(object):
    """
    Group of entries with name and description.
    """
    def __init__(self, name="", desc="", entries=None):
        self.name = name
        self.desc = desc
        self.entries = []
        if entries is None:
            return
        for e in entries:
            if isinstance(e, Entry):
                self.entries.append(e)
            else:
                try:
                    t = e.entry_name.lower()
                    if t in ["ofp_flow_mod", "flow_mod",
                             "flowmod", "ofpflowmod"]:
                        self.entries.append(Entry.create_flow_mod(
                            e.dpid, e.match, e.actions, e.command, e.priority))
                    elif t in ["ofp_rule", "rule", "ofprule"]:
                        self.entries.append(Entry.create_rule(
                            e.dpid, e.match, e.actions, e.priority))
                    else:
                        raise TypeError("Unsupported type")
                except:
                    self.entries = []
                    return

    def __setstate__(self, d):
        self.name = d.get("name", "")
        self.desc = d.get("desc", "")
        self.entries = []
        entries = d.get("entries", [])
        for e in entries:
            x = Entry()
            x.__setstate__(e)
            self.entries.append(x)
