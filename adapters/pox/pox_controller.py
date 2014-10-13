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


pox_popen = None
pox_lock = Lock()
from ext.debugger.elt.util import app_logging
log = app_logging.getLogger("PoxController")


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

    def on_close(self):
        log.info("HttpServer: client disconnected")
        if self.handlers is not None:
            self.handlers.remove(self)

    def check_origin(self, origin):
        return True

    def on_message(self, message):
        self.process_message(message)

    def process_message(self, message):
        global pox_lock
        if message.startswith("start_pox"):
            pox_lock.acquire()
            stop_pox()
            start_pox(message.replace("start_pox", "").strip())
            pox_lock.release()
        elif message.startswith("stop_pox"):
            pox_lock.acquire()
            stop_pox()
            pox_lock.release()
        elif (message.startswith("launch_single") or
                message.startswith("launch_hierarchical")):
            pox_lock.acquire()
            send_command(message)
            pox_lock.release()
        else:
            log.warning("Invalid message:\n%s" % message)


def start_pox(args):
    global pox_popen
    splitted = [x for x in args.split(' ') if x != ""]
    if ("debugger.component_launcher" not in splitted and
            "ext.debugger.component_launcher" not in splitted):
        splitted.append("debugger.component_launcher")
    if "py" not in splitted:
        splitted.insert(0, "py")
    if "log.level" not in splitted:
        splitted.insert(0, "log.level")
        splitted.insert(1, "--WARNING")
    #if "--no-openflow" not in splitted:
    #    splitted.insert(0, "--no-openflow")
    splitted.insert(0, os.path.join(os.getcwd(), "pox.py"))
    splitted.insert(0, "python")
    log.debug("%s" % splitted)
    try:
        pox_popen = Popen(splitted, stdin=PIPE, stdout=sys.stdout,
                          stderr=sys.stderr)
    except Exception as e:
        log.error(str(e))


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
    _, rlist, _ = select([], [pox_popen.stdin], [], 0)
    if len(rlist) > 0:
        log.debug("Sending command: \n%s" % message)
        pox_popen.stdin.write(message)
    else:
        log.warning("Cannot write to pox's stdin!")


def stop_pox():
    global pox_popen
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


def start_server(port):
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
