
"""
In charge of OpenFlow 1.0 switches.

NOTE: You should load this module first to avoid
loading standard openflow.of_01
"""
import inspect

from pox.openflow.of_01 import (Connection, of, core, deferredSender,
                                DeferredSender, log,
                                OpenFlow_01_Task)
import pox.core

from .proxy_controller import ProxyController


proxy = None


class ProxiedConnection (Connection):

    """
    Log sent messages to cli
    """

    def __init__(self, sock):
        super(ProxiedConnection, self).__init__(sock)
        global proxy
        self.proxy = proxy

    def __setattr__(self, name, value):
        """
        We proxify handlers.
        """
        self.__dict__[name] = value
        if name == "handlers":
            self.handlers[of.OFPT_FLOW_REMOVED] = decorate_flow_removed(
                self.handlers[of.OFPT_FLOW_REMOVED])

    def send(self, data):
        if isinstance(data, of.ofp_header):
            pass
        elif type(data) is bytes:
            ofp_type = ord(data[1])
            data = self.unpackers[ofp_type](data, 0)[1]
        else:
            super(ProxiedConnection, self).send(data)
            return

        if (of.ofp_type_map[data.header_type] == 'OFPT_FLOW_MOD'):
            data.flags |= of.OFPFF_SEND_FLOW_REM

            if data.match.is_exact and of.OFP_VERSION == 0x01:
                data.priority = 65535
            # HINT: Debuggers can modify the message
            super(ProxiedConnection, self).send(data)
            self.save_info(data)
        else:
            super(ProxiedConnection, self).send(data)

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


def decorate_flow_removed(func):
    """
    We must process FlowRemoveds first.
    But just once.
    """
    if func.func_name == 'proxy_wrapper':
        return func

    def proxy_wrapper(con, msg):
        if msg.reason == 0 or msg.reason == 1:  # timeouts
            con.proxy.process_flow_removed(con.dpid, msg)
        func(con, msg)
    return proxy_wrapper


class Proxied_OF_01_Task (OpenFlow_01_Task):
    """
    We change openflow.of_01.Connection to ProxiedConnection.
    Also we process OFPFT_FLOW_REMOVED first.
    """
    def __init__(self, port=6633, address='0.0.0.0', ssl_key=None,
                 ssl_cert=None, ssl_ca_cert=None, do_proxy=False, **kw):
        super(Proxied_OF_01_Task, self).__init__(port, address, ssl_key,
                                                 ssl_cert, ssl_ca_cert)
        self.do_proxy = do_proxy
        if do_proxy:
            self.proxy = ProxyController(**kw)
            core.addListener(pox.core.GoingDownEvent, self._handle_DownEvent)
            global proxy
            proxy = self.proxy
            pox.openflow.of_01.Connection = ProxiedConnection

    def _handle_DownEvent(self, event):
        if self.do_proxy:
            self.proxy.close()


def launch(port=6633, address="0.0.0.0", name=None,
           private_key=None, certificate=None, ca_cert=None,
           __INSTANCE__=None, **kw):
    """
    Start a proxied (!!!) listener for OpenFlow connections

    If you want to enable SSL, pass private_key/certificate/ca_cert in
    reasonable combinations and pointing to reasonable key/cert files.
    These have the same meanings as with Open vSwitch's old test controller,
    but they are more flexible (e.g., ca-cert can be skipped).
    """
    if name is None:
        basename = "of_01"
        counter = 1
        name = basename
    while core.hasComponent(name):
        counter += 1
        name = "%s-%s" % (basename, counter)

    if core.hasComponent(name):
        log.warn("of_01 '%s' already started", name)
        return None

    if not pox.openflow.of_01.deferredSender:
        pox.openflow.of_01.deferredSender = DeferredSender()

    if of._logger is None:
        of._logger = core.getLogger('libopenflow_01')

    l = Proxied_OF_01_Task(port=int(port), address=address,
                           ssl_key=private_key, ssl_cert=certificate,
                           ssl_ca_cert=ca_cert, do_proxy=True, **kw)
    core.register(name, l)
    return l
