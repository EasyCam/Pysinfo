# PySInfo

PySInfo: A Python command line tool that displays information about the current system, including hardware and critical software.

version 1.3.3

## Features

- One-screen summary: OS, kernel, uptime, shell, terminal, CPU, GPU, memory, disk, network, Python, CUDA/OpenCL/Vulkan
- **No root required**: anything that would need root (e.g. SMBIOS memory slots/speed) is simply left out instead of shown as "Unknown"
- **Responsive layout**: fits the terminal width and never wraps; over-long values are shortened with `…`, and narrow windows stack the logo above the info block
- **Per-platform logos**: Tux (Linux), Windows tiles (田), Apple (macOS), BSD Daemon / Beastie (FreeBSD, OpenBSD, NetBSD, DragonFly)
- **`--logo` flag** to preview any platform's logo (and theme color) on any machine

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
pysinfo
```

## Usage

```Bash
pysinfo                     # detect the current platform
python -m pysinfo           # same, run as a module
python run.py               # standalone single-file version

pysinfo --logo windows      # force a platform logo for preview
pysinfo --logo macos        # aliases: mac, darwin, osx, apple
pysinfo --logo bsd          # aliases: freebsd, openbsd, netbsd, dragonfly
pysinfo --logo linux        # alias: tux
pysinfo --logo default      # generic icon for unknown systems
```

## Example

```Bash
╒═══════════════════════════════════════════════════════════════╕
│        PySinfo: A Python Tool to Get System Infomation        │
╘═══════════════════════════════════════════════════════════════╛

OS: Ubuntu 26.04                                                                          .---.
Host: aimax                                                                              /     \
Kernel: 7.0.0-38-generic                                                                 \.o o./
Uptime: 26d 13h 53m                                                                      /`\_/`\
Shell: bash                                                                             //  _  \\
Terminal: 100x24                                                                       | \     )|_
                                                                                      /`\_`>  <_/ \
Hardware:                                                                             \__/'---'\__/
CPU Model: AMD RYZEN AI MAX+ 395 w/ Radeon 8060S
CPU Architecture: x86_64
CPU Current Freq: 3.54 GHz
CPU Cores: 16 (Physical), 32 (Logical)
CPU Usage: 0.0%
GPU: Strix Halo [Radeon Graphics / Radeon 8050S Graphics / Radeon 8060S Graphics]
Memory: 51.57 GB / 119.24 GB (43.2%)
Disk: 914.96 GB / 3.58 TB (26.3%)

Network:
IP Address: 192.168.0.124

Development Environment:
Python: 3.12.14 (CPython)
Python Path: ~/miniconda3/envs/dev/bin/python3.12

Graphics API Support:
CUDA: Not available
OpenCL: Not detected
Vulkan: 1.4.341

████████████████████████████████████████████████████████████████████████████████████████████████████

Report generated on: 2026-11-08 08:54:38
```

## Requirements

- Python 3.8+
- `psutil`, `distro`, `GPUtil-fix`, `colorama`
- Optional: `pyopencl` (better OpenCL detection when an ICD is installed)

## License

MIT
