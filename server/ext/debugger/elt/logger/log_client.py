import socket
import time
from ConfigParser import ConfigParser
import bz2
import os
import base64

from ..message_server import ClosingMessage
from ..interaction import Instantiator, ConnectionFactory
from ..util import app_logging

from .messages import HelloMessage, LogMessage, ReportQuery, ReportReply


PORT = 5523
ADDRESS = "0.0.0.0"
log = app_logging.getLogger('Log Client')
CONFIG = ["server/config/config.cfg", "config/config.cfg"]
LOG_DIR = "data/event_logs/"


class LogClient(object):
    """
    The only thing I can is sending errors to log.
    """
    def __init__(self, name="", connect=True):
        self.connection_factory = ConnectionFactory(
            instantiator=Instantiator(
                module="ext.debugger.elt.logger.messages"))

        self.port = PORT
        self.address = ADDRESS
        self.log_dir = LOG_DIR

        self.config = ConfigParser()
        log.info("Read config: %s" % (self.config.read(CONFIG)))
        if self.config.has_option("log_client", "port"):
            self.port = self.config.getint("log_client", "port")
        if self.config.has_option("log_client", "address"):
            self.address = self.config.get("log_client", "address")
        if self.config.has_option("log_client", "log_dir"):
            self.log_dir = self.config.get("log_client", "log_dir")

        self.name = name
        self.connection = None
        if connect:
            while self.reconnect() is False:
                time.sleep(0.1)

    @property
    def connected(self):
        return self.connection is not None

    def close(self):
        self.connection.send(ClosingMessage())
        self.connection.close()
        self.connection = None

    def log_event(self, event):
        """
        Send a message about event to Log Server.
        """
        if not self.connection:
            raise EOFError('LogClient: Connection closed')
        try:
            self.connection.send(LogMessage(event))
        except Exception as e:
            log.info('LogClient: Connection closed.' +
                     ' Try using self.reconnect()')

    def reconnect(self):
        """
        Try to reconnect to Log Server.
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.address, self.port))
            self.connection = self.connection_factory.create_connection(s)

            self.connection.send(HelloMessage(self.name))
            log.info('LogClient: Connection established.')
            return True
        except Exception as e:
            log.debug(str(e))
            log.info('LogClient: Unable to establish connection. ' +
                     'Try using self.reconnect()')
            return False

    def save_log(self):
        """
        Receive log file(-s) from Log Server.
        Save them to self.log_dir.
        """
        msg = self.get_log(fmt="bz2/base64")
        if isinstance(msg.report, dict):
            for k, v in msg.report.items():
                try:
                    open(os.path.join(self.log_dir, k), "w").write(
                        bz2.decompress(base64.decodestring(v)))
                except Exception as e:
                    log.warning("Unable to save log files:\n%s" % e)

    def get_log(self, fmt="bz2/base64"):
        """
        Receive log file(-s) from Log Server.
        Return ReportReply message.
        """
        self.connection.send(ReportQuery(fmt))
        msg = None
        while True:
            msg = self.connection.recv()
            if msg is not None:
                break
        if not isinstance(msg, ReportReply):
            raise Exception("Unexpected report reply")

        return msg
