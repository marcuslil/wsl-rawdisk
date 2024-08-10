
import sys
import time
import os
import json
import tempfile
from subprocess import Popen, PIPE, run, DEVNULL
from threading import Thread
from fusepy import FUSE

import connections
import wsl
from connected_device import ConnectedDevice
from protocol import *
from eprint import eprint
from fuse_fs import FS

def main():
    tmp_mountpoint = tempfile.TemporaryDirectory(prefix="wsl_rawdisk_")
    mountpoint = os.path.abspath(tmp_mountpoint.name)

    connection = "stdio_elevated"

    server_path = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), 'wsl-rawdisk-server.exe'))
    if not os.path.exists(server_path):
        print("server not found")
        sys.exit(0)

    os.chdir(wsl.win2linux("C:\\"))
    tmp_base = wsl.win2linux(wsl.get_win_tmp())
    tmp_dir_tmp = tempfile.TemporaryDirectory(dir=tmp_base, prefix="wsl_rawdisk_")
    tmp_dir = tmp_dir_tmp.name
    os.chdir(tmp_dir)
    run(["cp", server_path, '.'])

    server_exe_lin = "./wsl-rawdisk-server.exe"
    server_exe_win = "wsl-rawdisk-server.exe"

    processes = []

    if connection == "tcpclient":
        host = wsl.get_host_addr()
        port = 50000
        conn = connections.TcpClientConnection(host, port)

    elif connection == "tcpserverelevated":
        host = wsl.get_wsl_addr()
        conn = connections.TcpServer(host, port=0)
        cmd = [server_exe_lin, 'elevate', 'tcpclient', host, str(conn.port)]
        p = Popen(cmd, stdin=DEVNULL, shell=False, start_new_session=True)
        processes.append(p)

    elif connection == "tcpserversudo":
        host = wsl.get_wsl_addr()
        conn = connections.TcpServer(host, port=0)
        cmd = ['/mnt/c/Windows/System32/cmd.exe', '/c', 'sudo', server_exe_win, 'tcpclient', host, str(conn.port)]
        p = open(cmd)
        processes.append(p)

    elif connection == "stdio_sudo":
        cmd = ['/mnt/c/Windows/System32/cmd.exe', '/c', 'sudo', server_exe_win, 'stdiopipe']

        p = Popen(cmd, stdout=PIPE, stdin=PIPE, text=False, shell=False, start_new_session=True)
        processes.append(p)
        conn = connections.SubprocessConnection(p)

    elif connection == "stdio_elevated":
        name = "wsl_rawdisk_" + str(time.time())
        cmd = [server_exe_lin, 'stdiopipe', 'forward', 'namedpipeserver', name, '0', 'elevate', 'namedpipeclient', name]

        p = Popen(cmd, stdout=PIPE, stdin=PIPE, text=False, shell=False, start_new_session=True)
        processes.append(p)
        conn = connections.SubprocessConnection(p)

    if not conn.connect():
        raise

    conn.pack("B", CMD_GET_DISKDRIVES)
    size = conn.unpack("I")
    drives = conn.recv(size)
    drives = json.loads(drives.decode("utf-8"))
    drives.sort()

    #eprint("connected")

    devices = {}
    for d in drives:
        if not d.startswith("\\\\.\\"):
            d = "\\\\.\\" + d
        device = ConnectedDevice(conn, d)
        if len(d) == 5 and d.startswith("\\\\.\\"):
            d = d + ":"
        filename = d.replace("\\", "").replace(".", "").replace(":", "").replace("/", "").lower()
        if device.open():
            devices[filename] = device
            device.filename = filename
            device.loop_dev = None
        else:
            print("opening", d, "failed")

    running = True
    def loop_device_thread():
        if not os.geteuid() == 0:
            eprint("not running as root, cannot create loop devices")
            return

        while running and not os.path.exists(mountpoint + "/" + list(devices.values())[0].filename):
            time.sleep(0.01)

        for d in devices.values():
            c = ["losetup", "-f", "--show", "-P", "--direct-io=on", mountpoint + "/" + d.filename]
            p = Popen(c, stdout=PIPE, stderr=PIPE, text=True)
            loop_dev, err = p.communicate()
            if err == '':
                d.loop_dev = loop_dev.rstrip("\n")
                print(d.device_name, d.loop_dev)

    thread = Thread(target=loop_device_thread)
    thread.start()

    try:
        FUSE(FS(devices), mountpoint, nothreads=True, foreground=True, allow_other=True, debug=False)
    except KeyboardInterrupt:
        pass

    running = False
    conn.pack("b", CMD_CLOSE)
    conn.close()
    thread.join()

    for d in devices.values():
        if d.loop_dev is not None:
            c = ["losetup", "-d", d.loop_dev]
            run(c)

    for p in processes:
        p.wait()

if __name__ == '__main__':
    main()
