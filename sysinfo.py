"""
SysInfo: A command line tool that displays information about the current system, including hardware and critical software.
version 1.1
"""

import platform
import psutil
import os
import socket
import datetime
import distro
import shutil
import GPUtil
import colorama
import sys
import subprocess
from colorama import Fore, Style, Back

def get_system_info():
    info = {}
    
    # OS Information
    if platform.system() == "Windows":
        info["os"] = f"{platform.system()} {platform.version()}"
    else:
        info["os"] = f"{distro.name()} {distro.version()}"
    
    info["hostname"] = socket.gethostname()
    info["kernel"] = platform.release()
    info["uptime"] = get_uptime()
    
    # Hardware Information
    info["cpu"] = platform.processor()
    info["cpu_cores"] = f"{psutil.cpu_count(logical=False)} (Physical), {psutil.cpu_count(logical=True)} (Logical)"
    info["cpu_usage"] = f"{psutil.cpu_percent()}%"
    
    mem = psutil.virtual_memory()
    info["memory"] = f"{bytes_to_readable(mem.used)} / {bytes_to_readable(mem.total)} ({mem.percent}%)"
    
    # Python Information
    info["python_version"] = f"{platform.python_version()} ({platform.python_implementation()})"
    info["python_path"] = sys.executable
    
    # Try to get GPU info and CUDA support
    try:
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu_info = []
            for i, gpu in enumerate(gpus):
                gpu_info.append(f"{gpu.name} ({bytes_to_readable(gpu.memoryTotal * 1024 * 1024)})")
            info["gpu"] = " | ".join(gpu_info)
            
            # Check CUDA support
            cuda_version = check_cuda_version()
            info["cuda"] = cuda_version if cuda_version else "Not detected"
        else:
            info["gpu"] = "No dedicated GPU detected"
            info["cuda"] = "Not available"
    except Exception as e:
        info["gpu"] = "GPU information unavailable"
        info["cuda"] = "Not detected"
    
    # Check OpenCL support
    info["opencl"] = check_opencl_version()
    
    # Check Vulkan support
    info["vulkan"] = check_vulkan_version()
    
    # Disk Information
    disk = psutil.disk_usage('/')
    info["disk"] = f"{bytes_to_readable(disk.used)} / {bytes_to_readable(disk.total)} ({disk.percent}%)"
    
    # Network Information
    info["ip_address"] = socket.gethostbyname(socket.gethostname())
    
    # Shell Information
    if platform.system() == "Windows":
        info["shell"] = os.environ.get("COMSPEC", "Unknown")
    else:
        info["shell"] = os.environ.get("SHELL", "Unknown")
    
    # Terminal Information
    terminal_size = shutil.get_terminal_size()
    info["terminal"] = f"{terminal_size.columns}x{terminal_size.lines}"
    
    return info

def check_cuda_version():
    try:
        if platform.system() == "Windows":
            # Try to get CUDA version from nvcc
            result = subprocess.run(["nvcc", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if "release" in line.lower() and "V" in line:
                        return line.split("V")[1].split(" ")[0]
        else:
            # For Linux/macOS
            cuda_path = "/usr/local/cuda/bin/nvcc"
            if os.path.exists(cuda_path):
                result = subprocess.run([cuda_path, "--version"], capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if "release" in line.lower() and "V" in line:
                            return line.split("V")[1].split(" ")[0]
        
        # Alternative check with nvidia-smi for CUDA driver version
        result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if "CUDA Version:" in line:
                    return line.split("CUDA Version:")[1].strip()
        
        return "Not detected"
    except:
        return "Not detected"

def check_opencl_version():
    try:
        # Try to detect OpenCL with a simple command
        if platform.system() == "Windows":
            result = subprocess.run(["clinfo", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if "OpenCL" in line:
                        return line.strip()
        else:
            # For Linux
            if os.path.exists("/usr/bin/clinfo"):
                result = subprocess.run(["clinfo", "--version"], capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if "OpenCL" in line:
                            return line.strip()
        
        return "Not detected"
    except:
        return "Not detected"

def check_vulkan_version():
    try:
        # Try to detect Vulkan with vulkaninfo
        if platform.system() == "Windows":
            result = subprocess.run(["vulkaninfo", "--summary"], capture_output=True, text=True)
        else:
            result = subprocess.run(["vulkaninfo"], capture_output=True, text=True)
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if "Vulkan Instance Version:" in line:
                    return line.split("Vulkan Instance Version:")[1].strip()
                if "Vulkan API Version:" in line:
                    return line.split("Vulkan API Version:")[1].strip()
        
        return "Not detected"
    except:
        return "Not detected"

def get_uptime():
    if platform.system() == "Windows":
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        now = datetime.datetime.now()
        uptime = now - boot_time
        days, remainder = divmod(uptime.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(days)} days, {int(hours)} hours, {int(minutes)} minutes"
    else:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            days, remainder = divmod(uptime_seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{int(days)} days, {int(hours)} hours, {int(minutes)} minutes"

def bytes_to_readable(bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} PB"

def get_ascii_logo(system):
    logos = {
        "Windows": [
            "                                ..,",
            "                    ....,,:;+ccllll",
            "      ...,,+:;  cllllllllllllllllll",
            ",cclllllllllll  lllllllllllllllllll",
            "llllllllllllll  lllllllllllllllllll",
            "llllllllllllll  lllllllllllllllllll",
            "llllllllllllll  lllllllllllllllllll",
            "llllllllllllll  lllllllllllllllllll",
            "llllllllllllll  lllllllllllllllllll",
            "                                   ",
            "llllllllllllll  lllllllllllllllllll",
            "llllllllllllll  lllllllllllllllllll",
            "llllllllllllll  lllllllllllllllllll",
            "llllllllllllll  lllllllllllllllllll",
            "llllllllllllll  lllllllllllllllllll",
            "`'ccllllllllll  lllllllllllllllllll",
            "      `' \\*::  :ccllllllllllllllll",
            "                       ````''*::cll",
            "                                 ``",
        ],
        "Linux": [
            "         _nnnn_",
            "        dGGGGMMb",
            "       @p~qp~~qMb",
            "       M|@||@) M|",
            "       @,----.JM|",
            "      JS^\\__/  qKL",
            "     dZP        qKRb",
            "    dZP          qKKb",
            "   fZP            SMMb",
            "   HZM            MMMM",
            "   FqM            MMMM",
            " __| \".        |\\dS\"qML",
            " |    `.       | `' \\Zq",
            "_)      \\.___.,|     .'",
            "\\____   )MMMMMP|   .'",
            "     `-'       `--'",
        ],
        "Darwin": [
            "                  #####",
            "                 ######",
            "                ######",
            "               #######",
            "              #######",
            "             #######",
            "            #######",
            "           #######  #####",
            "          ####### #######",
            "         ##################",
            "        #################",
            "       ################",
            "      ###############",
            "     ##############",
            "    #############",
            "   ############",
            "  ###########",
        ],
    }
    
    default_logo = [
        "   _____            _                 ",
        "  / ____|          | |                ",
        " | (___  _   _ ___ | |_ ___ _ __ ___  ",
        "  \\___ \\| | | / __|| __/ _ \\ '_ ` _ \\ ",
        "  ____) | |_| \\__ \\| ||  __/ | | | | |",
        " |_____/ \\__, |___/ \\__\\___|_| |_| |_|",
        "          __/ |                       ",
        "         |___/                        ",
    ]
    
    return logos.get(system, default_logo)

def print_system_info():
    colorama.init()
    system_info = get_system_info()
    ascii_logo = get_ascii_logo(platform.system())
    
    # ANSI Color codes for different OS
    color = Fore.CYAN  # Default color
    if platform.system() == "Windows":
        color = Fore.BLUE
    elif platform.system() == "Linux":
        color = Fore.GREEN
    elif platform.system() == "Darwin":
        color = Fore.WHITE
    
    # Header
    print(f"\n{Style.BRIGHT}{Back.BLACK}{color}╒════════════════════════════════════════════════════════════════╕{Style.RESET_ALL}")
    print(f"{Style.BRIGHT}{Back.BLACK}{color}│                      SYSTEM INFORMATION                         │{Style.RESET_ALL}")
    print(f"{Style.BRIGHT}{Back.BLACK}{color}╘════════════════════════════════════════════════════════════════╛{Style.RESET_ALL}\n")
    
    # Prepare data display
    data_lines = [
        f"{color}OS:{Style.RESET_ALL} {system_info['os']}",
        f"{color}Host:{Style.RESET_ALL} {system_info['hostname']}",
        f"{color}Kernel:{Style.RESET_ALL} {system_info['kernel']}",
        f"{color}Uptime:{Style.RESET_ALL} {system_info['uptime']}",
        f"{color}Shell:{Style.RESET_ALL} {os.path.basename(system_info['shell'])}",
        f"{color}Terminal:{Style.RESET_ALL} {system_info['terminal']}",
        "",
        f"{Style.BRIGHT}{color}Hardware:{Style.RESET_ALL}",
        f"{color}CPU:{Style.RESET_ALL} {system_info['cpu']}",
        f"{color}CPU Cores:{Style.RESET_ALL} {system_info['cpu_cores']}",
        f"{color}CPU Usage:{Style.RESET_ALL} {system_info['cpu_usage']}",
        f"{color}GPU:{Style.RESET_ALL} {system_info['gpu']}",
        f"{color}Memory:{Style.RESET_ALL} {system_info['memory']}",
        f"{color}Disk:{Style.RESET_ALL} {system_info['disk']}",
        "",
        f"{Style.BRIGHT}{color}Network:{Style.RESET_ALL}",
        f"{color}IP Address:{Style.RESET_ALL} {system_info['ip_address']}",
        "",
        f"{Style.BRIGHT}{color}Development Environment:{Style.RESET_ALL}",
        f"{color}Python:{Style.RESET_ALL} {system_info['python_version']}",
        f"{color}Python Path:{Style.RESET_ALL} {system_info['python_path']}",
        "",
        f"{Style.BRIGHT}{color}Graphics API Support:{Style.RESET_ALL}",
        f"{color}CUDA:{Style.RESET_ALL} {system_info['cuda']}",
        f"{color}OpenCL:{Style.RESET_ALL} {system_info['opencl']}",
        f"{color}Vulkan:{Style.RESET_ALL} {system_info['vulkan']}",
    ]
    
    # Calculate spacing
    logo_width = max(len(line) for line in ascii_logo)
    spacing = 4
    
    # Print logo and info side by side
    logo_length = len(ascii_logo)
    for i in range(logo_length):
        logo_line = ascii_logo[i] if i < len(ascii_logo) else " " * logo_width
        info_line = data_lines[i] if i < len(data_lines) else ""
        print(f"{color}{logo_line}{' ' * spacing}{Style.RESET_ALL}{info_line}")
    
    # Print remaining info
    for i in range(logo_length, len(data_lines)):
        print(f"{' ' * (logo_width + spacing)}{data_lines[i]}")
    
    # Print color blocks
    print("\n" + "".join(f"{color}██████{Style.RESET_ALL}" for color in [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN, Fore.WHITE]))
    
    # Footer
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{Style.DIM}Report generated on: {current_time}{Style.RESET_ALL}")

if __name__ == "__main__":
    print_system_info()