import time
from .entries import Entry, EntryGroup


"""
Event format
Event: {name, desc, time, entry_groups}
entry_groups: [EntryGroup, EntryGroup, EntryGroup]
EntryGroup: {name, desc, entries}
entries: [Entry, Entry, Entry]
Entry: {name, desc, data}
data: ofp_flow_mod | ofp_rule
"""


class BaseError(object): # Maybe inherit message_server.Message?
    """
    Common ancestor for all errors processed by our system.
    Provides unpacking by name.
    """
    def __init__(self):
        self._name = str(self.__class__).rsplit('.', 1)[1][:-2]

    @property
    def name(self):
        return self._name

    def __setstate__(self, d):
        self._name = d.get("_name", self._name)

    def __getstate__(self):
        return {"_name": self._name}


class NetworkError(BaseError):
    """
    Common ancestor for all errors processed by our system.
    Provides unpacking by name.
    """
    def __init__(self):
        BaseError.__init__(self)
        t = time.time()
        self.time = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime(t))
        self.time += "." + "%03d" % (int((t - int(t)) * 1000))
        self.desc = "No description"
        self.entry_groups = []

    @property
    def name(self):
        return self._name

    def __setstate__(self, d):
        BaseError.__setstate__(self, d)
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
        d = BaseError.__getstate__(self)
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

    def __str__(self):
        return "\n".join([str(e.data.match) for group in self.entry_groups
                          for e in group.entries])
