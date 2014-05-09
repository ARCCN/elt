import socket
import time
from ConfigParser import ConfigParser

from ..message_server import ClosingMessage
from ..interaction import Instantiator, ConnectionFactory
from ..util import app_logging

from .messages import HelloMessage, LogMessage


PORT = 5523
log = app_logging.getLogger('Log Client')
CONFIG = ["server/config/config.cfg", "config/config.cfg"]


class LogClient(object):
    """
    The only thing I can is sending errors to log.
    """
    def __init__(self, name="", connect=True):
        self.connection_factory = ConnectionFactory(
            instantiator=Instantiator(
                module="ext.debugger.elt.logger.messages"))

        self.config = ConfigParser()
        log.info("Read config: %s" % (self.config.read(CONFIG)))
        port = PORT
        if self.config.has_option("log_client", "port"):
            port = self.config.getint("log_client", "port")

        self.port = port
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
        if not self.connection:
            raise EOFError('LogClient: Connection closed')
        try:
            self.connection.send(LogMessage(event))
        except Exception as e:
            log.info('LogClient: Connection closed.' +
                     ' Try using self.reconnect()')

    def reconnect(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('0.0.0.0', self.port))
            self.connection = self.connection_factory.create_connection(s)

            self.connection.send(HelloMessage(self.name))
            log.info('LogClient: Connection established.')
            return True
        except Exception as e:
            log.debug(str(e))
            log.info('LogClient: Unable to establish connection. ' +
                     'Try using self.reconnect()')
            return False
