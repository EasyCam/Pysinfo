"""
PySInfo: A python command line tool that displays information about the current system, including hardware and critical software.
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
import sys
import subprocess
import re
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
    
    # Hardware Information - Enhanced CPU details
    cpu_info = get_detailed_cpu_info()
    info["cpu_model"] = cpu_info.get("model", platform.processor())
    info["cpu_arch"] = cpu_info.get("architecture", platform.machine())
    info["cpu_cores"] = f"{psutil.cpu_count(logical=False)} (Physical), {psutil.cpu_count(logical=True)} (Logical)"
    info["cpu_freq"] = cpu_info.get("frequency", "Unknown")
    info["cpu_cache"] = cpu_info.get("cache", "Unknown")
    info["cpu_process"] = cpu_info.get("process", "Unknown")
    info["cpu_usage"] = f"{psutil.cpu_percent()}%"
    
    # Enhanced Memory Information
    memory_info = get_detailed_memory_info()
    mem = psutil.virtual_memory()
    info["memory"] = f"{bytes_to_readable(mem.used)} / {bytes_to_readable(mem.total)} ({mem.percent}%)"
    info["memory_slots"] = memory_info.get("slots", "Unknown")
    info["memory_type"] = memory_info.get("type", "Unknown")
    info["memory_speed"] = memory_info.get("speed", "Unknown")
    info["memory_timings"] = memory_info.get("timings", "Unknown")
    
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

def get_detailed_cpu_info():
    """Get more detailed CPU information."""
    cpu_info = {
        "model": platform.processor(),
        "architecture": platform.machine(),
        "frequency": psutil.cpu_freq().current if psutil.cpu_freq() else "Unknown",
        "cores": f"{psutil.cpu_count(logical=False)} (Physical), {psutil.cpu_count(logical=True)} (Logical)",
        "usage": f"{psutil.cpu_percent()}%"
    }
    
    try:
        if platform.system() == "Windows":
            # Try multiple methods to get CPU model name
            model = None
            
            # Method 1: Try using WMI
            try:
                result = subprocess.run(["wmic", "cpu", "get", "name"], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) >= 2:
                        model = lines[1].strip()
            except:
                pass
            
            # Method 2: Try using PowerShell if WMI fails
            if not model or model == platform.processor():
                try:
                    result = subprocess.run(["powershell", "-Command", "(Get-CimInstance -Class Win32_Processor).Name"], 
                                            capture_output=True, text=True)
                    if result.returncode == 0 and result.stdout.strip():
                        model = result.stdout.strip()
                except:
                    pass
            
            # Method 3: Registry as fallback
            if not model or model == platform.processor():
                try:
                    result = subprocess.run(["reg", "query", "HKEY_LOCAL_MACHINE\\HARDWARE\\DESCRIPTION\\System\\CentralProcessor\\0", 
                                            "/v", "ProcessorNameString"], capture_output=True, text=True)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if "ProcessorNameString" in line:
                                model = line.split('REG_SZ')[1].strip()
                except:
                    pass
            
            if model and model != platform.processor():
                cpu_info["model"] = model
            
            # Rest of the function remains the same...
            # Get CPU frequency
            
            # Get CPU frequency
            result = subprocess.run(["wmic", "cpu", "get", "MaxClockSpeed"], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    freq_mhz = lines[1].strip()
                    if freq_mhz.isdigit():
                        cpu_info["frequency"] = f"{int(freq_mhz)/1000:.2f} GHz"
            
            # Try to get cache information
            result = subprocess.run(["wmic", "cpu", "get", "L2CacheSize,L3CacheSize"], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    cache_parts = lines[1].strip().split()
                    if len(cache_parts) >= 2:
                        l2_cache = f"{int(cache_parts[0])/1024:.1f} MB" if cache_parts[0].isdigit() else "Unknown"
                        l3_cache = f"{int(cache_parts[1])/1024:.1f} MB" if cache_parts[1].isdigit() else "Unknown"
                        cpu_info["cache"] = f"L2: {l2_cache}, L3: {l3_cache}"
            
            # Try to get CPU process information from model name
            model = cpu_info["model"].lower()
            if any(x in model for x in ["ryzen", "epyc"]):
                if "3000" in model or "4000" in model or "5000" in model:
                    cpu_info["process"] = "7nm"
                elif "6000" in model or "7000" in model:
                    cpu_info["process"] = "5nm"
                elif "7945" in model:
                    cpu_info["process"] = "4nm"
            elif any(x in model for x in ["intel", "core", "xeon"]):
                if "10th" in model or "10" in model:
                    cpu_info["process"] = "14nm"
                elif "11th" in model or "11" in model:
                    cpu_info["process"] = "10nm"
                elif "12th" in model or "12" in model:
                    cpu_info["process"] = "Intel 7 (10nm)"
                elif "13th" in model or "13" in model or "14th" in model or "14" in model:
                    cpu_info["process"] = "Intel 7 (10nm)"
        else:
            # For Linux systems
            if os.path.exists("/proc/cpuinfo"):
                with open("/proc/cpuinfo", "r") as f:
                    cpuinfo = f.read()
                
                # Extract model name
                model_match = re.search(r"model name\s+:\s+(.*)", cpuinfo)
                if model_match:
                    cpu_info["model"] = model_match.group(1)
                
                # Extract CPU frequency
                freq_match = re.search(r"cpu MHz\s+:\s+(.*)", cpuinfo)
                if freq_match:
                    freq_mhz = float(freq_match.group(1))
                    cpu_info["frequency"] = f"{freq_mhz/1000:.2f} GHz"
                
                # Extract cache info
                cache_match = re.search(r"cache size\s+:\s+(.*)", cpuinfo)
                if cache_match:
                    cpu_info["cache"] = cache_match.group(1)
    except Exception as e:
        pass
    
    return cpu_info

def get_detailed_memory_info():
    """Get detailed memory information including slots, type, speed, and timings."""
    memory_info = {
        "slots": "Unknown",
        "type": "Unknown",
        "speed": "Unknown",
        "timings": "Unknown"
    }
    
    try:
        if platform.system() == "Windows":
            # Get memory type and speed
            result = subprocess.run(["wmic", "memorychip", "get", "Capacity,Speed,DeviceLocator,MemoryType"], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    # Parse memory slots info
                    slots = []
                    speeds = []
                    mem_types = []
                    
                    for line in lines[1:]:
                        if line.strip():
                            parts = line.strip().split()
                            if len(parts) >= 3:
                                try:
                                    capacity = int(parts[0])
                                    slots.append(f"{capacity / (1024**3):.0f} GB")
                                    
                                    if parts[-2].isdigit():
                                        speeds.append(f"{parts[-2]} MHz")
                                    
                                    # Convert memory type code to human-readable
                                    mem_type_code = parts[-1] if parts[-1].isdigit() else "0"
                                    mem_type = "Unknown"
                                    mem_type_map = {
                                        "0": "Unknown", "1": "Other", "2": "DRAM",
                                        "3": "Synchronous DRAM", "4": "Cache DRAM",
                                        "5": "EDO", "6": "EDRAM", "7": "VRAM",
                                        "8": "SRAM", "9": "RAM", "10": "ROM",
                                        "11": "Flash", "12": "EEPROM", "13": "FEPROM",
                                        "14": "EPROM", "15": "CDRAM", "16": "3DRAM",
                                        "17": "SDRAM", "18": "SGRAM", "19": "RDRAM",
                                        "20": "DDR", "21": "DDR2", "22": "DDR2 FB-DIMM",
                                        "24": "DDR3", "26": "DDR4", "27": "DDR5",
                                        "28": "LPDDR", "29": "LPDDR2", "30": "LPDDR3",
                                        "31": "LPDDR4", "32": "LPDDR5"
                                    }
                                    mem_types.append(mem_type_map.get(mem_type_code, "Unknown"))
                                except:
                                    pass
                    
                    if slots:
                        memory_info["slots"] = f"{len(slots)} ({', '.join(slots)})"
                    if speeds and len(set(speeds)) == 1:
                        memory_info["speed"] = speeds[0]
                    elif speeds:
                        memory_info["speed"] = ', '.join(speeds)
                    if mem_types and len(set(mem_types)) == 1 and mem_types[0] != "Unknown":
                        memory_info["type"] = mem_types[0]
            
            # Try to get memory timings using a CAS latency estimate from speed
            if memory_info["speed"] != "Unknown" and "MHz" in memory_info["speed"]:
                speed_mhz = int(memory_info["speed"].split()[0])
                if "DDR4" in memory_info["type"]:
                    if speed_mhz >= 3600:
                        memory_info["timings"] = "CL16-18-18-38 (estimated)"
                    elif speed_mhz >= 3200:
                        memory_info["timings"] = "CL16-18-18-36 (estimated)"
                    elif speed_mhz >= 2666:
                        memory_info["timings"] = "CL16-18-18-35 (estimated)"
                    else:
                        memory_info["timings"] = "CL16-16-16-32 (estimated)"
                elif "DDR5" in memory_info["type"]:
                    if speed_mhz >= 6000:
                        memory_info["timings"] = "CL40-40-40-76 (estimated)"
                    elif speed_mhz >= 5600:
                        memory_info["timings"] = "CL36-36-36-76 (estimated)"
                    elif speed_mhz >= 4800:
                        memory_info["timings"] = "CL34-34-34-68 (estimated)"
                    else:
                        memory_info["timings"] = "CL30-30-30-60 (estimated)"
        else:
            # For Linux systems
            if os.path.exists("/proc/meminfo"):
                # Try using dmidecode if available
                try:
                    # This requires sudo permissions - may not work without them
                    result = subprocess.run(["sudo", "dmidecode", "--type", "memory"], capture_output=True, text=True)
                    if result.returncode == 0:
                        output = result.stdout
                        
                        # Count memory slots
                        slot_count = output.count("Memory Device")
                        if slot_count > 0:
                            memory_info["slots"] = str(slot_count)
                        
                        # Look for type
                        type_match = re.search(r"Type: (DDR\d+)", output)
                        if type_match:
                            memory_info["type"] = type_match.group(1)
                        
                        # Look for speed
                        speed_match = re.search(r"Speed: (\d+ MHz)", output)
                        if speed_match:
                            memory_info["speed"] = speed_match.group(1)
                except:
                    pass
    except Exception as e:
        pass
    
    return memory_info

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
        f"{color}CPU Model:{Style.RESET_ALL} {system_info['cpu_model']}",
        f"{color}CPU Architecture:{Style.RESET_ALL} {system_info['cpu_arch']}",
        f"{color}CPU Current Freq:{Style.RESET_ALL} {system_info['cpu_freq']}MHz",
        f"{color}CPU Cores:{Style.RESET_ALL} {system_info['cpu_cores']}",
        f"{color}CPU Usage:{Style.RESET_ALL} {system_info['cpu_usage']}",
        f"{color}GPU:{Style.RESET_ALL} {system_info['gpu']}",
        f"{color}Memory:{Style.RESET_ALL} {system_info['memory']}",
        f"{color}Memory Slots:{Style.RESET_ALL} {system_info['memory_slots']}",
        f"{color}Memory Type:{Style.RESET_ALL} {system_info['memory_type']}",
        f"{color}Memory Speed:{Style.RESET_ALL} {system_info['memory_speed']}",
        f"{color}Memory Timings:{Style.RESET_ALL} {system_info['memory_timings']}",
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
    for i in range(min(logo_length, len(data_lines))):
        logo_line = ascii_logo[i]
        info_line = data_lines[i]
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