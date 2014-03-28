import socket

from pox.lib.recoco.recoco import Exit

from ..message_server import Message, PythonMessageServer
from ..interaction import (SimpleConnection, TimeoutException,
                           ConnectionFactory, Instantiator)
from ..util import app_logging, profile

from .messages import FlowModMessage, FlowModQuery, RuleQuery, QueryReply
from .database import Database


BUFFER_SIZE = 1
PORT = 5522
#Logging
log = app_logging.getLogger("Database Server")


class DatabaseServer(PythonMessageServer):

    def __init__(self, port=PORT, **kw):
        """
        We need want to wait 0.001s each turn.
        Every 20th turn we process BUFFER_SIZE messages.
        """
        self.db = Database(**kw)
        self.check_iter = 0
        factory = ConnectionFactory(instantiator=Instantiator(
            module='ext.debugger.pox_proxy.database.messages'))
        PythonMessageServer.__init__(self, port=port, enqueue=True,
                                     single_queue=True, cooldown=0.0,
                                     interval=1, connection_factory=factory)

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
        Exit()

    def check_waiting_messages(self):
        """
        Process up to BUFFER_SIZE messages.
        """
        if self.single_queue:
            if len(self.queue) == 0:
                return False
            pool = (len(self.queue) if len(self.queue) < BUFFER_SIZE
                    else BUFFER_SIZE)
            for i in xrange(pool):
                msg, con = self.queue.popleft()
                self.process_message(msg, con)
            self.check_iter += 1
            if self.check_iter % 1000 == 0:
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
        pool = (len(self.clients[con]) if len(self.clients[con]) < BUFFER_SIZE
                else BUFFER_SIZE)
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


