import socket
import time

from ..competition_errors import *
from ..message_server import ClosingMessage
from ..interaction import Instantiator, ConnectionFactory
from ..util import app_logging

from .messages import HelloMessage, LogMessage


log = app_logging.getLogger('Log Client')


class LogClient:
    """
    The only thing I can is sending errors to log.
    """
    def __init__(self, port=5523, name=""):
        self.port = port
        self.name = name
        self.connection_factory = ConnectionFactory(
                    instantiator = Instantiator(
                        module="ext.debugger.pox_proxy.logger.messages"))

        self.connection = None
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
            log.info('LogClient: Connection closed. Try using self.reconnect()')

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


