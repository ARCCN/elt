import time

from pox.lib.recoco.recoco import Exit

from ..message_server import PythonMessageServer
from ..util import profile, app_logging
from ..interaction import Instantiator, ConnectionFactory
from ..database import DatabaseClient, QueryReply

from .util import FlowModInfo, RuleInfo, MessageInfo, ReQuery
from .messages import HelloMessage, LogMessage
from .loggers import TextLogger, XmlLogger

BUFFER_SIZE = 10
log = app_logging.getLogger('Log Server')


class LogServer(PythonMessageServer):
    """
    Writes error messages to log file.
    Uses DatabaseClient to retrieve FlowMod call stack.
    Uses asynchronious querying to save resources.
    """
    def __init__(self, port=5523, logger=None, log_file='LogServer.log'):
        self.db_client = DatabaseClient(mode='rw')
        if logger is None:
            #self.log = TextLogger(log_file)
            self.log = XmlLogger()
        else:
            self.log = logger
        self.names = {}
        self.pending = {} # mid -> (MessageInfo, conn_name)
        self.qid_mid = {}
        self.last_qid = 0
        self.last_mid = 0
        self.check_iter = 0
        self.generated = 0
        self.total_sent = 0
        self.empty_response = 0
        factory = ConnectionFactory(instantiator=Instantiator(
            module='ext.debugger.elt.logger.messages'))
        PythonMessageServer.__init__(self, port, enqueue=True,
                                     single_queue=True, cooldown=0.0,
                                     interval=1, connection_factory=factory)

    def close(self):
        while self.enqueue and self.check_waiting_messages() is True:
            pass
        for s in self.sockets:
            self.remove_connection(s)
        while self.db_client.connected and len(self.pending) > 0:
            self.check_pending()
        self.log.flush()
        self.closed = True
        self.flush_stats()
        Exit()

    def flush_stats(self):
        f = open('LogServer.stats', 'w')
        f.write('Generated %06d queries\n' % self.generated)
        f.write('Received  %06d empty responses\n' % self.empty_response)
        f.write('Sent      %06d messages totally' % (self.total_sent))
        f.close()

    #@profile
    def check_waiting_messages(self):
        """
        Every flushing we check our DBClient for responses.
        """
        result = False
        replies = 0
        try:
            if len(self.pending) > 0:
                replies = self.check_pending()
                result = True
        except:
            pass
        if self.single_queue:
            self.check_iter += 1
            pool = (len(self.queue) if len(self.queue) < BUFFER_SIZE
                    else BUFFER_SIZE)
            if self.check_iter % 100 == 0:
                log.info('Received %-8d Queue %-8d Pending %-8d' % (
                    self.received, len(self.queue), len(self.pending)))
            if pool == 0:
                if replies == 0:
                    time.sleep(0.01)
                return result
            for i in xrange(pool):
                message = self.queue.popleft()
                if isinstance(message, tuple):
                    msg, con = message
                    self.process_message(msg, con)
                elif isinstance(message, ReQuery):
                    self._send_queries([message])
            result = True
        return result

    def process_message(self, msg, con):
        """
        Substitute call stack in place of %CODE.
        We just send requests to Database and check replies some time.
        We use qid_mid to match response with request.
        At first we prepare everything to get reply. Finally, send messages.
        """
        try:
            if isinstance(msg, LogMessage):
                self.last_mid += 1
                args = msg.event.args()
                qids = []
                indices = []
                infos = []
                buffer = []
                #prepare everything for receiving reply
                for e, i in zip(args, msg.event.indices()):
                    type = e.name
                    entry = (e.dpid, e.data)
                    info = None
                    if type in ["FlowMod", "ofp_flow_mod"]:
                        info = FlowModInfo(entry)
                    elif type in ['Rule', 'rule', 'ofp_rule']:
                        info = RuleInfo(entry)
                    else:
                        raise TypeError('Invalid record type')
                    qid = self._get_qid()
                    qids.append(qid)
                    infos.append(info)
                    indices.append(i)
                    self.qid_mid[qid] = self.last_mid
                    buffer.append(ReQuery(info, qid))
                    self.generated += 1
                conn_name = self.names.get(con, str(con))
                minfo = MessageInfo(infos, qids, indices, msg.event)
                self.pending[self.last_mid] = (minfo, conn_name)
                #after all, send our queries
                self._send_queries(buffer)
            elif isinstance(msg, HelloMessage):
                self.names[con] = msg.name
            else:
                raise TypeError('Unsupported message type')
        except Exception as e:
            log.debug(str(e))

    def _log_message(self, mid):
        """
        Save to log and clear information.
        """
        minfo, conn_name = self.pending[mid]
        try:
            self.log.log_event(conn_name, minfo)
        except Exception as e:
            log.debug(str(e))
        del self.pending[mid]

    def _send_queries(self, buffer):
        for req in buffer:
            try:
                if isinstance(req.info, FlowModInfo):
                    self.db_client.find_flow_mod_async(
                        req.info.dpid, req.info.match, req.info.actions,
                        req.info.command, req.info.priority, req.qid)
                elif isinstance(req.info, RuleInfo):
                    self.db_client.find_rule_async(
                        req.info.dpid, req.info.match, req.info.actions,
                        req.info.priority, req.qid)
                else:
                    raise TypeError('Wrong info format')
                self.total_sent += 1
            except EOFError:
                self.db_client.reconnect()
            except Exception as e:
                log.debug(str(e))
                self.queue.appendleft(req)

    def _get_qid(self):
        self.last_qid += 1
        #if self.last_qid % 1000 == 0:
        #    print 'last_qid', self.last_qid
        return self.last_qid

    def check_pending(self):
        """
        Read replies. Fill call stack.
        If all the call stacks acquired, write to log file.
        If reply is empty, re-query.
        THIS CAN CAUSE DEADLOCK!
        Put a message to queue instead of re-querying.
        """
        ress = []
        try:
            ress = self.db_client.read_messages()
        except EOFError as e:
            log.debug(str(e))
            self.db_client.reconnect()
        except Exception as e:
            log.debug(str(e))
            return False
        for res in ress:
            if isinstance(res, QueryReply):
                code = res.code
                qid = res.qid
                #print qid
                mid = self.qid_mid.get(qid, None)
                if mid is not None and mid in self.pending:
                    found = False if len(
                            [value for type, value in code
                             if value == 'Not found']
                            ) > 0 else True
                    if not found:
                        minfo, conn_name = self.pending[mid]
                        if minfo.get_query_count(qid) <= 3:
                            new_qid = self._get_qid()
                            minfo.change_qid(qid, new_qid)
                            self.qid_mid[new_qid] = mid
                            self.queue.appendleft(ReQuery(
                                minfo.infos[new_qid], new_qid))
                            self.empty_response += 1
                            minfo.inc_query_count(new_qid)
                        else:
                            try:
                                minfo.set_code(qid, code)
                                if minfo.filled():
                                    self._log_message(mid)
                            except Exception as e:
                                log.debug(e)
                    else:
                        try:
                            self.pending[mid][0].set_code(qid, code)
                            if self.pending[mid][0].filled():
                                self._log_message(mid)
                        except Exception as e:
                            log.debug(e)
            elif res is None:
                pass
        return len(ress)
