# PySInfo:一个轻量的系统信息命令行工具

写代码、跑模型,日常难免要查看设备配置。尤其云服务器往往没有 GUI,只能用 CLI,查看配置得装一堆第三方工具。

以前我一直用 neofetch,但安装和依赖偏重。于是顺手用 Python 做了这个轻量工具:几百行代码,开箱即用,关键硬件与软件信息一屏展示。

**不需要 root**:任何需要 root 才能读到的东西(比如 SMBIOS 里的内存插槽/频率)会直接不显示,而不是硬撑一个 "Unknown"。

## 特性

- 一屏展示:系统、内核、运行时长、Shell、终端、CPU、GPU、内存、磁盘、网络、Python、CUDA/OpenCL/Vulkan
- **自适应终端宽度**:任何行都不换行/串行;过长的值用 `…` 截断;窗口太窄时自动把图标竖排到信息上方
- **平台图标**:企鹅(Linux)、田字窗(Windows)、苹果(macOS)、小恶魔 Beastie(FreeBSD / OpenBSD / NetBSD / DragonFly)
- **`--logo` 参数**:在任意机器上强制预览其它平台的图标和主题色
- 纯 Python,依赖少:psutil / distro / GPUtil-fix / colorama

## 安装

### 从源码运行

```Bash
git clone https://github.com/EasyCam/Pysinfo.git
cd Pysinfo
python -m pip install -r requirements.txt
python -m pysinfo
```

### 通过 PyPI 安装

```Bash
pip install pysinfo
pysinfo
```

## 用法

```Bash
pysinfo                     # 自动识别当前平台
python -m pysinfo           # 以模块方式运行
python run.py               # 单文件独立版

pysinfo --logo windows      # 强制预览某平台图标
pysinfo --logo macos        # 别名:mac、darwin、osx、apple
pysinfo --logo bsd          # 别名:freebsd、openbsd、netbsd、dragonfly
pysinfo --logo linux        # 别名:tux
pysinfo --logo default      # 未知系统时的通用图标
```

## 示例

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

## 环境要求

- Python 3.8+
- `psutil`、`distro`、`GPUtil-fix`、`colorama`
- 可选:`pyopencl`(装了 ICD 时能更准确地检测 OpenCL)

## 许可证

MIT
