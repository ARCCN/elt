import xml.etree.ElementTree as ET
from matches import FlowMatch, HistoryMatch

class XmlMatch(ET.Element):
    def __init__(self, match):
        ET.Element.__init__(self, 'match')
        for field, typ in match.headers:
            list, type = match.fields[field]
            elem = ET.Element(field)
            if list is None or list == []:
                elem.text = 'NULL'
            else:
                elem.text = str(list[0])
            self.append(elem)
 

class XmlFlowReport(ET.Element):
    def __init__(self, ID):
        ET.Element.__init__(self, 'id' + str(ID))

    def set_match(self, match):
        self.append(XmlMatch(match))
        for field, typ in match.headers:
            list, type = match.fields[field]
            elem = ET.Element('field')
            if list is None or list == []:
                elem.text = field + '=NULL'
            else:
                elem.text = field + '=' + str(list[0])
            self.append(elem)

            

    def add_comment(self, comment):
        com = ET.Element('comment')
        com.text = str(comment)
        self.append(com)

class XmlReport:

    categories = ["correct", "error", "uncheckable"]


    def __init__(self, filename):
        self.filename = filename
        self.clear()

    def clear(self):
        self.result = ET.Element('document')
        for cat in self.categories:
            setattr(self, cat, ET.SubElement(self.result, cat))
        self.current = None

    def flush(self, name = None):
        if name == None:
            name = self.filename
        tree = ET.ElementTree(self.result)
        tree.write(name)

    def new_flow(self, ID):
        self.current = XmlFlowReport(ID)
        return self.current

    def add_flow(self, category, flow_report = None):
        if category not in self.categories:
            return False
        if flow_report is None:
            flow_report = self.current

        getattr(self, category).append(flow_report)
        return True


        

