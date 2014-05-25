import sys

import pox.openflow.libopenflow_01 as of

from ..interaction import ofp_flow_mod, ofp_rule
from ..message_server import Message, ClosingMessage


class FlowModMessage(Message):
    """
    FlowMod info to be stored to Database.
    """
    def __init__(self, dpid=None, data=None, code_entries=None):
        Message.__init__(self)
        self.dpid = dpid
        if isinstance(data, ofp_flow_mod):
            self.data = data
        else:
            self.data = ofp_flow_mod.from_flow_mod(data)
        self.code_entries = code_entries

    def __setstate__(self, d):
        if "dpid" in d:
            self.dpid = d['dpid']
        if "data" in d:
            self.data = ofp_flow_mod()
            self.data.__setstate__(d['data'])
        if "code_entries" in d:
            self.code_entries = [tuple(ce) for ce in d['code_entries']]


class FlowModQuery(Message):
    """
    Request call stack for FlowMod.
    Reply's qid must be identical.
    """
    def __init__(self, dpid=None, data=None, qid=-1):
        Message.__init__(self)
        self.dpid = dpid
        if isinstance(data, ofp_flow_mod):
            self.data = data
        else:
            self.data = ofp_flow_mod.from_flow_mod(data)
        self.qid = qid

    def __setstate__(self, d):
        if "dpid" in d:
            self.dpid = d['dpid']
        if "data" in d:
            self.data = ofp_flow_mod()
            self.data.__setstate__(d['data'])
        if "qid" in d:
            self.qid = d['qid']


class RuleQuery(Message):
    """
    Request call stacks for rule.
    May contain one ADD and multiple MODIFYs.
    """
    def __init__(self, dpid=None, data=None, qid=-1):
        Message.__init__(self)
        self.dpid = dpid
        if isinstance(data, ofp_rule):
            self.data = data
        else:
            self.data = ofp_rule.from_rule(data)
        self.qid = qid

    def __setstate__(self, d):
        if "dpid" in d:
            self.dpid = d['dpid']
        if "data" in d:
            self.data = ofp_rule()
            self.data.__setstate__(d['data'])
        if "qid" in d:
            self.qid = d['qid']


class QueryReply(Message):
    """
    Call stack for FM/Rule.
    """
    def __init__(self, code=None, qid=-1):
        Message.__init__(self)
        self.code = code
        self.qid = qid

    def __setstate__(self, d):
        if "qid" in d:
            self.qid = d["qid"]
        if "code" in d:
            code = d["code"]
            self.code = []
            if code is None:
                return
            # [['ADD', [[module, line], ]], ]
            code = [tuple(row) for row in code]
            #[('ADD', [[module, line], ])]
            for type, c in code:
                if isinstance(c, basestring):
                    self.code.append((type, c))
                else:
                    self.code.append((type, [tuple(row) for row in c]))
            # [('ADD', [(module, line), (module, line)]),
            #  ('MODIFY', 'Not found')]
