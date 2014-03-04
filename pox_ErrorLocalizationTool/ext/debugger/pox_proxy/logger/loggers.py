import logging
from xml_report import XmlReport


class TextLogger:
    def __init__(self, filename):
        """
        That's where we are writing.
        """
        self.log = logging.getLogger("LogServer")
        self.log.setLevel(logging.DEBUG)
        hdlr = logging.FileHandler(filename)
        self.log.addHandler(hdlr)

    def info(self, s):
        self.log.info(s)

    def debug(self, s):
        self.log.debug(s)

    def warning(self, s):
        self.log.warning(s)

    def error(self, s):
        self.log.error(s)

    def critical(self, s):
        self.log.critical(s)

    def log_event(self, conn_name, minfo):
        self.info(conn_name + ":\n" + str(minfo))
        
    def flush(self):
        pass
        

class XmlLogger:
    def __init__(self):
        self.conn_to_report = {}
        
    def log_event(self, conn_name, minfo):
        if conn_name not in self.conn_to_report:
            self.conn_to_report[conn_name] = XmlReport("event_logs/" + conn_name + ".xml", conn_name)
        self.conn_to_report[conn_name].add_event(minfo)
        
    def flush(self):
        for v in self.conn_to_report.values():
            v.flush()
            
