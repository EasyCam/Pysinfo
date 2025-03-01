"""
SysInfo: A command line tool that displays information about the current system, including hardware and critical software.
version 1.0
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
from colorama import Fore, Style

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
    
    # Try to get GPU info
    try:
        gpus = GPUtil.getGPUs()
        if gpus:
            info["gpu"] = f"{gpus[0].name} ({bytes_to_readable(gpus[0].memoryTotal * 1024 * 1024)})"
        else:
            info["gpu"] = "No dedicated GPU detected"
    except:
        info["gpu"] = "GPU information unavailable"
    
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
    
    # Prepare data display
    data_lines = [
        f"{color}OS:{Style.RESET_ALL} {system_info['os']}",
        f"{color}Host:{Style.RESET_ALL} {system_info['hostname']}",
        f"{color}Kernel:{Style.RESET_ALL} {system_info['kernel']}",
        f"{color}Uptime:{Style.RESET_ALL} {system_info['uptime']}",
        f"{color}Shell:{Style.RESET_ALL} {os.path.basename(system_info['shell'])}",
        f"{color}CPU:{Style.RESET_ALL} {system_info['cpu']}",
        f"{color}CPU Cores:{Style.RESET_ALL} {system_info['cpu_cores']}",
        f"{color}CPU Usage:{Style.RESET_ALL} {system_info['cpu_usage']}",
        f"{color}GPU:{Style.RESET_ALL} {system_info['gpu']}",
        f"{color}Memory:{Style.RESET_ALL} {system_info['memory']}",
        f"{color}Disk:{Style.RESET_ALL} {system_info['disk']}",
        f"{color}IP Address:{Style.RESET_ALL} {system_info['ip_address']}",
        f"{color}Terminal:{Style.RESET_ALL} {system_info['terminal']}"
    ]
    
    # Calculate spacing
    logo_width = max(len(line) for line in ascii_logo)
    spacing = 4
    
    # Print logo and info side by side
    max_lines = max(len(ascii_logo), len(data_lines))
    for i in range(max_lines):
        logo_line = ascii_logo[i] if i < len(ascii_logo) else " " * logo_width
        info_line = data_lines[i] if i < len(data_lines) else ""
        print(f"{color}{logo_line}{' ' * spacing}{Style.RESET_ALL}{info_line}")
    
    # Print color blocks
    print("\n" + "".join(f"{color}███{Style.RESET_ALL}" for color in [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN, Fore.WHITE]))

if __name__ == "__main__":
    print_system_info()