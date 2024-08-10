import sys
import namedpipe
import os
import win32ui
import win32event
import wmi
import json
import win32com.shell.shell as shell
from win32com.shell import shellcon

import connections
from eprint import eprint
from device import Device
from connected_device import ConnectedDevice
from protocol import *


def parse_connection(args):
    if args[0] == "tcpserver":
        host = args[1]
        port = int(args[2])
        return connections.TcpServer(host, port), 3

    elif args[0] == "tcpclient":
        host = args[1]
        port = int(args[2])
        return connections.TcpClientConnection(host, port), 3

    elif args[0] == "stdiopipe":
        return connections.StdioConnection(), 1

    elif args[0] == "namedpipeclient":
        name = args[1]
        print(args[:2])
        return namedpipe.NamedPipeClient(name), 2

    elif args[0] == "namedpipeserver":
        name = args[1]
        full_access = bool(args[2])
        return namedpipe.NamedPipeServer(name, full_access), 3

    else:
        return None, 0

def main():
    # required if elevate is used
    script = os.path.abspath(sys.argv[0])
    if script.endswith('.py'):  # normal python interpreter
        exe = sys.executable
        params = [script]
    else:  # installed with pyinstaller
        exe = script
        params = []

    server_conn = None
    forward_conn = None
    reconnect = False
    debug = False
    processes = []

    #eprint("Server started, args", sys.executable, sys.argv)

    i = 1
    while i < len(sys.argv):
        new_conn, consumed_args = parse_connection(sys.argv[i:])
        if new_conn:
            server_conn = new_conn
            i += consumed_args

        elif sys.argv[i] == "reconnect":
            reconnect = True
            i += 1

        elif sys.argv[i] == "debug":
            debug = True
            i += 1

        elif sys.argv[i] == "forward":
            new_conn, consumed_args = parse_connection(sys.argv[i+1:])
            forward_conn = new_conn
            i += consumed_args + 1

        elif sys.argv[i] == "elevate":
            params += sys.argv[i+1:]
            p = shell.ShellExecuteEx(lpVerb='runas', lpFile=exe, lpParameters=' '.join(params), fMask=shellcon.SEE_MASK_NOCLOSEPROCESS)
            i = len(sys.argv)
            processes.append(p)

        elif sys.argv[i] == "echo":
            print(sys.argv[i+1], flush=True)
            i += 2

        elif sys.argv[i] == "message":
            win32ui.MessageBox(sys.argv[i+1], "wsl-rawdisk-server")
            i += 2

        else:
            raise Exception("Unknown command " + sys.argv[i])

    if forward_conn is not None:
        assert forward_conn.connect()

    if server_conn is not None:
        while True:
            devices = []
            if not server_conn.connect():
                break
            if debug:
                eprint("connected")

            while True:
                try:
                    command = server_conn.unpack("B")
                    if command == CMD_OPEN:  # open
                        size = server_conn.unpack("H")
                        device_name = server_conn.recv(size).decode('utf-8')
                        if debug:
                            eprint("recv cmd open", device_name)
                        if forward_conn is None:
                            device = Device(device_name)
                        else:
                            device = ConnectedDevice(forward_conn, device_name)

                        if device.open():
                            server_conn.pack("h", len(devices))
                            devices.append(device)
                        else:
                            server_conn.pack("h", -1)

                    elif command == CMD_READ:  # read
                        index, pos, size = server_conn.unpack("=H2Q")
                        # eprint("read", index, pos, size)
                        if index < len(devices):
                            data = devices[index].read(pos, size)
                        else:
                            eprint("index out of range")
                            data = None

                        if data is None:
                            server_conn.pack("B", 1)
                        else:
                            server_conn.pack("B", 0)
                            server_conn.send(data)

                    elif command == CMD_WRITE:  # write
                        index, pos, size = server_conn.unpack("=H2Q")
                        # eprint("write", index, pos, size)
                        data = server_conn.recv(size)
                        assert len(data) == size
                        if index < len(devices):
                            res = devices[index].write(pos, data)
                        else:
                            res = False

                        server_conn.pack("B", 0 if res else 1)

                    elif command == CMD_GET_SIZE:
                        index = server_conn.unpack("H")
                        if index < len(devices):
                            server_conn.pack("Q", devices[index].size)
                        else:
                            eprint("index out of range")
                            server_conn.pack("Q", 0)

                    elif command == CMD_GET_DISKDRIVES:
                        drives = [disk.Name for disk in wmi.WMI().query("SELECT * from Win32_DiskDrive")]
                        drives = json.dumps(drives).encode("utf-8")
                        server_conn.pack("I", len(drives))
                        server_conn.send(drives)

                    elif command == CMD_CLOSE:
                        if forward_conn is not None:
                            forward_conn.pack("b", CMD_CLOSE)
                        break

                    else:
                        eprint("unknown command", command)

                except ConnectionError as e:
                    break

            for d in devices:
                d.close()

            if not reconnect:
                break

    for p in processes:
        try:
            win32event.WaitForSingleObject(p['hProcess'], -1)
        except:
            pass

if __name__ == '__main__':
    main()
