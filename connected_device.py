from protocol import CMD_OPEN, CMD_READ, CMD_WRITE, CMD_GET_SIZE

class ConnectedDevice():
    def __init__(self, conn, device_name):
        self.conn = conn
        self.device_name = device_name
        self.index = -1

    def open(self):
        device_name = self.device_name.encode('utf-8')
        self.conn.pack("=BH", CMD_OPEN, len(device_name))
        self.conn.send(device_name)
        self.index = self.conn.unpack("h")
        self.size = self.get_size()
        return self.index != -1

    def read(self, pos, size):
       self.conn.pack("=BH2Q", CMD_READ, self.index, pos, size)
       status = self.conn.unpack("B")
       if status == 0:
           data = self.conn.recv(size)
       else:
           data = b''
       return data

    def write(self, pos, data):
       self.conn.pack("=BH2Q", CMD_WRITE, self.index, pos, len(data))
       self.conn.send(data)
       return self.conn.unpack("B") == 0

    def get_size(self):
        self.conn.pack("=BH", CMD_GET_SIZE, self.index)
        return self.conn.unpack("Q")

    def close(self):
        self.conn.close()