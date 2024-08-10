import win32con, win32file, winioctlcon, pywintypes
from eprint import eprint
import struct

class Device:
    def __init__(self, devicename):
        self.devicename = devicename
        self.handle = None

    def open(self):
        self.handle = win32file.CreateFile(
            self.devicename,
            win32con.MAXIMUM_ALLOWED,
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
            None,
            win32con.OPEN_EXISTING,
            win32con.FILE_ATTRIBUTE_NORMAL,
            #win32con.FILE_FLAG_NO_BUFFERING | win32con.FILE_FLAG_WRITE_THROUGH,
            None
        )

        if self.handle == win32file.INVALID_HANDLE_VALUE:
            eprint("Failed to obtain device handle...")
            return False

        self.sector_size = self.get_geometry()['BytesPerSector']
        self.size = self.get_size()

        return True

    def close(self):
        if self.handle is not None:
            win32file.CloseHandle(self.handle)
            self.handle = None

    def get_geometry(self):
        # type: () -> tuple[int, ...]
        """
        Retrieves information about the physical disk's geometry.
        https://learn.microsoft.com/en-us/windows/win32/api/winioctl/ns-winioctl-disk_geometry_ex

        Returns a tuple of:
            Cylinders-Lo
            Cylinders-Hi
            Media Type
            Tracks Per Cylinder
            Sectors Per Track
            Bytes Per Sector
            Disk Size
            Extra Data
        """
        res = struct.unpack("QLLLLQb", win32file.DeviceIoControl(
            self.handle,  # handle
            winioctlcon.IOCTL_DISK_GET_DRIVE_GEOMETRY_EX,  # ioctl api
            b"",  # in buffer
            33  # out buffer
        ))
        return dict(zip(["Cylinders", "MediaType", "TracksPerCylinder", "SectorsPerTrack", "BytesPerSector", "DiskSize", "ExtraData"], res))

    def get_size(self):
        iRes = win32file.DeviceIoControl(
            self.handle,
            winioctlcon.IOCTL_DISK_GET_LENGTH_INFO,
            None,
            8)
        return int.from_bytes(iRes, 'little')

    def read(self, pos, size):
        offset = pos % self.sector_size
        pos -= offset
        extra = (self.sector_size - (size + offset)) % self.sector_size
        total_size = size + offset + extra

        win32file.SetFilePointer(self.handle, pos, win32file.FILE_BEGIN)
        try:
            res, data = win32file.ReadFile(self.handle, total_size, None)
        except pywintypes.error as e:
            eprint(e)
            return None

        if res != 0:
            eprint(f"An error occurred: {res} {data}")
            return None

        if len(data) != total_size:
            eprint(f"Read {total_size - len(data)} less bytes than requested...")
            return None
        return data[offset:offset + size]

    def write(self, pos, data):
        offset = pos % self.sector_size
        assert offset == 0
        pos -= offset
        #for i in range(0, len(data), self.sector_size):

        win32file.SetFilePointer(self.handle, pos, win32file.FILE_BEGIN)
        try:
            res = win32file.WriteFile(self.handle, data)
            if res != (0, len(data)):
                #raise IOError(f"An error occurred: {res}")
                eprint("An error occurred: {res}")
                return False

        except Exception as e:
            eprint(e)
            eprint("write failed", pos, len(data))
            return False

        return True
