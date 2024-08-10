import win32file, win32con, win32pipe, winerror, pywintypes, win32security
from connections import Connection
from eprint import eprint


def get_security_attributes():
    security_attributes = pywintypes.SECURITY_ATTRIBUTES()
    security_attributes.SECURITY_DESCRIPTOR.SetSecurityDescriptorDacl(1, None, 0)
    return security_attributes


class NamedPipe(Connection):
    def send(self, data):
        pos = 0
        while pos != len(data):
            res, l = win32file.WriteFile(self.pipe, data[pos:])
            if res != 0:
                eprint("named pipe send error", res)
                self.pipe = None
                raise ConnectionError
            pos += l
            if pos != len(data):
                eprint("didnt send all bytes")

    def recv(self, size):
        try:
            result, data = win32file.ReadFile(self.pipe, size)
        except pywintypes.error as e:
            if e.winerror != winerror.ERROR_BROKEN_PIPE:
                eprint(e)
            self.pipe = None
            raise ConnectionError()

        if (result == 0 or result == winerror.ERROR_MORE_DATA) and len(data) == size:
            return data

        self.pipe = None
        eprint("named pipe recv error", result, len(data), size)
        print("ERROR_MORE_DATA=", winerror.ERROR_MORE_DATA)
        print("ERROR_IO_PENDING=", winerror.ERROR_IO_PENDING)
        raise ConnectionError()

    def close(self):
        win32file.CloseHandle(self.pipe)

class NamedPipeServer(NamedPipe):
    def __init__(self, name, full_access):
        self.name = name
        self.full_access = full_access
        self.create()

    def create(self):
        self.pipe = win32pipe.CreateNamedPipe(
        r'\\.\pipe\\' + self.name,
        win32pipe.PIPE_ACCESS_DUPLEX,
        win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
        1, 65536, 65536,
        0,
        get_security_attributes() if self.full_access else None)

    def connect(self):
        if self.pipe is None:
            self.create()
        res = win32pipe.ConnectNamedPipe(self.pipe, None)
        assert res == 0
        return True

class NamedPipeClient(NamedPipe):
    def __init__(self, name):
        self.name = name

    def connect(self):
        self.pipe = win32file.CreateFile(
            r'\\.\pipe\\' + self.name,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None
        )
        win32pipe.SetNamedPipeHandleState(self.pipe, win32pipe.PIPE_READMODE_MESSAGE, None, None)
        return True
