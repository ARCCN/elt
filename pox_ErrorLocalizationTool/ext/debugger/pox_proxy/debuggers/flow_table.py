# This file is part of ErrorLocalizationTool.

# Contains CompetitionError classes.
# Contains FlowTable and utilities.
# TODO: Debug. Why there are deletions with l2_learning?
import copy
from pytrie import Trie

from pox.openflow.flow_table import (TableEntry, FlowTable, 
                                     FlowTableModification)
import pox.openflow.libopenflow_01 as of

from ..util import profile, ip_to_uint

from .competition_errors import (FlowMasked, FlowModified, 
                                 FlowUndefined, FlowDeleted)


def ip_to_key(addr):
    """Generate a trie key."""
    if addr is None:
        return ''
    if not isinstance(addr, tuple):
        return bin(ip_to_uint(addr))
    if addr[1] == 0 or addr[0] is None:
        return ''
    return bin(ip_to_uint(addr[0]))[2:2 + addr[1]]


class TableEntryTag(object):

    def __init__(self, local_id=None, flowmod_id=None):
        self.local_id = local_id
        self.flowmod_id = flowmod_id


class TaggedTableEntry(TableEntry):

    """
    Each table entry contains tag (local_id, flowmod_id).
    local_id        id for using inside a session.
                    Local pointer to assign flowmod_id later.
    flowmod_id      id for using between sessions.
                    The pointer in database.
    """

    def __init__(self, priority=of.OFP_DEFAULT_PRIORITY, cookie=0,
                 idle_timeout=0, hard_timeout=0, flags=0, match=None,
                 actions=[], buffer_id=None, now=None, local_id=None,
                 flowmod_id=None, command=None, dpid=None):
        if match is None:
            match = of.ofp_match()
        TableEntry.__init__(self, priority, cookie, idle_timeout, hard_timeout,
                            flags, match, actions, buffer_id, now)
        self.tag = TableEntryTag(local_id, flowmod_id)
        self.command = command
        self.dpid = dpid
        self.entry_name = "ofp_flow_mod"

    @staticmethod
    def from_flow_mod_tag(flow_mod, dpid, local_id=None, flowmod_id=None):
        """Create new Entry with given ids."""
        priority = flow_mod.priority
        cookie = flow_mod.cookie
        match = flow_mod.match
        actions = flow_mod.actions
        buffer_id = flow_mod.buffer_id
        flags = flow_mod.flags
        command = flow_mod.command
        return TaggedTableEntry(priority, cookie, flow_mod.idle_timeout,
                                flow_mod.hard_timeout, flags, match, actions,
                                buffer_id, local_id=local_id,
                                flowmod_id=flowmod_id, command=command, 
                                dpid=dpid)

    @staticmethod
    def from_flow_rem(flow_rem):
        priority = flow_rem.priority
        match = flow_rem.match
        return TaggedTableEntry(priority=priority, match=match)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        s = ("priority=%s, cookie=%x, idle_timeoout=%d," +
             " hard_timeout=%d \nmatch=\n%sactions=\n")
        s = s % (self.priority, self.cookie, self.idle_timeout,
                 self.hard_timeout, self.match.show(' '))
        s += "%s" * len(self.actions) + "buffer_id=%s"
        s = s % (tuple([' ' + of.ofp_action_type_map[action.type] + '\n' +
                        action.show('  ') for action in self.actions]) +
                 (str(self.buffer_id), ))
        return s


class TaggedFlowTable(FlowTable):

    """
    Model a flow table for our switch implementation.
    Handles the behavior in response to the OF messages send to the switch.
    O(N) lookup in trade for fast (O(1)?) addition and deletion.
    Additional memory for indexes on each field.

    Features:
    Tags:
      Each entry has tag value equal to last modification flowmod_id.
      Main usage is handling links to database.

    Competition errors detection:
      While processing every FlowMod we check for errors.
      It is done by checking overlaps on additions
      and ownership on modifications and deletions.

    Sorting off:
      Sorting greatly reduces performance.
      Using set as main container for faster addition/deletion.

    Optimization for overlap checking:
      nw_src, nw_dst -> Pytrie { prefix : set(Entry) }.
      other fields -> dict { (None if wildcarded else value) : set(Entry) }.

    """

    _eventMixin_events = set([
        FlowTableModification,
        FlowMasked,
        FlowDeleted,
        FlowModified,
        FlowUndefined
    ])

    dict_field_names = [
        'in_port',
        'dl_vlan',
        'dl_src',
        'dl_dst',
        'dl_type',
        'nw_proto',
        'tp_src',
        'tp_dst',
        'dl_vlan_pcp',
        'nw_tos'
    ]

    trie_field_names = [
        'nw_src',
        'nw_dst'
    ]

    def __init__(self, dpid=None, nexus=None):
        FlowTable.__init__(self)
        self.nexus = nexus
        self._table = set()
        # Used by controller to select Table by local_id.
        self.local_ids = {}
        self.dpid = dpid
        self.fields = {}
        for f in self.dict_field_names:
            self.fields[f] = {}
        for f in self.trie_field_names:
            self.fields[f] = Trie()

    def add_entry(self, entry):
        """
        Sorting dramatically decreases addition speed
        so an option to disable it is useful.
        """
        if not isinstance(entry, TableEntry):
            raise "Not an Entry type"
        self._table.add(entry)
        self.raiseEvent(FlowTableModification(added=[entry]))

    def remove_entry(self, entry):
        if not isinstance(entry, TableEntry):
            raise "Not an Entry type"
        self._table.discard(entry)
        self.raiseEvent(FlowTableModification(removed=[entry]))

    def entry_for_packet(self, packet, in_port):
        """
        Return the highest priority flow table entry that matches
        the given packet on the given in_port, or None
        if no matching entry is found.
        """
        packet_match = of.ofp_match.from_packet(packet, in_port)
        entries = []
        for entry in self._table:
            if entry.match.matches_with_wildcards(packet_match,
                                                  consider_other_wildcards=
                                                  False):
                if not entry.match.is_wildcarded:
                    return entry
                entries.append(entry)
        if len(entries) == 0:
            return None
        max_p = entries[0].priority
        max_entry = entries[0]
        for entry in entries:
            if entry.priority > max_p:
                max_p = entry.priority
                max_entry = entry
        return max_entry

    def process_flow_removed(self, flow_rem):
        current = TaggedTableEntry.from_flow_rem(flow_rem)
        return self.delete_error_checking(current, is_strict=True,
                                          raise_error=False)

    #@profile
    def process_flow_mod(self, flow_mod, local_id=None, flowmod_id=None):
        """
        Process a flow mod sent to the switch
        @return a tuple (added|modified|removed, [list of affected entries])
        (For compatibitily with SwitchFlowTable).

        Raise events in case of competition errors:
        ADD ->      FlowMasked(lower priority, highed priority),
                    FlowModified(equal priority, equal match),
                    FlowUndefined(equal priority, overlapping match)
        MODIFY ->   FlowMasked(as ADD),
                    FlowModified(as MODIFY),
                    FlowUndefined(as ADD)
        DELETE ->   FlowDeleted
        """
        if(flow_mod.flags & of.OFPFF_CHECK_OVERLAP):
            # Safe insertion
            check_overlap = True
        else:
            check_overlap = False
        if(flow_mod.out_port != of.OFPP_NONE and
           flow_mod.command == of.ofp_flow_mod_command_rev_map['OFPFC_DELETE']):
            raise NotImplementedError(
                "flow_mod outport checking not implemented")

        current = TaggedTableEntry.from_flow_mod_tag(flow_mod, self.dpid,
                                                     local_id, flowmod_id)
        current.entry_name = "ofp_flow_mod"
        result = None
        if flow_mod.command == of.OFPFC_ADD:
            result = self.add_entry_error_checking(current, check_overlap)
        elif (flow_mod.command == of.OFPFC_MODIFY or
              flow_mod.command == of.OFPFC_MODIFY_STRICT):
            is_strict = (flow_mod.command == of.OFPFC_MODIFY_STRICT)
            result = self.modify_error_checking(current,
                                              is_strict, check_overlap)
        elif (flow_mod.command == of.OFPFC_DELETE or
              flow_mod.command == of.OFPFC_DELETE_STRICT):
            is_strict = (flow_mod.command == of.OFPFC_DELETE_STRICT)
            result = self.delete_error_checking(current, is_strict)
        else:
            raise AttributeError("Command not yet implemented: %s" %
                                 flow_mod.command)
        current.entry_name = "rule"
        return result

    def add_entry_error_checking(self, current, check_overlap):
        """ Add entry to table raising CompetitionErrors if necessary."""
        # Candidates for modifying/masking/undefined behavior
        # 0.2ms
        overlapping = self.overlapping_entries(current.match,
                                               inner=True, outer=True)

        # exactly matching entries have to be removed
        # 0.01ms
        exact = self.select_matching_entries(overlapping, current.match,
                                             current.priority, strict=True)
        # Openflow-overlapping with CHECK_OVERLAP -> early exit, no events.
        if check_overlap and len(exact) > 0:
            return ("added", [])
        self.remove_entries_simple(exact)

        modified = {}
        masked = {}
        undefined = {}

        # exactly matching -> modified
        modified[current] = set()
        for entry in exact:
            for a1, a2 in zip(current.actions, entry.actions):
                if a1 != a2:
                    print a1.max_len, a2.max_len
                    modified[current].add(entry)
                    break
        overlapping -= exact

        masked[current] = set()
        undefined[current] = set()
        for entry in overlapping:
            # overlapping with lower effective priority -> masked
            # TODO: In OF 1.1+, exact matching no longer matters.
            if (entry.priority < current.priority or
                    entry.match.is_wildcarded() and
                    not current.match.is_wildcarded()):
                masked[current].add(entry)
            # wc, overlapping with equal priority -> undefined behavior
            # TODO: exact matching no longer matters
            elif (entry.priority == current.priority and
                  entry.match.is_wildcarded()):
                undefined[current].add(entry)
            else:
                # overlapping with higher eff. priority -> current is masked
                masked[entry] = {current}

        # Two classes with equal priority
        if (check_overlap and
                len(undefined[current]) + len(modified[current]) > 0):
            return ("added", [])

        self.raise_competition(masked, None, modified, undefined)
        #print 'added', len(self._table)
        # 0.15ms
        return self.add_entry_simple(current)

    def modify_error_checking(self, current, is_strict=False,
                              check_overlap=False):
        modified = []
        flow_modified = {current: set()}
        if is_strict:
            overlapping = self.overlapping_entries(current.match,
                                                   inner=False, outer=False)
        else:
            overlapping = self.overlapping_entries(current.match,
                                                   inner=True, outer=False)
        for entry in overlapping:
            if entry.priority == current.priority:
                flow_modified[current].add(copy.deepcopy(entry))
                self.remove_local_id(entry.tag.local_id)
                entry.tag = copy.deepcopy(current.tag)
                entry.actions = current.actions
                modified.append(entry)

        if(len(modified) == 0):
            # if no matching entry is found, modify acts as add
            return self.add_entry_error_checking(current, check_overlap)
        else:
            self.add_local_id(current.tag.local_id, modified)
            self.raise_competition(modified=flow_modified)
            print 'modified'
            return ("modified", modified)

    def delete_error_checking(self, current, is_strict=False,
                              raise_error=True):
        removed = []
        if is_strict:
            overlapping = self.overlapping_entries(current.match,
                                                   inner=False, outer=False)
        else:
            overlapping = self.overlapping_entries(current.match,
                                                   inner=True, outer=False)
        for entry in overlapping:
            if entry.priority == current.priority:
                removed.append(entry)
        #print 'Removed', len(removed),'/', len(self._table)
        if raise_error:
            print 'Raising'
            deleted = {current: set(removed)}
            self.raise_competition(deleted=deleted)
        return self.remove_entries_simple(removed)

    def add_entry_simple(self, current):
        """ Add entry and set indexes."""
        self.add_local_id(current.tag.local_id)
        for f in self.dict_field_names:
            attr = getattr(current.match, f)
            if attr not in self.fields[f]:
                self.fields[f][attr] = {current}
            else:
                self.fields[f][attr].add(current)

        for f in self.trie_field_names:
            attr = ip_to_key(getattr(current.match, f))
            if attr not in self.fields[f]:
                self.fields[f][attr] = {current}
            else:
                self.fields[f][attr].add(current)

        return ("added", self.add_entry(current))

    def select_matching_entries(self, entries, match, priority=0,
                                strict=False, out_port=None):
        return {entry for entry in entries
                if entry.is_matched_by(match, priority, strict, out_port)}

    def remove_entries_simple(self, removed):
        """ Remove entries and clear indexes."""
        for entry in removed:
            self.remove_local_id(entry.tag.local_id)

        for f in self.dict_field_names:
            for current in removed:
                attr = getattr(current.match, f)
                self.fields[f][attr].discard(current)

        for f in self.trie_field_names:
            for current in removed:
                attr = ip_to_key(getattr(current.match, f))
                self.fields[f][attr].discard(current)

        return ("removed", self.remove_entries(removed))

    def remove_entries(self, remove_flows):
        """Just a wrapper."""
        for entry in remove_flows:
            self._table.discard(entry)
        self.raiseEvent(FlowTableModification(removed=remove_flows))
        return remove_flows

    def overlapping_entries(self, match, inner=True, outer=True):
        """
        The main bottleneck. Get all entries from table
        whose matches intersect with given.
        IP addresses have very high cardinality. So we get possible value set
        from IP address trie and then use A & (B | C) = (A & B) | (A & C) to
        minimize complexity.

        inner, outer
        True, True      {x : flow(x) intersects flow(match)}
        False, False    {x : flow(x) == flow(match)}
        True, False     {x : flow(x) <= flow(match)}
        False, True     {x : flow(x) >= flow(match)}

        """
        # Wildcarded fields match with everything, no need to check.
        non_wc = [f for f in self.dict_field_names
                  if getattr(match, f) is not None]
        wc = [f for f in self.dict_field_names if f not in non_wc]
        sets = []

        # 0.15ms
        for f in self.trie_field_names:
            attr = ip_to_key(getattr(match, f))
            s = set([])
            if outer:
                for i in self.fields[f].iter_prefix_values(attr):
                    s |= i
            if inner:
                for i in self.fields[f].values(attr):
                    s |= i
            if not inner and not outer:
                s |= self.fields[f].get(attr, set())
            if len(s) == 0:
                return s
            sets.append(s)

        # Hopefully it has small size.
        search_set = set.intersection(*sets)

        # 0.05ms
        for f in non_wc:
            attr = getattr(match, f)
            if outer:
                search_set = ((search_set &
                               self.fields[f].get(attr, set())) |
                              (search_set &
                               self.fields[f].get(None, set())))
            elif inner or (not inner and not outer):
                search_set = search_set & self.fields[f].get(attr, set())
        for f in wc:
            if not inner:
                search_set = search_set & self.fields[f].get(None, set())

        return search_set

    def raise_competition(self, masked=None, deleted=None,
                          modified=None, undefined=None):
        """ Raise CompetitionError events. """
        # TODO: Work aroung targeted events.
        # Now not really raising events
        events = []
        if self.nexus is None:
            return
        if masked is not None:
            for k in masked.keys():
                if len(masked[k]) > 0:
                    e = FlowMasked(self.dpid, k, masked[k])
                    events.append(e)
        if deleted is not None:
            for k in deleted.keys():
                if len(deleted[k]) > 0:
                    e = FlowDeleted(self.dpid, k, deleted[k])
                    events.append(e)
        if modified is not None:
            for k in modified.keys():
                if len(modified[k]) > 0:
                    e = FlowModified(self.dpid, k, modified[k])
                    events.append(e)
        if undefined is not None:
            for k in undefined.keys():
                if len(undefined[k]) > 0:
                    e = FlowUndefined(self.dpid, k, undefined[k])
                    events.append(e)
        for e in events:
            self.nexus.handle_CompetitionError(e)

    def assign_flowmod_id(self, local_id, flowmod_id):
        """ Set flowmod_id by local_id. """
        for entry in self._table:
            if entry.local_id == local_id:
                entry.flowmod_id = flowmod_id

    def add_local_id(self, local_id, count=1):
        if local_id not in self.local_ids:
            self.local_ids[local_id] = count
        else:
            self.local_ids[local_id] += count

    def remove_local_id(self, local_id, count=1):
        if local_id in self.local_ids:
            self.local_ids[local_id] -= count
        if self.local_ids[local_id] <= 0:
            del self.local_ids[local_id]
