wsl-rawdisk enables access to pysical drives from WSL including the Windows system disk.

To start the app, extract the contents of the release package on the WSL side, then run:
sudo python3 wsl-rawdisk.py

In WSL fusepy must be installed. For ubuntu this can be done using:
sudo apt install python3-fusepy

Use at own risk, destroying partition tables or system disk can lead to bricked system.

Tested on Windows 11 and WSL running Ubuntu 22.04
