import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
from multiprocessing import Process, Pipe
import functools

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
    messages = []
    try:
        while conn.poll() is True:
            messages.append(conn.recv())
    except:
        tornado.ioloop.IOLoop.instance().close()
    for s in messages:
        for h in self.handlers:
            h.write_message(s)


def start_server(port, conn):
    handlers = []
    application = tornado.web.Application([
        (r'/ws', WSHandler, {"instances": handlers})
    ])
    server = tornado.httpserver.HTTPServer(application)
    server.listen(port)
    loop = tornado.ioloop.IOLoop.instance()
    callback = functools.partial(connection_ready, handlers, conn)
    loop.add_handler(conn.fileno(), callback, loop.READ)
    loop.start()


class HttpLogger(BaseLogger):
    def __init__(self, port=8080):
        self.conn, child_conn = Pipe()
        self.child = Process(target=start_server, args=(port, child_conn))
        self.port = port
        self.child.start()

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
