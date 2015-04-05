import time
import socket
from ConfigParser import ConfigParser

import pox.openflow.libopenflow_01 as of

from ..message_server import Message, ClosingMessage
from ..interaction import (SimpleConnection, TimeoutException,
                           ConnectionFactory, Instantiator,
                           ofp_rule, ofp_flow_mod)
from ..util import app_logging, profile

from .messages import FlowModMessage, FlowModQuery, RuleQuery, QueryReply


# Client-server interaction defaults.
PORT = 5522
ADDRESS = "0.0.0.0"
#Logging
log = app_logging.getLogger("Database Client")
CONFIG = ["server/config/config.cfg", "config/config.cfg"]


class DatabaseClient(object):
    """
    Connects to Database. Supports flowmod addition and retrieving.
    Supports sync/async queries.
    """
    def __init__(self, mode='w', connect=True):
        self.connection_factory = ConnectionFactory(
            instantiator=Instantiator(
                module="ext.debugger.elt.database.messages"))

        self.port = PORT
        self.address = ADDRESS

        self.config = ConfigParser()
        log.info("Read config: %s" % (self.config.read(CONFIG)))
        if self.config.has_option("database_client", "port"):
            self.port = self.config.getint("database_client", "port")
        if self.config.has_option("database_client", "address"):
            self.address = self.config.get("database_client", "address")

        self.connection = None
        if connect:
            while self.reconnect() is False:
                time.sleep(0.1)
        if mode.find('w') != -1:
            self.writing = True
        else:
            self.writing = False

        if mode.find('r') != -1:
            self.reading = True
        else:
            self.reading = False

    @property
    def connected(self):
        return self.connection is not None

    def add_flow_mod(self, dpid, data, code_entries, cid=None):
        """
        Add FlowMod data to Database.
        """
        while True:
            try:
                self.send_message(FlowModMessage(dpid, data, code_entries, cid),
                                  async=True)
                break
            except TimeoutException:
                pass
            except:
                raise

    def close(self):
        """
        Send a message for server to shut down. Close connection.
        """
        self.connection.send(ClosingMessage())
        self.connection.close()
        self.connection = None

    def find_flow_mod(self, dpid, match, actions,
                      command, priority, cid=None):
        """
        Retrieve call stack for FlowMod.
        QID does not matter here.
        """
        fm = ofp_flow_mod(match=match, actions=actions,
                          command=command, priority=priority)
        return self.query(FlowModQuery(dpid, fm, cid))

    def find_rule(self, dpid, match, actions, priority):
        """
        Retrieve call stack(-s) for Rule.
        QID does not matter here.
        """
        rule = ofp_rule(match=match, actions=actions, priority=priority)
        return self.query(RuleQuery(dpid, rule))

    def query(self, msg, async=False):
        """
        Query the Database Server. Wait for response if not async.
        """
        if not self.connection:
            raise EOFError('DBClient: Connection closed')
        try:
            return self.send_message(msg, async=async)
        except TimeoutException as e:
            raise
        except:
            log.info('Connection closed. Try using db.reconnect()')
            self.connection.close()
            self.connection = None
            raise

    def find_flow_mod_async(self, dpid, match, actions,
                            command, priority, cid, qid):
        """
        Retrieve call stack for FlowMod.
        QID will be used to match request and response.
        """
        #Hack! We save on __init__ calls.
        fm = ofp_flow_mod(match=match, actions=actions,
                          command=command, priority=priority)
        return self.query(FlowModQuery(dpid, fm, cid, qid), async=True)

    def find_rule_async(self, dpid, match, actions,
                        priority, qid):
        """
        Retrieve call stack for FlowMod.
        QID will be used to match request and response.
        """
        rule = ofp_rule(match=match, actions=actions, priority=priority)
        return self.query(RuleQuery(dpid, rule, qid), async=True)

    def reconnect(self):
        """
        Try to reconnect to Database server.
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.address, self.port))
            self.connection = self.connection_factory.create_connection(s)
            log.info('DBClient: Connection established.')
            return True
        except Exception as e:
            log.debug(str(e))
            log.info('DBClient: Unable to establish connection. ' +
                     'Try using db.reconnect()')
            return False

    def send_message(self, msg, async=False):
        """
        If not async, wait for response.
        Otherwise, return immediately.
        """
        if not self.writing:
            return
        try:
            self.connection.send(msg)
            if self.reading and not async:
                obj = self.connection.recv()
                return obj
        except EOFError as e:
            log.debug(str(e))
            self.connection.close()
            self.connection = None
            raise
        except TimeoutException as e:
            raise

    def read_messages(self):
        """
        Read object from connection.
        Wait for timeout if not available.
        If timeout == 0, return immediately.
        If timeout is None, wait infinitely.
        """
        if self.connection is None:
            raise EOFError("Socket is closed")
        if not self.reading:
            return
        try:
            r = self.connection.recv_all()
            return r
        except Exception as e:
            log.debug(str(e))
            self.connection.close()
            self.connection = None
            raise

    def read_message(self, timeout=0):
        """
        Read available objects from connection.
        """
        if not self.reading or self.connection is None:
            return
        try:
            r = None
            if self.connection.readable(0):
                r = self.connection.recv()
            return r
        except Exception as e:
            log.debug(str(e))
            self.connection.close()
            self.connection = None
            raise
