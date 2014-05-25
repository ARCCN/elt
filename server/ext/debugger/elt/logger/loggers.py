import logging
import os
from xml_report import XmlReport


class TextLogger(object):
    """
    Error report with simple text.
    """
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
        return {self.filename, open(self.filename, "r").read()}


class XmlLogger(object):
    """
    Error reports as XML.
    Separate file for each message source.
    """
    def __init__(self, log_dir):
        self.conn_to_report = {}
        self.log_dir = log_dir

    def log_event(self, conn_name, minfo):
        """
        Save a message to appropriate file.
        It won't be really saved until flush().
        """
        if conn_name not in self.conn_to_report:
            self.conn_to_report[conn_name] = XmlReport(
                os.path.join(self.log_dir, conn_name + ".xml"), conn_name)
        self.conn_to_report[conn_name].add_event(minfo)

    def flush(self):
        """
        Flush log files to disk.
        """
        for v in self.conn_to_report.values():
            v.flush()

    def flushs(self):
        """
        Flush log files to dict: {filename: report_as_string}
        """
        return {conn_name + ".xml": report.flushs() for
                conn_name, report in self.conn_to_report.items()}
