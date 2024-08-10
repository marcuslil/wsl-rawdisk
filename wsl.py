import json
from subprocess import Popen, PIPE

def get_host_addr():
    f = open("/etc/resolv.conf")
    for l in f:
        if l.startswith("nameserver"):
            return l.split()[1]
    return None

def get_wsl_addr():
    p = Popen("ip -o -4 -json addr list eth0", stdout=PIPE, shell=True)
    return json.loads(p.communicate()[0])[0]['addr_info'][0]['local']

def win2linux(win_path):
    p = Popen(["wslpath", "-u", win_path], stdout=PIPE, stderr=PIPE, text=True, shell=False)
    outs, errs = p.communicate()
    assert errs == '', errs
    return outs.rstrip("\n")

def linux2win(linux_path):
    p = Popen(["wslpath", "-w", linux_path], stdout=PIPE, stderr=PIPE, text=True, shell=False)
    outs, errs = p.communicate()
    assert errs == '', errs
    return outs.rstrip("\n")

def get_win_tmp():
    p = Popen(["/mnt/c/Windows/System32/cmd.exe", "/C", "echo %tmp%"], stdout=PIPE, stderr=PIPE, text=True, shell=False)
    outs, errs = p.communicate()
    assert errs == '', errs
    return outs.rstrip("\n")

