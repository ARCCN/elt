import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web

from .loggers import BaseLogger
from .xml_report import *


class WSHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        self.handlers = kwargs.get("instances")
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
        pass


class HttpLogger(BaseLogger):
    def __init__(self, port=8080):
        self.port = port
        self.handlers = []
        self.application = tornado.web.Application([
            (r'ws', WSHandler, {"instances": self.handlers})
        ])
        self.server = tornado.httpserver.HTTPServer(self.application)
        self.run()

    def run(self):
        self.server.listen(self.port)
        tornado.ioloop.IOLoop.instance().start()

    def log_event(self, conn_name, minfo):
        report = XmlReport("", conn_name)
        report.add_event(minfo)
        s = report.flushs()
        for h in self.handlers:
            h.write_message(s)

    def flush(self):
        pass

    def flushs(self):
        pass





