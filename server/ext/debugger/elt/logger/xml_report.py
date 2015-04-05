import xml.etree.ElementTree as ET
from .util import FlowModInfo, RuleInfo
import pox.openflow.libopenflow_01 as of
import re


def multiwordReplace(text, wordDic):
    """
    take a text and replace words that match a key in a dictionary with
    the associated value, return the changed text
    """
    rc = re.compile('|'.join(map(re.escape, wordDic)))

    def translate(match):
        return wordDic[match.group(0)]
    return rc.sub(translate, text)


class XmlMatch(ET.Element):
    """
    XML representation of ofp_match.
    """
    def __init__(self, match):
        ET.Element.__init__(self, 'match')
        for k in ["wildcards", "in_port", "dl_src", "dl_dst",
                  "dl_vlan", "dl_vlan_pcp", "dl_type", "nw_tos", "nw_proto",
                  "nw_src", "nw_dst", "tp_src",  "tp_dst"]:
            v = getattr(match, k, None)
            elem = ET.Element(k)
            elem.text = str(v)
            self.append(elem)


class XmlCode(ET.Element):
    """
    XML representation of call stacks.
    """
    def __init__(self, code):
        ET.Element.__init__(self, 'code')
        for t, call_stack in code:
            e = ET.Element(t)
            if isinstance(call_stack, basestring):
                elem = ET.Element('call')
                elem.text = call_stack
                e.append(elem)
            elif isinstance(call_stack, list):
                for module, line in call_stack:
                    elem = ET.Element('call')
                    name = ET.Element('name')
                    name.text = module + ' : ' + str(line)
                    elem.append(name)
                    m = ET.Element('module')
                    m.text = module
                    l = ET.Element('line')
                    l.text = str(line)
                    elem.append(m)
                    elem.append(l)
                    e.append(elem)
            else:
                raise TypeError("Call stack type invalid")
            self.append(e)


class XmlAction(ET.Element):
    """
    XML representation of ofp_action.
    """
    def __init__(self, action):
        s = of.ofp_action_type_map[action.type]
        ET.Element.__init__(self, s)
        for k, v in vars(action).items():
            elem = ET.Element(str(k))
            elem.text = str(v)
            self.append(elem)


class XmlActions(ET.Element):
    """
    XML representation of list of ofp_action.
    """
    def __init__(self, actions):
        ET.Element.__init__(self, 'actions')
        for action in actions:
            self.append(XmlAction(action))


class XmlFlowMod(ET.Element):
    """
    XML representation of ofp_flow_mod
    """
    def __init__(self, flow_mod):
        ET.Element.__init__(self, 'ofp_flow_mod')
        self.set_fields(flow_mod)

    def set_fields(self, flow_mod):
        for field in ['dpid', 'command', 'priority', 'cid']:
            try:
                elem = ET.Element(field)
                elem.text = str(getattr(flow_mod, field))
                self.append(elem)
            except:
                if field == 'command':
                    elem = ET.Element(field)
                    elem.text = 'None'
                    self.append(elem)
        self.append(XmlMatch(flow_mod.match))
        self.append(XmlActions(flow_mod.actions))


class XmlRule(XmlFlowMod):
    """
    XML representation of switch table rule.
    """
    def __init__(self, rule):
        ET.Element.__init__(self, 'rule')
        self.set_fields(rule)


class XmlInfo(ET.Element):
    """
    XML representation of FlowMod/Rule + Code
    """
    def __init__(self, info, code):
        ET.Element.__init__(self, 'entry')
        name = ET.Element('name')
        if isinstance(info, FlowModInfo):
            self.append(XmlFlowMod(info))
            name.text = 'ofp_flow_mod'
            self.append(name)
        elif isinstance(info, RuleInfo):
            self.append(XmlRule(info))
            name.text = 'rule'
            self.append(name)
        else:
            self.append(ET.Element('Empty'))
        self.append(XmlCode(code))


class XmlEntryGroup(ET.Element):
    """
    XML representation of EntryGroup.
    """
    def __init__(self, entry_group, children):
        ET.Element.__init__(self, "entry_group")
        name = ET.Element("name")
        name.text = entry_group.name
        self.append(name)
        desc = ET.Element("desc")
        desc.text = entry_group.desc
        self.append(desc)
        self.extend(children)


class XmlEvent(ET.Element):
    """
    XML representation of NetworkError.
    """
    def __init__(self, minfo):
        ET.Element.__init__(self, "event")
        name = ET.Element("name")
        name.text = minfo.event.time
        self.append(name)
        desc = ET.Element("desc")
        desc.text = minfo.event.desc
        self.append(desc)
        self.tail = '\n'

        for i, entry_group in enumerate(minfo.event.entry_groups):
            xml_entries = []
            for j in xrange(len(entry_group.entries)):
                xml_entries.append(XmlInfo(*minfo.get_info_and_code((i, j))))
            self.append(XmlEntryGroup(entry_group, xml_entries))


class XmlReport(object):
    """
    Report for messages from one source (conn_name).
    Writes to filename.
    """
    def __init__(self, filename, conn_name):
        self.filename = filename
        self.conn_name = conn_name
        self.clear()

    def clear(self):
        """
        Remove collected information.
        """
        self.result = ET.Element('client')
        name = ET.Element('name')
        name.text = self.conn_name
        self.result.append(name)
        self.result.text = "\n"
        self.events = {}

    def flush(self, name=None):
        """
        Save report to file.
        """
        if name is None:
            name = self.filename
        with open(name, 'w') as f:
            f.write(self.flushs())

    def flushs(self):
        """
        Save report to string.
        """
        subelements = []
        for s, e in self.events.items():
            tmp = list(e)
            # Set all subelements as text.
            e.text = '\n' + "".join([str(c) for c in tmp])
            # Clear subelements.
            for se in tmp:
                e.remove(se)
            subelements.append(tmp)

        report = (multiwordReplace(ET.tostring(self.result), {
            '&gt;': '>',
            '&lt;': '<',
            '&amp;': '&'
            }))
        # Restore subelements.
        index = 0
        for s, e in self.events.items():
            e.extend(subelements[index])
            index += 1

        return report

    def add_event(self, minfo):
        """
        Save report to memory.
        Doesn't write anywhere before flush().
        """
        s = minfo.event.name
        if s == "":
            s = "Empty"
        if s not in self.events:
            e = ET.SubElement(self.result, 'event_type')
            name = ET.Element('name')
            name.text = s
            e.append(ET.tostring(name))
            e.tail = '\n'
            e.text = '\n'
            self.events[s] = e
        xml = XmlEvent(minfo)
        # Cheat. Store strings instead of objects.
        self.events[s].append(ET.tostring(xml))
        return True
