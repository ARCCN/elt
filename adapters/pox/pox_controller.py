#!/usr/bin/python

from __future__ import print_function

import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
from subprocess import Popen, PIPE
import functools
from threading import Lock
import time
import sys
import os
from select import select
from ConfigParser import ConfigParser

from controller_messages import *


pox_popen = None
pox_lock = Lock()
from ext.debugger.elt.util import app_logging
log = app_logging.getLogger("PoxController")
handlers = []
launched = []


# TODO: Get launched modules. Useful when connecting while pox is running.


class WSHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        self.handlers = None
        try:
            self.handlers = kwargs["instances"]
            del kwargs["instances"]
        except:
            pass
        tornado.websocket.WebSocketHandler.__init__(self, application,
                                                    request, **kwargs)

    def open(self):
        log.info("HttpServer: client connected")
        if self.handlers is not None:
            self.handlers.append(self)
        global pox_popen
        if pox_popen is None:
            self.write_message(ControllerStatus("stopped").dumps())
        else:
            self.write_message(ControllerStatus("running").dumps())

    def on_close(self):
        log.info("HttpServer: client disconnected")
        if self.handlers is not None:
            self.handlers.remove(self)

    def check_origin(self, origin):
        return True

    def on_message(self, str_message):
        message = load_message(str_message)
        if not isinstance(message, ControllerMessage):
            return
        self.process_message(message)

    def process_message(self, message):
        global pox_lock
        if isinstance(message, StartController):
            pox_lock.acquire()
            stop_pox()
            start_pox(message.args.strip())
            pox_lock.release()
            if pox_popen is None:
                send_all(ControllerStatus("stopped").dumps())
            else:
                send_all(ControllerStatus("running").dumps())
        elif isinstance(message, StopController):
            pox_lock.acquire()
            stop_pox()
            pox_lock.release()
            if pox_popen is None:
                send_all(ControllerStatus("stopped").dumps())
            else:
                send_all(ControllerStatus("running").dumps())
        elif isinstance(message, LaunchComponent):
            output_ready(None, None)
            pox_lock.acquire()
            send_command(str(message))
            pox_lock.release()
        elif isinstance(message, GetControllerComponents):
            cc = get_controller_components()
            self.write_message(cc.dumps())
            # TODO: Maybe send launched by request-response?
            for c in launched:
                self.write_message(ComponentLaunched(c).dumps())
        else:
            log.warning("Invalid message:\n%s" % message)


def output_ready(fd, events):
    while True:
        try:
            rlist, _, _ = select([pox_popen.stdout], [], [], 0)
            if len(rlist) > 0:
                line = pox_popen.stdout.readline()
                line = line.replace("POX>", "").strip()
                print(line)
                if (line.startswith("Launching ") or
                        line.startswith("Launched ")):
                    line = (line.replace("Launching ", "").
                                 replace("Launched ", ""))
                    launched.append(line)
                    # We notify everyone.
                    send_all(ComponentLaunched(line).dumps())
            else:
                break
        except Exception as e:
            log.debug(str(e))
            break


def start_pox(args):
    global pox_popen, launched
    splitted = [x for x in args.split(' ') if x != ""]
    if ("debugger.component_launcher" not in splitted and
            "ext.debugger.component_launcher" not in splitted):
        splitted.append("debugger.component_launcher")
    if "py" not in splitted:
        splitted.insert(0, "py")
    if "log.level" not in splitted:
        splitted.insert(0, "log.level")
        splitted.insert(1, "--WARNING")
    if "--no-openflow" not in splitted:
        splitted.insert(0, "--no-openflow")
    splitted.insert(0, os.path.join(os.getcwd(), "pox.py"))
    splitted.insert(0, "python")
    log.debug("%s" % splitted)
    try:
        launched = []
        pox_popen = Popen(splitted, bufsize=0, stdin=PIPE,
                          stdout=PIPE, stderr=sys.stderr)
        loop = tornado.ioloop.IOLoop.instance()
        loop.add_handler(pox_popen.stdout.fileno(), output_ready, loop.READ)
        return True
    except Exception as e:
        log.error(str(e))
        return False


def send_command(message):
    global pox_popen
    if pox_popen is None:
        log.warning("Launching modules while pox is turned off.")
        return
    parts = [x for x in message.split(" ") if not x.isspace()]
    if len(parts) <= 1:
        log.debug("Command to short")
        return
    message = ("core.ComponentLauncher." + parts[0] +
               "([\"" + "\", \"".join(parts[1:]) + "\"])\n")
    _, wlist, _ = select([], [pox_popen.stdin], [], 0)
    if len(wlist) > 0:
        log.debug("Sending command: \n%s" % message)
        pox_popen.stdin.write(message)
    else:
        log.warning("Cannot write to pox's stdin!")


def stop_pox():
    global pox_popen, launched
    if pox_popen is not None:
        pox_popen.stdin.close()
        for i in xrange(5):
            if pox_popen.poll() is None:
                time.sleep(0.1)
        if pox_popen.poll() is None:
            pox_popen.terminate()
            time.sleep(0.1)
        if pox_popen.poll() is None:
            pox_popen.kill()
        pox_popen = None
        launched = []


class CaseConfigParser(ConfigParser):
    def __init__(self, allow_no_value=False):
        ConfigParser.__init__(self, allow_no_value=allow_no_value)
        self.optionxform = str


def get_controller_components():
    # TODO: Maybe move to separate file (e.g. ext/debugger/component_launcher)?
    # TODO: More intelligent lookup.
    CONFIG = ["debugger/component_launcher/component_config/",
          "ext/debugger/component_launcher/component_config/",
          "pox/ext/debugger/component_launcher/component_config/",
          "adapters/pox/ext/debugger/component_launcher/component_config/"]
    config = {}
    def _raise(x):
        raise x

    for directory in CONFIG:
        try:
            for dirname, dirnames, filenames in os.walk(
                    directory, onerror=_raise):
                del dirnames[:]
                for filename in filenames:
                    if not filename.endswith(".cfg"):
                        continue
                    cp = CaseConfigParser(allow_no_value=True)
                    log.info("Read config: %s" %
                             cp.read(os.path.join(dirname, filename)))
                    config[filename.replace(".cfg", "")] = cp
        except Exception as e:
            log.debug(str(e))
    cc = ControllerComponents()
    for component, cfg in config.items():
        params = []
        for k, v in cfg.defaults().items():
            if v is None:
                params.append(ComponentParam(k))
            else:
                params.append(ComponentParam(k, True, v))
        c = Component(component, params)
        cc.add_component(c)
    return cc


def send_all(message):
    for h in handlers:
        h.write_message(message)


def start_server(port):
    global handlers
    handlers = []
    application = tornado.web.Application([
        (r'/ws', WSHandler, {"instances": handlers})
    ])
    server = tornado.httpserver.HTTPServer(application)
    server.listen(port)
    try:
        loop = tornado.ioloop.IOLoop.instance()
        loop.start()
    except KeyboardInterrupt:
        stop_pox()

if __name__ == "__main__":
    start_server(8081)
