from ..message_server import Message, ClosingMessage
from ..interaction import instantiate
from ..network_error import NetworkError


class HelloMessage(Message):
    """
    Let's name ourselves!
    """
    def __init__(self, name=""):
        Message.__init__(self)
        self.name = name

    def __setstate__(self, d):
        if "name" in d:
            self.name = d["name"]


class LogMessage(Message):
    """
    Error to be saved to log.
    """
    def __init__(self, event=None):
        Message.__init__(self)
        self.event = event

    def __setstate__(self, d):
        if "event" in d:
            self.event = d["event"]
            if isinstance(self.event, dict):
                self.event = NetworkError()
                self.event.__setstate__(d["event"])


class ReportQuery(Message):
    """
    Request log files encoded into specific format.
    """
    def __init__(self, fmt="pure"):
        Message.__init__(self)
        self.fmt = fmt

    def __setstate__(self, d):
        if "fmt" in d:
            self.fmt = d["fmt"]


class ReportReply(Message):
    """
    Return log files encoded into specific format.
    """
    def __init__(self, report=None, fmt="pure"):
        Message.__init__(self)
        self.fmt = fmt
        self.report = report

    def __setstate__(self, d):
        if "fmt" in d:
            self.fmt = d["fmt"]
        if "report" in d:
            self.report = d["report"]