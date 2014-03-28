import select
import cPickle
import json

from ..util import app_logging

from .instantiate import instantiate, Instantiator

#
# Support for using JSON for serialization
#


log = app_logging.getLogger('Connection')


def _get_dict(obj):
    if hasattr(obj, "__getstate__"):
        r = obj.__getstate__()
    else:
        r = obj.__dict__
    return r


class JSONPickler(object):
    def __init__(self, hook=instantiate):
        self.hook = hook

    def dumps(self, obj):
        return json.dumps(obj, separators=(',', ':'), default=_get_dict)

    def load(self, f):
        j = json.JSONDecoder(object_hook=self.hook)
        pos = f.tell()
        s = f.read()
        x, i = j.raw_decode(s)
        f.seek(i + pos)
        return x


def _json_dumps(obj):
    #return jsonpickle.encode(obj, unpicklable=False)
    return json.dumps(obj, separators=(',', ':'), default=_get_dict)


def _json_load(f):
    #print len(f)
    j = json.JSONDecoder(object_hook=instantiate)
    pos = f.tell()
    s = f.read()
    x, i = j.raw_decode(s)
    f.seek(i + pos)
    return x

#
# Support for using cPickle for serialization
#


def _cPickle_dumps(obj):
    return cPickle.dumps(obj, -1)


def _cPickle_loads(s):
    return cPickle.loads(s)


def _cPickle_load(f):
    return cPickle.load(f)

SEEK_START = 0
SEEK_CUR = 1
SEEK_END = 2
STRIP_LENGTH = 10000


import cStringIO


class ReadableBuffer1:
    """
    File-like interface for sequence.
    Supports state save/load (position only), read and append.
    Can strip first part by appending.
    Set frozen=True before using seek/tell.
    """
    def __init__(self, s=None):
        self.buf = cStringIO.StringIO()
        if s is not None:
            self.buf.write(s)
        self.buf.seek(0)
        self.spos = 0
        self._frozen = False

    def read(self, n=-1):
        return self.buf.read(n)

    def readline(self):
        return self.buf.readline()

    def append(self, s):
        x = self.buf.tell()
        self.buf.seek(0, SEEK_END)
        self.buf.write(s)
        self.buf.seek(x, SEEK_START)

        if not self._frozen and x > STRIP_LENGTH:
            self._strip_prefix()

    def _strip_prefix(self):
        s = self.buf.read()
        self.buf.close()
        self.buf = cStringIO.StringIO()
        self.buf.write(s)
        self.buf.seek(0)

    def savestate(self):
        self.spos = self.buf.tell()

    def loadstate(self):
        self.buf.seek(self.spos)

    def seek(self, pos, whence=SEEK_START):
        self.buf.seek(pos, whence)

    def tell(self):
        return self.buf.tell()

    @property
    def frozen(self):
        return self._frozen

    @frozen.setter
    def frozen(self, frozen):
        if isinstance(frozen, bool):
            self._frozen = frozen
            return
        raise TypeError('Frozen must be bool')

    def getvalue(self):
        return self.buf.getvalue()

    def __len__(self):
        c = self.buf.tell()
        self.buf.seek(0, SEEK_END)
        e = self.buf.tell()
        self.buf.seek(c, SEEK_START)
        return e - c


class ReadableBuffer:
    """
    File-like interface for sequence.
    Supports state save/load, read and append.
    Can strip first part by appending.
    Set frozen=True before using seek/tell.
    """
    def __init__(self, s=None):
        if s is None:
            self.buf = ""
        else:
            self.buf = s
        self.pos = 0
        self.sbuf = self.buf
        self.spos = self.pos
        self._frozen = False

    def readtail(self):
        s = self.buf[self.pos:]
        self.pos = len(self.buf)
        return s

    def read(self, n=-1):
        if n < 0:
            return self.readtail()
        else:
            s = self.buf[self.pos:self.pos + n]
            self.pos += len(s)
            return s

    def readline(self):
        n = self.buf.find('\n', self.pos)
        if n == -1:
            return self.readtail()
        else:
            s = self.buf[self.pos:n + 1]
            self.pos = n + 1
            return s

    def append(self, s):
        self.buf += s
        if not self._frozen and self.pos > STRIP_LENGTH:
            self.buf = self.buf[self.pos:]
            self.pos = 0

    def savestate(self):
        self.spos = self.pos
        self.sbuf = self.buf

    def loadstate(self):
        self.pos = self.spos
        self.buf = self.sbuf

    def seek(self, pos, whence=SEEK_START):
        seek_pos = 0
        if whence == SEEK_CUR:
            seek_pos = self.pos
        elif whence == SEEK_END:
            seek_pos = len(self.buf)

        pos = pos + seek_pos
        if pos < 0:
            self.pos = 0
        elif pos > len(self.buf):
            self.pos = len(self.buf)
        else:
            self.pos = pos

    def tell(self):
        return self.pos

    @property
    def frozen(self):
        return self._frozen

    @frozen.setter
    def frozen(self, frozen):
        if isinstance(frozen, bool):
            self._frozen = frozen
            return
        raise TypeError('Frozen must be bool')

    def getvalue(self):
        return self.buf

    def __len__(self):
        return len(self.buf) - self.pos


class TimeoutException(Exception):
    pass


class ConnectionFactory(object):
    def __init__(self, pickler=None, instantiator=None):
        if pickler is None:
            if instantiator is None:
                pickler = JSONPickler(hook=Instantiator())
            else:
                pickler = JSONPickler(hook=instantiator)
        self.pickler = pickler

    def create_connection(self, socket):
        return SimpleConnection(socket, load=self.pickler.load, dumps=self.pickler.dumps)


class SimpleConnection:
    """
    Wrapper for a socket.
    Supports asyncronious object send/recv with provided serializers.
    Reads all available data from socket and returns fully received objects.
    """
    def __init__(self, socket, load=_json_load, dumps=_json_dumps):
        self.socket = socket
        socket.setblocking(False)
        self.buffer = ReadableBuffer()
        self.dead = False
        self.load = load
        self.dumps = dumps

    def send(self, obj):
        if self.dead:
            raise EOFError('Socket is closed')
        d = None
        try:
            d = self.dumps(obj)
        except Exception as e:
            log.debug('%s on dump %s' % (e, obj))
            return
        try:
            r, w, e = select.select([], [self.socket], [], 1)
        except:
            self.dead = True
        if len(w) > 0:
            #print 'send', obj
            self.socket.sendall(d)
        else:
            log.info("Unable to send: select() timeout")
            raise TimeoutException()

    def recv(self):
        while True:
            r = []
            w = []
            e = []
            if not self.dead:
                try:
                    r, w, e = select.select([self.socket], [],
                                            [self.socket], 0.01)
                except Exception as e:
                    log.debug("%s" % e)
                    self.dead = True
                if len(r) > 0:
                    d = self.socket.recv(8192)
                    if len(d) == 0:
                        self.dead = True
                    self.buffer.append(d)
                if len(e) > 0:
                    self.dead = True
            self.buffer.savestate()
            obj = None
            try:
                obj = self.load(self.buffer)
            except:
                self.buffer.loadstate()
                if self.dead:
                    raise EOFError("Socket is closed")
                if len(r) == 0:
                    return None
            if obj is not None:
                return obj

    def recv_all(self):
        objs = []
        buffers = []
        while not self.dead:
            r = []
            w = []
            e = []
            try:
                r, w, e = select.select([self.socket], [], [self.socket], 0.0)
            except Exception as e:
                log.debug("%s" % e)
                self.dead = True
                break
            if len(e) > 0:
                self.dead = True
            if len(r) > 0:
                d = self.socket.recv(4096)
                if len(d) == 0:
                    self.dead = True
                buffers.append(d)
            else:
                break

        self.buffer.append("".join(buffers))
        while True:
            self.buffer.savestate()
            obj = None
            try:
                obj = self.load(self.buffer)
            except Exception as e:
                #log.debug(str(e) + self.buffer.getvalue())
                self.buffer.loadstate()
                if self.dead and len(objs) == 0:
                    raise EOFError("Socket is closed")
                else:
                    return objs
            if obj is not None:
                objs.append(obj)

    def close(self):
        self.socket.close()

    def readable(self, timeout):
        self.buffer.append("")
        if len(self.buffer) > 0:
            return True
        if len(select.select([self.socket], [], [], timeout)[0]) > 0:
            return True
        return False

    def writeable(self, timeout):
        if len(select.select([], [self.socket], [], timeout)[1]) > 0:
            return True
        return False

    def error(self, timeout):
        if len(select.select([], [], [self.socket], timeout)[2]) > 0:
            return True
        return False

    def fileno(self):
        return self.socket.fileno()
