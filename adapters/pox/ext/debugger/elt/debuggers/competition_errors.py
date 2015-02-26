from ..network_error import NetworkError, Entry, EntryGroup
from ..interaction import ofp_flow_mod


class CompetitionError(NetworkError):
    """
    Common ancestor for all competition errors.
    """
    pass


class FlowMasked(CompetitionError):
    """
    Old flows are masked by a new one.
    """
    def __init__(self, masking_entry, masked_entries):
        CompetitionError.__init__(self)
        self.masking_entry = masking_entry
        self.masked_entries = masked_entries

    def __getstate__(self):
        d = NetworkError.__getstate__(self)
        d["entry_groups"] = []
        d["entry_groups"].append(EntryGroup(
            name="Masking",
            desc="This entry has higher priority",
            entries=[self.masking_entry]))
        d["entry_groups"].append(EntryGroup(
            name="Masked",
            desc="These entries have lower priority",
            entries=list(self.masked_entries)))
        return d

    def log(self):
        s = []
        s.append(CompetitionError.log(self)[0])
        s.append("Masking:\n")
        s.append(str(self.masking_entry))
        s.append("\nCode:\n%CODE\n")
        s.append("Masked:\n")
        s.append("".join([str(entry) + "\nCode:\n%CODE\n"
                          for entry in self.masked_entries]))
        args = [self.masking_entry]
        args.extend(self.masked_entries)
        return ("".join(s), args)


class FlowDeleted(CompetitionError):
    """
    Old flows are deleted.
    """
    def __init__(self, match_entry, deleted_entries):
        CompetitionError.__init__(self)
        self.match_entry = match_entry
        self.deleted_entries = deleted_entries

    def __getstate__(self):
        d = NetworkError.__getstate__(self)
        d["entry_groups"] = []
        d["entry_groups"].append(EntryGroup(
            name="Template",
            desc="Template for deleting",
            entries=[self.match_entry]))
        d["entry_groups"].append(EntryGroup(
            name="Deleted",
            desc="These entries were deleted",
            entries=list(self.deleted_entries)))
        return d

    def log(self):
        s = []
        s.append(CompetitionError.log(self)[0])
        s.append("Match:\n")
        s.append(str(self.match_entry))
        s.append("\nCode:\n%CODE\n")
        s.append("Deleted:\n")
        s.append("".join([str(entry) + "\nCode:\n%CODE\n"
                          for entry in self.deleted_entries]))
        args = [self.match_entry]
        args.extend(self.deleted_entries)
        return ("".join(s), args)


class FlowModified(CompetitionError):
    """
    Old flows' actions are replaced by those from a new one.
    """
    def __init__(self, match_entry, old_entries):
        CompetitionError.__init__(self)
        self.match_entry = match_entry
        self.old_entries = old_entries

    def __getstate__(self):
        d = NetworkError.__getstate__(self)
        d["entry_groups"] = []
        d["entry_groups"].append(EntryGroup(
            name="Template",
            desc="Modification event",
            entries=[self.match_entry]))
        d["entry_groups"].append(EntryGroup(
            name="Old",
            desc="Matching entries before modification",
            entries=list(self.old_entries)))
        return d

    def log(self):
        s = CompetitionError.log(self)[0]
        s += "Match:\n"
        s += str(self.match_entry) + "\nCode:\n%CODE\n"
        s += "Old:\n"
        s += "".join([str(entry) + "\nCode:\n%CODE\n"
                      for entry in self.old_entries])
        args = [self.match_entry]
        args.extend(self.old_entries)
        return (s, args)


class FlowUndefined(CompetitionError):
    """
    New flow is inserted that overlaps with existing ones.
    """
    def __init__(self, new_entry, old_entries):
        CompetitionError.__init__(self)
        self.new_entry = new_entry
        self.old_entries = old_entries

    def __getstate__(self):
        d = NetworkError.__getstate__(self)
        d["entry_groups"] = []
        d["entry_groups"].append(EntryGroup(
            name="Added",
            desc="This entry was just added",
            entries=[self.new_entry]))
        d["entry_groups"].append(EntryGroup(
            name="Old",
            desc="These entries were installed before",
            entries=list(self.old_entries)))
        return d

    def log(self):
        s = CompetitionError.log(self)[0]
        s += "New:\n"
        s += str(self.new_entry) + "\nCode:\n%CODE\n"
        s += "Old:\n"
        s += "".join([str(entry) + "\nCode:\n%CODE\n"
                      for entry in self.old_entries])
        args = [self.new_entry]
        args.extend(self.old_entries)
        return (s, args)


class FakeError(NetworkError):
    """
    For tests.
    """
    def __init__(self, dpid=None, flow_mod=None):
        NetworkError.__init__(self)
        self.flow_mod = ofp_flow_mod.from_flow_mod(flow_mod)
        if flow_mod is not None:
            self.entry_groups.append(EntryGroup(
                name="Fake Group", desc="No comments",
                entries=[Entry(self.flow_mod, dpid)]))

    def log(self):
        s = []
        s.append(NetworkError.log(self)[0])
        s.append("Self:\n")
        s.append(str(self.flow_mod))
        s.append("\nCode:\n%CODE\n")
        return ("".join(s))
