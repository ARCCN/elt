
"""
In charge of OpenFlow 1.0 switches.

NOTE: You should load this module first to avoid
loading standard openflow.of_01
"""
import inspect
import time
import sys
import socket
from errno import ECONNRESET
import exceptions

from pox.openflow.of_01 import (unpackers, Connection, of, core, handlers,
                                wrap_socket, log, OpenFlow_01_Task, Select)
import pox.core
import pox.openflow.debug

from ..util import profile

from .proxy_controller import ProxyController


class ProxiedConnection (Connection):

    """
    Log sent messages to cli
    """

    def __init__(self, sock, proxy):
        super(ProxiedConnection, self).__init__(sock)
        self.msg_id = 0
        self.proxy = proxy

    #@profile
    def send(self, data):
        if isinstance(data, of.ofp_header):
            pass
        elif type(data) is bytes:
            ofp_type = ord(data[1])
            data = unpackers[ofp_type](data, 0)[1]
        else:
            super(ProxiedConnection, self).send(data)
            return

        if (of.ofp_type_map[data.header_type] == 'OFPT_FLOW_MOD'):
            if data.match.is_exact:
                data.priority = 65535
            self.save_info(data)
            # HINT: Debuggers can modify the message
        super(ProxiedConnection, self).send(data)

    def read(self):
        """
        Read data from this connection.  Generally this is just called by the
        main OpenFlow loop below.

        Note: This function will block if data is not available.
        """
        d = self.sock.recv(2048)
        if len(d) == 0:
            return False
        self.buf += d
        buf_len = len(self.buf)

        offset = 0
        while buf_len - offset >= 8:  # 8 bytes is minimum OF message size
            # We pull the first four bytes of the OpenFlow header off by hand
            # (using ord) to find the version/length/type so that we can
            # correctly call libopenflow to unpack it.

            ofp_type = ord(self.buf[offset + 1])

            if ord(self.buf[offset]) != of.OFP_VERSION:
                if ofp_type == of.OFPT_HELLO:
                    # We let this through and hope the other side switches
                    # down.
                    pass
                else:
                    log.warning("Bad OpenFlow version (0x%02x) \
                                 on connection %s"
                                % (ord(self.buf[offset]), self))
                    return False  # Throw connection away

            msg_length = ord(self.buf[offset + 2]
                             ) << 8 | ord(self.buf[offset + 3])

            if buf_len - offset < msg_length:
                break

            new_offset, msg = unpackers[ofp_type](self.buf, offset)
            assert new_offset - offset == msg_length
            offset = new_offset

            try:
                h = handlers[ofp_type]
                if (of.ofp_type_map[ofp_type] == 'OFPT_FLOW_REMOVED' and
                        (msg.reason == 0 or msg.reason == 1)):  # timeouts
                    self.proxy.process_flow_removed(self.dpid, msg)
                h(self, msg)
            except:
                log.exception("%s: Exception while handling \
                               OpenFlow message:\n" +
                              "%s %s", self, self,
                              ("\n" + str(self) + " ").
                              join(str(msg).split('\n')))
                continue

        if offset != 0:
            self.buf = self.buf[offset:]

        return True

    def save_info(self, data):
        #~1 ms without querying database

        #~0.8 ms
        stack = inspect.stack(context=0)

        # Get innermost frame
        inner = (3 if stack[2][3] == 'sendToDPID' else 2)

        # We dont need to go deeper
        stop_functions = ['read', 'run', 'execute']

        code_entries = []

        for i in range(inner, len(stack)):
            if stack[i][3] in stop_functions:
                break
            # TODO: Maybe copy string?
            code_entries.append((stack[i][1], stack[i][2]))

        if of.ofp_type_map[data.header_type] == 'OFPT_FLOW_MOD':
            # Save info to DB
            # Strip off payload
            payload = data.data
            data.data = None
            self.proxy.add_flow_mod(self.dpid, data, code_entries)
            data.data = payload


class Proxied_OF_01_Task (OpenFlow_01_Task):

    def __init__(self, port=6633, address='0.0.0.0', do_proxy=False, **kw):
        super(Proxied_OF_01_Task, self).__init__(port, address)
        self.do_proxy = do_proxy
        if do_proxy:
            self.proxy = ProxyController(**kw)
            core.addListener(pox.core.GoingDownEvent, self._handle_DownEvent)

    def _handle_DownEvent(self, event):
        self.proxy.close()

    def run(self):
        # List of open sockets/connections to select on
        sockets = []

        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((self.address, self.port))
        listener.listen(16)
        sockets.append(listener)

        log.debug("Listening on %s:%s" %
                  (self.address, self.port))

        if self.do_proxy:
            log.info("Running proxied version of OpenFlow_01_Task")

        con = None
        while core.running:
            try:
                while True:
                    con = None
                    rlist, wlist, elist = yield Select(sockets, [],
                                                       sockets, 5)
                    if (len(rlist) == 0 and len(wlist) == 0 and
                            len(elist) == 0):
                        if not core.running:
                            break

                    for con in elist:
                        if con is listener:
                            raise RuntimeError("Error on listener socket")
                        else:
                            try:
                                con.close()
                            except:
                                pass
                            try:
                                sockets.remove(con)
                            except:
                                pass

                    timestamp = time.time()
                    for con in rlist:
                        if con is listener:
                            new_sock = listener.accept()[0]
                            if pox.openflow.debug.pcap_traces:
                                new_sock = wrap_socket(new_sock)
                            new_sock.setblocking(0)
                            # Note that instantiating a Connection
                            # object fires a
                            # ConnectionUp event (after negotation has
                            # completed)
                            if self.do_proxy:
                                newcon = ProxiedConnection(
                                    new_sock, self.proxy)
                            else:
                                newcon = Connection(new_sock)
                            sockets.append(newcon)
                            # print str(newcon) + " connected"
                        else:
                            con.idle_time = timestamp
                            if con.read() is False:
                                con.close()
                                sockets.remove(con)
            except exceptions.KeyboardInterrupt:
                break
            except:
                doTraceback = True
                if sys.exc_info()[0] is socket.error:
                    if sys.exc_info()[1][0] == ECONNRESET:
                        con.info("Connection reset")
                        doTraceback = False

                if doTraceback:
                    log.exception("Exception reading connection " + str(con))

                if con is listener:
                    log.error("Exception on OpenFlow listener.  Aborting.")
                    break
                try:
                    con.close()
                except:
                    pass
                try:
                    sockets.remove(con)
                except:
                    pass

        log.debug("No longer listening for connections")


def launch(port=6633, address="0.0.0.0", **kw):
    if core.hasComponent('of_01'):
        return None
    l = Proxied_OF_01_Task(
        port=int(port), address=address, do_proxy=True, **kw)
    core.register("of_01", l)
    return l
