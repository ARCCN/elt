import sys
import exceptions
import socket
import select
import time
from collections import deque

from ..interaction import SimpleConnection, ConnectionFactory
from ..util import app_logging, profile

from .messages import Message, ClosingMessage


INTERVAL = 1
COOLDOWN = 0.01
log = app_logging.getLogger("Message Server")


class PythonMessageServer(object):
    """
    Base class for our servers.
    Supports queues/immediate processing.
    Supports single/per-client queue.
    Cooldown is used as select timeout.
    Process enqueued messages every interval reading cycles.
    """
    def __init__(self, port, enqueue=True, single_queue=True,
                 interval=INTERVAL, cooldown=COOLDOWN,
                 connection_factory=None):
        self.clients = {}
        self.port = port
        self._closing = False
        self.queue = deque()
        self.current_client = None
        self.closed = False
        self.enqueue = enqueue
        self.single_queue = single_queue
        self.received = 0
        self.cooldown = cooldown
        self.interval = interval
        if connection_factory is None:
            connection_factory = ConnectionFactory()
        self.connection_factory = connection_factory
        self.run()

    def dummy_select(self, r, w, e, cooldown):
        cd = 1.0 * cooldown / (len(r) + len(w) + len(e))
        rd = []
        wr = []
        er = []
        for x in r:
            if x is self.listener:
                rd.extend(select.select([x], [], [], cd)[0])
            elif x.readable(cd):
                rd.append(x)

        for x in w:
            if x is self.listener:
                wr.extend(select.select([], [x], [], cd)[1])
            elif x.writeable(cd):
                wr.append(x)

        for x in e:
            if x is self.listener:
                er.extend(select.select([], [], [x], cd)[2])
            elif x.error(cd):
                er.append(x)
        return (rd, wr, er)

    def run(self):
        self.sockets = []
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener = listener
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(('0.0.0.0', self.port))
        listener.listen(1000)
        self.sockets.append(listener)
        log.info('Running at 0.0.0.0 :%d' % self.port)
        iteration = 0
        while True:
            try:
                while True:
                    to_sleep = False
                    con = None
                    try:
                        rlist, wlist, elist = self.dummy_select(
                            self.sockets, [], self.sockets, self.cooldown)
                    except Exception as e:
                        log.debug(str(e))
                    if len(rlist) + len(wlist) + len(elist) == 0:
                        to_sleep = True
                    for con in elist:
                        if con is listener:
                            raise RuntimeError("Error on listener socket")
                        else:
                            try:
                                self.remove_connection(con)
                            except Exception as e:
                                log.debug(str(e))

                    for con in rlist:
                        if con is listener:
                            new_sock = listener.accept()[0]
                            try:
                                self.add_connection(new_sock)
                            except:
                                pass

                        else:
                            try:
                                connection = con
                                objs = connection.recv_all()
                                for obj in objs:
                                    if obj is None:
                                        continue
                                    self.process_object(obj, con)
                            except EOFError:
                                try:
                                    log.info('EOF %s' % str(con))
                                    self.remove_connection(con)
                                except:
                                    pass
                            except Exception as e:
                                log.debug(str(e))

                    if self.enqueue:
                        iteration += 1
                        if iteration % (self.interval) == 0:
                            try:
                                if (self.check_waiting_messages() is False and
                                        to_sleep):
                                    time.sleep(0.01)
                            except Exception as e:
                                log.debug(str(e))

                    if self._closing:
                        raise Exception('Closing')

            except exceptions.KeyboardInterrupt:
                break
            except Exception as e:
                log.debug(str(e))
                if self._closing:
                    self.close()
                    break

                if con is listener:
                    log.error('Error on listener')
                    break
                try:
                    self.remove_connection(con)
                except Exception as e:
                    log.debug(str(e))

    def remove_connection(self, con):
        try:
            self.sockets.remove(con)
            con.close()
        except:
            pass

    def add_connection(self, skt):
        c = self.connection_factory.create_connection(skt)
        self.sockets.append(c)
        self.clients[c] = []

    def close(self):
        """
        Flush pending messages before closing.
        """
        while self.enqueue and self.check_waiting_messages() is True:
            pass
        for s in self.sockets:
            self.remove_connection(s)
        self.closed = True
        sys.exit(0)

    def get_client_queue(self):
        """
        In per-client queues, get next queue to be flushed.
        """
        for con in self.clients.keys():
            if len(self.clients[con]) > 0:
                yield con
            elif con not in self.sockets:
                del self.clients[con]

    def check_waiting_messages(self):
        return True

    def process_message(self, msg, con):
        pass

    def process_object(self, obj, con):
        """
        Called on receiving an object.
        """
        self.received += 1
        if not isinstance(obj, Message):
            raise TypeError('obj is not Message')
        if isinstance(obj, ClosingMessage):
            self._closing = True
            log.info('Closing')
            return
        if self.enqueue:
            if self.single_queue:
                self.queue.append((obj, con))
            else:
                self.clients[con].append(obj)
        else:
            self.process_message(obj, con)
