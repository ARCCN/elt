import socket
import sys
from ConfigParser import ConfigParser

from ..message_server import Message, PythonMessageServer
from ..interaction import (SimpleConnection, TimeoutException,
                           ConnectionFactory, Instantiator)
from ..util import app_logging, profile

from .messages import FlowModMessage, FlowModQuery, RuleQuery, QueryReply
from .database import Database


BUFFER_SIZE = 5
STATUS_INTERVAL = 1000
PORT = 5522
CONFIG = ["server/config/config.cfg", "config/config.cfg"]
log = app_logging.getLogger("Database Server")


class DatabaseServer(PythonMessageServer):

    def __init__(self, **kw):
        """
        We want to wait 0.0s each turn.
        Every turn we process BUFFER_SIZE messages.
        """
        self.db = Database(**kw)
        self.check_iter = 0
        factory = ConnectionFactory(instantiator=Instantiator(
            module='ext.debugger.elt.database.messages'))
        self.config = ConfigParser()
        log.info("Read config: %s" % (self.config.read(CONFIG)))
        self.cooldown = 0.0
        self.interval = 1
        self.buffer_size = BUFFER_SIZE
        self.port = PORT
        self.status_interval = STATUS_INTERVAL
        if self.config.has_option("database_server", "cooldown"):
            self.cooldown = self.config.getfloat("database_server", "cooldown")
        if self.config.has_option("database_server", "interval"):
            self.interval = self.config.getint("database_server", "interval")
        if self.config.has_option("database_server", "buffer_size"):
            self.buffer_size = self.config.getint("database_server",
                                                  "buffer_size")
        if self.config.has_option("database_server", "port"):
            self.port = self.config.getint("database_server", "port")
        if self.config.has_option("database_server", "status_interval"):
            self.status_interval = self.config.getint("database_server",
                                                      "status_interval")

        PythonMessageServer.__init__(self, port=self.port, enqueue=True,
                                     single_queue=True, cooldown=self.cooldown,
                                     interval=self.interval,
                                     connection_factory=factory)

    def close(self):
        """
        We have to flush pending messages before closing.
        """
        while self.check_waiting_messages() is True:
            pass
        for s in self.sockets:
            self.remove_connection(s)
        self.db.disconnect()
        self.closed = True
        self.db.flush_stats()
        sys.exit(0)

    def check_waiting_messages(self):
        """
        Process up to BUFFER_SIZE messages.
        """
        if self.single_queue:
            if len(self.queue) == 0:
                return False
            pool = (len(self.queue) if len(self.queue) < self.buffer_size
                    else self.buffer_size)
            for i in xrange(pool):
                msg, con = self.queue.popleft()
                self.process_message(msg, con)
            self.check_iter += 1
            if self.check_iter % self.status_interval == 0:
                log.info('Received %-8d Queue %-8d' % (
                    self.received, len(self.queue)))
            return True

        try:
            con = self.current_client.next()
        except:
            self.current_client = self.get_client_queue()
            try:
                con = self.current_client.next()
            except:
                return

        if len(self.clients[con]) == 0:
            return
        pool = (len(self.clients[con]) if len(self.clients[con]) <
                self.buffer_size else self.buffer_size)
        queue = self.clients[con][:pool]
        self.clients[con] = self.clients[con][pool:]
        results = self.db.flush_buffer(queue)
        for r in results:
            con.send(r)
        return True

    def process_message(self, msg, con):
        """
        Feed message to Database and send response to client.
        """
        try:
            result = self.db.process_message(msg)
        except Exception as e:
            log.debug(str(e))
            return
        while True:
            try:
                if result is not None:
                    con.send(result)
                break
            except EOFError as e:
                self.remove_connection(con)
                break
            except TimeoutException:
                log.info('Unable to send. Retry')
        return True
