import logging
import os
from xml_report import XmlReport

class TextLogger(object):
    def __init__(self, filename):
        """
        That's where we are writing.
        """
        self.log = logging.getLogger("EventLog")
        self.log.setLevel(logging.DEBUG)
        hdlr = logging.FileHandler(filename)
        self.log.addHandler(hdlr)
        self.filename = filename

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

    def flushs(self):
        return open(self.filename, "r").read()


class XmlLogger(object):
    def __init__(self, log_dir):
        self.conn_to_report = {}
        self.log_dir = log_dir

    def log_event(self, conn_name, minfo):
        if conn_name not in self.conn_to_report:
            self.conn_to_report[conn_name] = XmlReport(
                os.path.join(self.log_dir, conn_name + ".xml"), conn_name)
        self.conn_to_report[conn_name].add_event(minfo)

    def flush(self):
        for v in self.conn_to_report.values():
            v.flush()

    def flushs(self):
        return {conn_name: report.flushs() for
                conn_name, report in self.conn_to_report.items()}
