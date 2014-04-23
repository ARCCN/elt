
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


proxy = None


class ProxiedConnection (Connection):

    """
    Log sent messages to cli
    """

    def __init__(self, sock):  # , proxy):
        super(ProxiedConnection, self).__init__(sock)
        global proxy
        self.proxy = proxy

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
    def __init__(self, port=6633, address='0.0.0.0', do_proxy=False, **kw):
        super(Proxied_OF_01_Task, self).__init__(port, address)
        self.do_proxy = do_proxy
        if do_proxy:
            self.proxy = ProxyController(**kw)
            core.addListener(pox.core.GoingDownEvent, self._handle_DownEvent)
            handlers[of.OFPT_FLOW_REMOVED] = decorate_flow_removed(
                handlers[of.OFPT_FLOW_REMOVED])
            global proxy
            proxy = self.proxy
            pox.openflow.of_01.Connection = ProxiedConnection

    def _handle_DownEvent(self, event):
        if self.do_proxy:
            self.proxy.close()


def launch(port=6633, address="0.0.0.0", **kw):
    if core.hasComponent('of_01'):
        return None
    l = Proxied_OF_01_Task(
        port=int(port), address=address, do_proxy=True, **kw)
    core.register("of_01", l)
    return l
