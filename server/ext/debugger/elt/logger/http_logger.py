import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
from multiprocessing import Process, Pipe
import functools
import os

from .loggers import BaseLogger
from .xml_report import *
from ..util import app_logging


log = app_logging.getLogger("WebSocket server")


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
        log.info(message)


def connection_ready(handlers, conn, fd, events):
    loop = tornado.ioloop.IOLoop.instance()
    if loop.ERROR & events != 0:
        loop.close()
        return
    messages = []
    try:
        while conn.poll() is True:
            messages.append(conn.recv())
    except:
        loop.close()
    for s in messages:
        for h in handlers:
            h.write_message(s)


def check_parent(parent):
    loop = tornado.ioloop.IOLoop.instance()
    try:
        os.kill(parent, 0)
    except:
        loop.close()
        log.debug("Parent dead. Terminating.")


def start_server(port, conn, parent):
    handlers = []
    application = tornado.web.Application([
        (r'/ws', WSHandler, {"instances": handlers})
    ])
    server = tornado.httpserver.HTTPServer(application)
    server.listen(port)
    loop = tornado.ioloop.IOLoop.instance()
    callback = functools.partial(connection_ready, handlers, conn)
    loop.add_handler(conn.fileno(), callback, loop.READ | loop.ERROR)
    tornado.ioloop.PeriodicCallback(functools.partial(check_parent, parent),
                                    1000, loop).start()
    try:
        loop.start()
    except:
        pass


class HttpLogger(BaseLogger):
    def __init__(self, port=8080):
        self.conn, child_conn = Pipe()
        self.child = Process(target=start_server, args=(port, child_conn, os.getpid()))
        self.port = port
        self.child.daemon = True
        self.child.start()
        child_conn.close()

    def __del__(self):
        self.child.terminate()

    def log_event(self, conn_name, minfo):
        report = XmlReport("", conn_name)
        report.add_event(minfo)
        s = report.flushs()
        self.conn.send(s)

    def flush(self):
        pass

    def flushs(self):
        pass
