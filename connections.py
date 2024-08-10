import sys
from eprint import eprint
import socket
import struct

class Connection:
    def connect(self):
        return True

    def send(self, data):
        raise ConnectionError()

    def recv(self, size):
        raise ConnectionError()

    def close(self):
        pass

    def unpack(self, fmt):
        size = struct.calcsize(fmt)
        data = self.recv(size)
        values = struct.unpack(fmt, data)
        if len(values) == 1:
            values = values[0]
        return values

    def pack(self, fmt, *values):
        data = struct.pack(fmt, *values)
        self.send(data)


class StdioConnection(Connection):
    def send(self, data):
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()

    def recv(self, n):
        buff = bytearray(n)
        pos = 0
        while pos < n:
            cr = sys.stdin.buffer.readinto(memoryview(buff)[pos:])
            if cr == 0:
                raise ConnectionError()
            pos += cr
        return buff

    def close(self):
        sys.stdout.close()
        sys.stdin.close()

class TcpServer(Connection):
    def __init__(self, host = '0.0.0.0', port=50000):

        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error:
            raise Exception('Failed to create socket')

        self.s.bind((host, port))
        self.s.listen()
        self.conn = None
        self.port = self.s.getsockname()[1]

    def connect(self):
        self.conn, _ = self.s.accept()
        return True

    def recv(self, n):
        buff = bytearray(n)
        pos = 0
        while pos < n:
            cr = self.conn.recv_into(memoryview(buff)[pos:])
            if cr == 0:
                raise ConnectionError()
            pos += cr
        return buff

    def send(self, data):
        self.conn.sendall(data)

    def close(self):
        self.conn.close()

class TcpClientConnection(Connection):
    def __init__(self, host=None, port=50000):
        self.host = host
        self.port = port

    def connect(self):
        self.s = socket.socket()  # instantiate
        self.s.connect((self.host, self.port))  # connect to the server

        return True

    def send(self, data):
        self.s.sendall(data)

    def recv(self, n):
        buff = bytearray(n)
        pos = 0
        while pos < n:
            cr = self.s.recv_into(memoryview(buff)[pos:])
            if cr == 0:
                eprint("tcp client recv 0 error")
                raise ConnectionError()
            pos += cr
        return buff

    def close(self):
        self.conn.close()
class SubprocessConnection(Connection):
    def __init__(self, p):
        super(SubprocessConnection, self).__init__()
        self.p = p

    def send(self, data):
        l = self.p.stdin.write(data)
        if l != len(data):
            raise ConnectionError()
        self.p.stdin.flush()

    def recv(self, n):
        data = self.p.stdout.read(n)
        if len(data) != n:
            raise ConnectionError()
        return data
