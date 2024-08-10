
from fusepy import FUSE, FuseOSError, Operations
import time
from stat import S_IFDIR, S_IFREG
from errno import ENOENT
import errno

class FS(Operations):
    def __init__(self, devices):
        self.fd = 0
        self.files = {}
        self.devices = devices
        now = time.time()
        self.files['/'] = dict(
            st_mode=(S_IFDIR | 0o755),
            st_ctime=now,
            st_mtime=now,
            st_atime=now,
            st_nlink=2)
        for name, device in self.devices.items():
            self.files['/' + name] = dict(
                st_mode=(S_IFREG | 0o755),
                st_ctime=now,
                st_mtime=now,
                st_atime=now,
                st_nlink=2,
                st_size=device.size)

    def open(self, path, flags):
        if path[0] == "/" and path[1:] in self.devices:
            self.fd += 1
            return self.fd
        else:
            return -1

    def read(self, path, length, offset, fh):
        if path[0] == "/" and path[1:] in self.devices:
            device = self.devices[path[1:]]
            data = device.read(offset, length)

            assert len(data) == length
            return bytes(data)
        return b''

    def write(self, path, buf, offset, fh):
        if path[0] == "/" and path[1:] in self.devices:
            device = self.devices[path[1:]]
            if device.write(offset, buf):
                return len(buf)
            else:
                print("write failed")
                return -errno.EACCES
        else:
            return -1

    def readdir(self, path, fh):
        for d in self.devices.keys():
            yield d

    def getattr(self, path, fh=None):
        if path not in self.files:
            raise FuseOSError(ENOENT)

        return self.files[path]