from pox.lib.revent.revent import Event
import time
from .interaction import ofp_flow_mod, ofp_rule, instantiate_fm_or_rule

"""
Event format
Event: {name, desc, time, entry_groups}
entry_groups: [EntryGroup, EntryGroup, EntryGroup]
EntryGroup: {name, desc, entries}
entries: [Entry, Entry, Entry]
Entry: {name, desc, data}
data: ofp_flow_mod | ofp_rule
"""



def show_entry(entry):
    return ("priority=%s, cookie=%x, idle_timeoout=%d, hard_timeout=%d," +
            " match=%s, actions=%s buffer_id=%s") % (
        entry.priority, entry.cookie, entry.idle_timeout, entry.hard_timeout,
        entry.match, repr(entry.actions), str(entry.buffer_id))


class Entry:
    def __init__(self, data=None, dpid=None):
        self.data = data
        self.dpid = dpid
        try:
            self.name = data.name
        except:
            pass
        
    def __setstate__(self, d):
        self.dpid = d.get("dpid")
        self.data = instantiate_fm_or_rule(d.get("data"))
        try:
            self.name = self.data.name
        except:
            pass
        
    @staticmethod
    def create_flow_mod(dpid, match, actions, command, priority):
        e = Entry()
        e.data = ofp_flow_mod(match, actions, command, priority)
        e.dpid = dpid
        return e
    
    @staticmethod
    def create_rule(dpid, match, actions, priority):
        e = Entry()
        e.data = ofp_rule(match, actions, priority)
        e.dpid = dpid
        return e


class EntryGroup:
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


class NetworkError(Event):
    """
    Provides unpacking by name.
    """
    def __init__(self):
        self._name = str(self.__class__).rsplit('.', 1)[1][:-2]
        t = time.time()
        self.time = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime(t))
        self.time += "." + "%03d" % (int((t - int(t)) * 1000))
        self.desc = "No description"
        self.entry_groups = []
        
    @property
    def name(self):
        return self._name
        
    def __setstate__(self, d):
        self._name = d.get("_name", self._name)
        self.desc = d.get("desc", "")
        if "time" in d:
            self.time = d["time"]
        if "entry_groups" in d:
            self.entry_groups = []
            for eg in d["entry_groups"]:
                g = EntryGroup()
                g.__setstate__(eg)
                self.entry_groups.append(g)
                
    def __getstate__(self):
        d = {}
        d["_name"] = self._name
        d["desc"] = self.desc
        d["time"] = self.time
        d["entry_groups"] = self.entry_groups
        return d
    
    def log(self):
        """
        Return the message to be saved to log.
        %CODE is used for call stack substitution.
        """
        return "%s:\n" % (type(self))
    
    def args(self):
        """
        Return [Entry1, Entry2, ...] to be used 
        for call stack retrieval.
        """
        args = []
        for eg in self.entry_groups:
            for e in eg.entries:
                args.append(e)
        return args
    
    def indices(self):
        """
        Return [(Group_index, Entry_index)]
        for entries in args.
        """
        indices = []
        for eg_i in xrange(len(self.entry_groups)):
            for e_i in xrange(len(self.entry_groups[eg_i].entries)):
                indices.append((eg_i, e_i))
        return indices