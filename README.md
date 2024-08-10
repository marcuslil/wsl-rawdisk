wsl-rawdisk enables access to pysical drives from WSL including the Windows system disk.

To start the app, extract the contents of the release package on the WSL side, then run:\
sudo python3 wsl-rawdisk.py

You can then access the partitions on your system disk using /dev/loop0p1 /dev/loop0p2 and so on.

In WSL fusepy must be installed. For ubuntu this can be done using:\
sudo apt install python3-fusepy

Use at own risk, destroying partition tables or system disk can lead to bricked system.\
Windows will automatically write protect partitions already mounted in Windows.

Tested on Windows 11 and WSL running Ubuntu 22.04

The wsl-rawdisk-server.exe is included in the distribution package, but can be build on windows:
python3 -m venv\
venv\Scripts\activate\
pip install -r venv-win-requirements.txt\
pyinstaller -F wsl-rawdisk-server.py
