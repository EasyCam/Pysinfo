# PySInfo

PySInfo: A python command line tool that displays information about the current system, including hardware and critical software.

version 1.0

## Installation

### Run from source

```Bash
git clone https://github.com/EasyCam/Pysinfo.git
cd Pysinfo
python -m pip install -r requirements.txt
python -m pysinfo
```

### Install from PyPI

```Bash
pip install pysinfo
python -m pysinfo
```

### Example

```Bash

╒════════════════════════════════════════════════════════════════╕
│     PySinfo: A Python Tool to Get System Infomation            │
╘════════════════════════════════════════════════════════════════╛

                                ..,    OS: Windows 10.0.26100
                    ....,,:;+ccllll    Host: MSI
      ...,,+:;  cllllllllllllllllll    Kernel: 11
,cclllllllllll  lllllllllllllllllll    Uptime: 0 days, 22 hours, 50 minutes
llllllllllllll  lllllllllllllllllll    Shell: cmd.exe
llllllllllllll  lllllllllllllllllll    Terminal: 92x49
llllllllllllll  lllllllllllllllllll
llllllllllllll  lllllllllllllllllll    Hardware:
llllllllllllll  lllllllllllllllllll    CPU Model: AMD Ryzen 9 7945HX with Radeon Graphics
                                       CPU Architecture: AMD64
llllllllllllll  lllllllllllllllllll    CPU Current Freq: 2501.0
llllllllllllll  lllllllllllllllllll    CPU Cores: 16 (Physical), 32 (Logical)
llllllllllllll  lllllllllllllllllll    CPU Usage: 6.3%
llllllllllllll  lllllllllllllllllll    GPU: NVIDIA GeForce RTX 4060 Laptop GPU (8.00 GB)
llllllllllllll  lllllllllllllllllll    Memory: 28.94 GB / 95.18 GB (30.4%)
`'ccllllllllll  lllllllllllllllllll    Memory Slots: 2 (48 GB, 48 GB)
       `' \*::  :ccllllllllllllllll    Memory Speed: 5200 MHz
                       ````''*::cll    Disk: 3.50 TB / 3.64 TB (96.3%)
                                 ``
                                       Network:
                                       IP Address: 192.168.0.2

                                       Development Environment:
                                       Python: 3.12.2 (CPython)
                                       Python Path: C:\Miniconda3\python.exe

                                       Graphics API Support:
                                       CUDA: 12.6.85
                                       OpenCL: Platform Version:                            OpenCL 3.0 CUDA 12.8.51
                                       Vulkan: 1.4.303

██████████████████████████████████████████
```



```Bash
╒════════════════════════════════════════════════════════════════╕
│     PySinfo: A Python Tool to Get System Infomation            │
╘════════════════════════════════════════════════════════════════╛

         _nnnn_                         OS: Ubuntu 24.04
        dGGGGMMb                        Host: MSI
       @p~qp~~qMb                       Kernel: 5.15.167.4-microsoft-standard-WSL2
       M|@||@) M|                       Uptime: 0 days, 0 hours, 0 minutes
       @,----.JM|                       Shell: bash
      JS^\__/  qKL                      Terminal: 87x48
     dZP        qKRb
    dZP          qKKb                   Hardware:
   fZP            SMMb                  CPU Model: AMD Ryzen 9 7945HX with Radeon Graphics
   HZM            MMMM                  CPU Architecture: x86_64
   FqM            MMMM                  CPU Current Freq: 2.50 GHz
 __| ".        |\dS"qML                 CPU Cores: 4 (Physical), 8 (Logical)
 |    `.       | `' \Zq                 CPU Usage: 0.0%
_)      \.___.,|     .'                 GPU: NVIDIA GeForce RTX 4060 Laptop GPU (8.00 GB)
\____   )MMMMMP|   .'                   Memory: 716.67 MB / 31.35 GB (3.5%)
     `-'       `--'                     Memory Slots: Unknown
                                        Memory Speed: Unknown
                                        Disk: 155.09 GB / 1006.85 GB (16.2%)

                                        Network:
                                        IP Address: 127.0.1.1

                                        Development Environment:
                                        Python: 3.11.7 (CPython)
                                        Python Path: /home/fred/anaconda3/bin/python

                                        Graphics API Support:
                                        CUDA: 12.9.86
                                        OpenCL: Not detected
                                        Vulkan: Not detected

██████████████████████████████████████████

Report generated on: 2025-08-10 19:36:05
```