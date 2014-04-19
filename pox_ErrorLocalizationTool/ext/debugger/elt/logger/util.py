import re

from ..message_server import Message
from ..util import app_logging


log = app_logging.getLogger('Log Utils')
code = re.compile('%CODE')


class FlowModInfo:
    """
    All we need to retrieve FlowMod from Database.
    """
    def __init__(self, entry):
        dpid, flow_mod = entry
        self.dpid = dpid
        self.match = flow_mod.match
        self.actions = flow_mod.actions
        self.command = flow_mod.command
        self.priority = flow_mod.priority

    def __str__(self):
        return (str(self.dpid) + '\n' + str(self.match) +
                '\n' + str(self.actions))


class RuleInfo:
    def __init__(self, entry):
        dpid, rule = entry
        self.dpid = dpid
        self.match = rule.match
        self.actions = rule.actions
        self.priority = rule.priority


class MessageInfo():
    """
    Utility for a single error message.
    Has multiple text <parts> with call stacks between them.
    Each call stack is associated with QueryID(qid) and FlowModInfo.
    Traces how many unanswered queries are remaining.
    """
    def __init__(self, infos, qids, indices, event):
        if len(infos) != len(qids) or len(qids) != len(indices):
            raise Exception('Wrong length')
        self.code = {}  # qid -> code
        self.infos = {}  # qid -> info
        self.qids = qids
        self.indices = indices
        self.indices_to_qids = {}
        self.unanswered = len(qids)
        self.query_count = {}
        for i, qid in enumerate(qids):
            self.infos[qid] = infos[i]
            self.code[qid] = None
            self.query_count[qid] = 0
        self.event = event

    def set_code(self, qid, code):
        """
        Set call stack for qid.
        """
        if self.code[qid] is None:
            self.unanswered -= self.qids.count(qid)
        self.code[qid] = code

    def filled(self):
        filled = (self.unanswered == 0)
        if filled:
            for i, qid in enumerate(self.qids):
                self.indices_to_qids[self.indices[i]] = qid
        return filled

    def get_info_and_code(self, index_pair):
        qid = self.indices_to_qids[index_pair]
        return (self.infos[qid], self.code[qid])

    def change_qid(self, old_qid, new_qid):
        """
        Remove <old_qid>, insert <new_qid> instead.
        Used for repeated queries with the same FlowMod.
        """
        count = 0
        for i, v in enumerate(self.qids):
            if v == old_qid:
                count += 1
                self.qids[i] = new_qid
        if count == 0:
            return
        self.code[new_qid] = self.code[old_qid]
        del self.code[old_qid]
        self.infos[new_qid] = self.infos[old_qid]
        del self.infos[old_qid]
        self.query_count[new_qid] = self.query_count[old_qid]
        del self.query_count[old_qid]

    def __str__(self):
        """
        Construct textual log message.
        """
        self.parts = code.split(self.event.log())
        text = ""
        for part, qid in zip(self.parts, self.qids):
            c = ""
            res = self.code[qid]
            for entry in res:
                c += entry[0] + '\n'
                if isinstance(entry[1], basestring):
                    c += '  ' + str(entry[1]) + '\n'
                elif isinstance(entry[1], tuple) or isinstance(entry[1], list):
                    c += '\n'.join(['  ' + str(r) for r in entry[1]]) + '\n'
            text += part + c
        text += self.parts[-1]
        return text

    def get_data(self):
        res = []
        for qid in self.qids:
            res.append((self.infos[qid], self.code[qid]))
        return res

    def get_query_count(self, qid):
        return self.query_count[qid]

    def inc_query_count(self, qid):
        self.query_count[qid] += 1


class ReQuery(Message):
    """
    Send specific query later.
    """
    def __init__(self, info, qid):
        self.info = info
        self.qid = qid
