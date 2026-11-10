"""
PySInfo: A python command line tool that displays information about the current system, including hardware and critical software.
version 1.3.4
"""
__version__ = "1.3.4"

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
import unicodedata
from colorama import Fore, Style, Back

def get_system_info():
    info = {}
    
    # OS Information
    if platform.system() == "Windows":
        info["os"] = f"{platform.system()} {platform.version()}"
    elif platform.system() == "Darwin":
        mac_ver = platform.mac_ver()[0]
        info["os"] = f"macOS {mac_ver}"
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
    info["memory_speed"] = memory_info.get("speed", "Unknown")
    
    # Python Information
    info["python_version"] = f"{platform.python_version()} ({platform.python_implementation()})"
    exe = sys.executable
    home = os.path.expanduser("~")
    if home and home != os.sep and exe.startswith(home):
        exe = "~" + exe[len(home):]
    info["python_path"] = exe
    
    # GPU: NVML/NVIDIA first (GPUtil), then a root-free lspci/sysfs fallback.
    # GPUtil raises when nvidia-smi is missing, so the fallback must also run
    # on exceptions - otherwise AMD-only machines report "unavailable".
    gpu_list = []
    try:
        for gpu in GPUtil.getGPUs():
            gpu_list.append(f"{gpu.name} ({bytes_to_readable(gpu.memoryTotal * 1024 * 1024)})")
    except Exception:
        pass
    if not gpu_list:
        gpu_list = get_fallback_gpus()
    if not gpu_list and platform.system() == "Darwin":
        try:
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            gpu_list = re.findall(r"Chipset Model:\s+(.*)", result.stdout) or ["Apple GPU"]
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            gpu_list = []
    info["gpus"] = gpu_list

    if platform.system() == "Darwin":
        info["cuda"] = "Not supported on macOS"
    else:
        cuda_version = check_cuda_version()
        info["cuda"] = cuda_version if cuda_version else "Not available"
    
    # Check OpenCL support
    info["opencl"] = check_opencl_version()
    
    # Check Vulkan support
    info["vulkan"] = check_vulkan_version()
    
    # Disk Information
    disk = psutil.disk_usage('/')
    info["disk"] = f"{bytes_to_readable(disk.used)} / {bytes_to_readable(disk.total)} ({disk.percent}%)"
    
    # Network Information
    info["ip_address"] = get_primary_ip()
    
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
        elif platform.system() == "Darwin":
            # CPU model
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                cpu_info["model"] = result.stdout.strip()
            else:
                # Apple Silicon fallback
                result = subprocess.run(
                    ["sysctl", "-n", "hw.model"],
                    capture_output=True,
                    text=True
                )
                cpu_info["model"] = result.stdout.strip()

            # CPU frequency
            result = subprocess.run(
                ["sysctl", "-n", "hw.cpufrequency"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip().isdigit():
                cpu_info["frequency"] = f"{int(result.stdout.strip()) / 1e9:.2f} GHz"

            # Cache (best effort)
            l2 = subprocess.run(["sysctl", "-n", "hw.l2cachesize"], capture_output=True, text=True)
            l3 = subprocess.run(["sysctl", "-n", "hw.l3cachesize"], capture_output=True, text=True)
            if l2.stdout.strip().isdigit() or l3.stdout.strip().isdigit():
                cpu_info["cache"] = f"L2: {int(l2.stdout)/1024/1024:.1f} MB, L3: {int(l3.stdout)/1024/1024:.1f} MB"

            # Apple Silicon process size
            if platform.machine() == "arm64":
                cpu_info["process"] = "5nm / 3nm (Apple Silicon)"
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
            # Try multiple methods to get accurate memory information
            
            # Method 1: Try using PowerShell (more reliable than WMIC)
            try:
                # Get memory details using Get-CimInstance
                ps_cmd = "Get-CimInstance -ClassName Win32_PhysicalMemory | Select-Object Capacity, Speed, ConfiguredClockSpeed, DeviceLocator, SMBIOSMemoryType, PartNumber | ConvertTo-Json"
                result = subprocess.run(["powershell", "-Command", ps_cmd], 
                                     capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0 and result.stdout.strip():
                    # Try to parse PowerShell output as JSON
                    import json
                    try:
                        mem_data = json.loads(result.stdout)
                        # Convert to list if single object is returned
                        if isinstance(mem_data, dict):
                            mem_data = [mem_data]
                            
                        # Process memory data
                        if mem_data:
                            # Parse memory slots info
                            slots = []
                            speeds = []
                            configured_speeds = []
                            mem_types = []
                            part_numbers = []
                            
                            for module in mem_data:
                                # Get capacity
                                if "Capacity" in module and module["Capacity"]:
                                    capacity_gb = int(module["Capacity"]) / (1024**3)
                                    slots.append(f"{capacity_gb:.0f} GB")
                                
                                # Get memory speed
                                if "Speed" in module and module["Speed"]:
                                    speeds.append(f"{module['Speed']} MHz")
                                
                                # Get configured clock speed (often more accurate)
                                if "ConfiguredClockSpeed" in module and module["ConfiguredClockSpeed"]:
                                    configured_speeds.append(f"{module['ConfiguredClockSpeed']} MHz")
                                
                                # Get memory type
                                if "SMBIOSMemoryType" in module and module["SMBIOSMemoryType"]:
                                    mem_type_code = str(module["SMBIOSMemoryType"])
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
                                
                                # Get part number (might contain timing info)
                                if "PartNumber" in module and module["PartNumber"]:
                                    part_num = module["PartNumber"].strip()
                                    if part_num:
                                        part_numbers.append(part_num)
                            
                            # Set memory info based on collected data
                            if slots:
                                memory_info["slots"] = f"{len(slots)} ({', '.join(slots)})"
                            
                            # Prefer configured speeds if available
                            if configured_speeds and len(set(configured_speeds)) == 1:
                                memory_info["speed"] = configured_speeds[0]
                            elif configured_speeds:
                                memory_info["speed"] = ", ".join(configured_speeds)
                            elif speeds and len(set(speeds)) == 1:
                                memory_info["speed"] = speeds[0]
                            elif speeds:
                                memory_info["speed"] = ", ".join(speeds)
                            
                            # Set memory type
                            if mem_types and len(set(mem_types)) == 1 and mem_types[0] != "Unknown":
                                memory_info["type"] = mem_types[0]
                            elif mem_types:
                                memory_info["type"] = ", ".join(set(mem_types))
                            
                            # Try to extract timing info from part numbers
                            if part_numbers:
                                for part in part_numbers:
                                    # Look for common timing patterns in part numbers
                                    timing_match = re.search(r"[^0-9](\d{1,2})-(\d{1,2})-(\d{1,2})(?:-(\d{1,2}))?", part)
                                    if timing_match:
                                        if timing_match.group(4):
                                            memory_info["timings"] = f"CL{timing_match.group(1)}-{timing_match.group(2)}-{timing_match.group(3)}-{timing_match.group(4)}"
                                        else:
                                            memory_info["timings"] = f"CL{timing_match.group(1)}-{timing_match.group(2)}-{timing_match.group(3)}"
                                        break
                                        
                                    # Second pattern attempt 
                                    cl_match = re.search(r"CL(\d{1,2})", part, re.IGNORECASE)
                                    if cl_match:
                                        memory_info["timings"] = f"CL{cl_match.group(1)} (partial)"
                                        break
                    except json.JSONDecodeError:
                        pass
            except (subprocess.SubprocessError, subprocess.TimeoutExpired):
                pass
            
            # Method 2: Fall back to WMIC if PowerShell approach failed
            if memory_info["slots"] == "Unknown":
                # Use the existing WMIC implementation
                result = subprocess.run(["wmic", "memorychip", "get", "Capacity,Speed,DeviceLocator,MemoryType"], 
                                      capture_output=True, text=True)
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
            
            # Method 3: Use Windows Management Instrumentation Command-line (WMIC)
            # to get SPD data if timing info is still unknown
            if memory_info["timings"] == "Unknown":
                try:
                    # Try to get SPD info using WMI
                    ps_cmd = """
                    $SPDInfoClass = Get-WmiObject -Class MSMemory_MemoryDevice
                    $SPDInfoClass | Select-Object DataWidth, TotalWidth, Speed | ConvertTo-Json
                    """
                    result = subprocess.run(["powershell", "-Command", ps_cmd], 
                                         capture_output=True, text=True, timeout=5)
                    
                    if result.returncode == 0 and result.stdout.strip():
                        # Try to determine memory timings from detailed memory specs
                        if memory_info["type"] != "Unknown" and memory_info["speed"] != "Unknown":
                            # Get the speed in MHz
                            speed_match = re.search(r"(\d+)\s*MHz", memory_info["speed"])
                            if speed_match:
                                speed_mhz = int(speed_match.group(1))
                                
                                # Determine memory timings based on type and speed
                                if "DDR4" in memory_info["type"]:
                                    if speed_mhz >= 3600:
                                        memory_info["timings"] = "CL16-18-18-38 (typical)"
                                    elif speed_mhz >= 3200:
                                        memory_info["timings"] = "CL16-18-18-36 (typical)"
                                    elif speed_mhz >= 2666:
                                        memory_info["timings"] = "CL16-18-18-35 (typical)"
                                    else:
                                        memory_info["timings"] = "CL16-16-16-32 (typical)"
                                elif "DDR5" in memory_info["type"]:
                                    if speed_mhz >= 6000:
                                        memory_info["timings"] = "CL40-40-40-76 (typical)"
                                    elif speed_mhz >= 5600:
                                        memory_info["timings"] = "CL36-36-36-76 (typical)"
                                    elif speed_mhz >= 4800:
                                        memory_info["timings"] = "CL34-34-34-68 (typical)"
                                    else:
                                        memory_info["timings"] = "CL30-30-30-60 (typical)"
                                elif "DDR3" in memory_info["type"]:
                                    if speed_mhz >= 2133:
                                        memory_info["timings"] = "CL15-15-15-35 (typical)"
                                    elif speed_mhz >= 1866:
                                        memory_info["timings"] = "CL13-13-13-32 (typical)"
                                    elif speed_mhz >= 1600:
                                        memory_info["timings"] = "CL11-11-11-28 (typical)"
                                    else:
                                        memory_info["timings"] = "CL9-9-9-24 (typical)"
                except (subprocess.SubprocessError, subprocess.TimeoutExpired):
                    pass
                    
            # Method 4: Get memory details from CPU-Z report if available (Windows only)
            if memory_info["type"] == "Unknown" or memory_info["timings"] == "Unknown":
                try:
                    # Check if CPU-Z is installed (common location)
                    cpuz_paths = [
                        os.path.join(os.environ.get('ProgramFiles', ''), 'CPUID\\CPU-Z\\cpuz.exe'),
                        os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'CPUID\\CPU-Z\\cpuz.exe')
                    ]
                    
                    cpuz_installed = any(os.path.exists(path) for path in cpuz_paths)
                    
                    if cpuz_installed:
                        # CPU-Z is installed, we could potentially run it in command line mode
                        # This is a placeholder - CPU-Z CLI options are limited
                        pass
                except:
                    pass
        elif platform.system() == "Darwin":
            mem = psutil.virtual_memory()
            memory_info["slots"] = "Unified Memory"
            memory_info["type"] = "LPDDR (Apple Silicon)" if platform.machine() == "arm64" else "DDR"
            memory_info["speed"] = "Unified (SoC)"
            memory_info["timings"] = "N/A"
        else:
            # The Linux section remains the same
            # For Linux systems
            if os.path.exists("/proc/meminfo"):
                # Try using dmidecode if available
                try:
                    # This requires sudo permissions - may not work without them
                    result = subprocess.run(["sudo", "-n", "dmidecode", "--type", "memory"], capture_output=True, text=True, timeout=10)
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
                except (subprocess.SubprocessError, FileNotFoundError, OSError):
                    pass
                if memory_info["slots"] == "Unknown":
                    memory_info["slots"] = "Unknown (needs root)"
                if memory_info["speed"] == "Unknown":
                    memory_info["speed"] = "Unknown (needs root)"
    except Exception as e:
        pass
    
    return memory_info

def get_fallback_gpus():
    """Detect GPUs without root or NVML (lspci first, then sysfs vendor IDs).

    Returns one entry per card so multi-GPU machines get one line per GPU.
    """
    gpus = []
    if platform.system() == "Linux":
        try:
            result = subprocess.run(["lspci"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if re.search(r"(VGA compatible controller|3D controller|Display controller)", line):
                        addr, _, desc = line.partition(" ")
                        name = desc.split(":", 1)[-1].strip()
                        name = re.sub(r"^.*\[AMD/ATI\]\s*", "", name)
                        name = name.split("(")[0].strip()
                        vram = _read_amd_vram(addr)
                        if vram:
                            name = f"{name} ({vram})"
                        if name and name not in gpus:
                            gpus.append(name)
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        if not gpus:
            vendor_names = {"0x1002": "AMD GPU", "0x10de": "NVIDIA GPU", "0x8086": "Intel GPU"}
            try:
                for card in sorted(os.listdir("/sys/class/drm")):
                    if not re.match(r"card\d+$", card):
                        continue
                    try:
                        with open(f"/sys/class/drm/{card}/device/vendor") as f:
                            vendor = f.read().strip()
                    except OSError:
                        continue
                    name = vendor_names.get(vendor)
                    if name and name not in gpus:
                        gpus.append(name)
            except OSError:
                pass
    return gpus

def _read_amd_vram(pci_addr):
    """VRAM size for amdgpu cards, straight from sysfs (no root needed)."""
    addr = pci_addr if pci_addr.count(":") >= 2 else f"0000:{pci_addr}"
    try:
        with open(f"/sys/bus/pci/devices/{addr}/mem_info_vram_total") as f:
            return bytes_to_readable(int(f.read().strip()))
    except (OSError, ValueError):
        return ""

def get_primary_ip():
    """Best-effort LAN IP without root (UDP connect trick sends no packets)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(1)
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        pass
    try:
        ip = socket.gethostbyname(socket.gethostname())
        return ip if not ip.startswith("127.") else "Not detected"
    except socket.gaierror:
        return "Not detected"

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
        elif platform.system() == "Darwin":
            return "OpenCL supported (Apple framework)"
        else:
            # For Linux
            if os.path.exists("/usr/bin/clinfo"):
                result = subprocess.run(["clinfo", "--version"], capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if "OpenCL" in line:
                            return line.strip()
        
        # Last resort: portable detection through the pyopencl binding
        try:
            import pyopencl as cl
            platforms = cl.get_platforms()
            if platforms:
                return f"{platforms[0].name} ({platforms[0].version})"
        except Exception:
            pass

        return "Not detected"
    except:
        return "Not detected"

def check_vulkan_version():
    try:
        # Try to detect Vulkan with vulkaninfo
        if platform.system() == "Windows":
            result = subprocess.run(["vulkaninfo", "--summary"], capture_output=True, text=True)
        elif platform.system() == "Darwin":
            return "Not supported (use MoltenVK)"
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
    elif platform.system() == "Darwin":
        result = subprocess.run(
            ["sysctl", "-n", "kern.boottime"],
            capture_output=True,
            text=True
        )
        match = re.search(r"sec = (\d+)", result.stdout)
        boot_time = datetime.datetime.fromtimestamp(int(match.group(1))) if match else datetime.datetime.now()
    else:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            boot_time = datetime.datetime.now() - datetime.timedelta(seconds=uptime_seconds)

    uptime = datetime.datetime.now() - boot_time
    days, remainder = divmod(uptime.total_seconds(), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{int(days)}d")
    if hours:
        parts.append(f"{int(hours)}h")
    parts.append(f"{int(minutes)}m")
    return " ".join(parts)

def bytes_to_readable(bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} PB"

# Tux by Joan G. Stark (jgs): compact and detailed variants.
_TUX_SMALL = [
    "       .---.",
    "      /     \\",
    "      \\.o o./",
    "      /`\\_/`\\",
    "     //  _  \\\\",
    "    | \\     )|_",
    "   /`\\_`>  <_/ \\",
    "   \\__/'---'\\__/",
]

_TUX_LARGE = [
    "              ___",
    "           ,-'   '-.",
    "          /  _   _  \\",
    "          | (o)_(o) |",
    "          \\ .-\"\"-.  /",
    "          //`._.-'`\\\\",
    "         //   :    ; \\",
    "        //. - '' -.|  |",
    "       /(    :     |  |",
    "      |  \\__:     ,/  /,",
    "     _;'`,_/'     |`.-' `\\",
    "    )     `\\.___./;     .'",
    "    '.__    )----'\\__.-'",
    "        `\"\"`",
]

# BSD Daemon (Beastie) head, after Felix Lee's classic FreeBSD boot art.
_BSD_DAEMON = [
    "     ,        ,",
    "    /(        )`",
    "    \\ \\___   / |",
    "    /-  _   `-/  '",
    "   ( /\\/ \\  \\   /\\",
    "    / /   |  `    \\",
    "    O O )  /    |",
    "    `-^--' `<     '",
]

def get_ascii_logo(system, max_width=None):
    logos = {
        "Windows": [
            "    _____  _____",
            "   |     ||     |",
            "   |     ||     |",
            "   |_____||_____|",
            "    _____  _____",
            "   |     ||     |",
            "   |     ||     |",
            "   |_____||_____|",
        ],
        "Linux": [],
        "Darwin": [
            "        .:'",
            "    __ :'__",
            " .'`  `-'  ``.",
            ":          .-'",
            ":         :",
            " `.__.-.__.'",
        ],
    }
    
    default_logo = [
            "     ________",
            "    |  ____  |",
            "    | |    | |",
            "    | |____| |",
            "    |________|",
            "       |  |",
            "     __|__|__",
            "    |________|",
        ]
    
    if system == "Linux":
        if max_width is not None:
            for art in (_TUX_LARGE, _TUX_SMALL):
                if max(len(line) for line in art) <= max_width:
                    return art
        return _TUX_SMALL
    if system in ("FreeBSD", "OpenBSD", "NetBSD", "DragonFly"):
        return _BSD_DAEMON
    return logos.get(system, default_logo)

# Below this many columns the logo no longer sits beside the info block.
_MIN_INFO_WIDTH = 24

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

def _display_width(text):
    """Width of a plain string in terminal cells (CJK glyphs count as two)."""
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in text)

def _visible_len(text):
    """Display width of a colored string (ANSI escapes do not count)."""
    return _display_width(_ANSI_RE.sub("", text))

def _truncate_to_width(text, max_width):
    """Cut *text* to *max_width* cells, keeping colors and adding an ellipsis."""
    if max_width <= 0 or _visible_len(text) <= max_width:
        return text
    budget = max(max_width - 1, 0)  # room for the ellipsis
    out = []
    width = 0
    pos = 0
    while pos < len(text):
        if text[pos] == "\x1b":
            match = _ANSI_RE.match(text, pos)
            if match:
                out.append(match.group(0))
                pos = match.end()
                continue
        cell = 2 if unicodedata.east_asian_width(text[pos]) in ("W", "F") else 1
        if width + cell > budget:
            break
        out.append(text[pos])
        width += cell
        pos += 1
    return "".join(out) + "…" + Style.RESET_ALL

# Aliases accepted by --logo, mapped to platform.system() names.
_LOGO_ALIASES = {
    "linux": "Linux", "tux": "Linux",
    "windows": "Windows", "win": "Windows",
    "macos": "Darwin", "mac": "Darwin", "darwin": "Darwin", "osx": "Darwin", "apple": "Darwin",
    "bsd": "FreeBSD", "freebsd": "FreeBSD", "openbsd": "OpenBSD",
    "netbsd": "NetBSD", "dragonfly": "DragonFly",
    "default": "Unknown", "unknown": "Unknown", "other": "Unknown",
}

def _resolve_logo_os(value):
    """Map a --logo argument to a platform name, or fail with a clear error."""
    if value in ("Linux", "Windows", "Darwin", "FreeBSD", "OpenBSD", "NetBSD", "DragonFly"):
        return value
    key = value.strip().lower()
    if key in _LOGO_ALIASES:
        return _LOGO_ALIASES[key]
    raise SystemExit(
        f"pysinfo: unknown logo '{value}'; choose from: "
        + ", ".join(sorted(set(_LOGO_ALIASES)))
    )

def _ensure_utf8_stdout():
    """Switch stdout to UTF-8 so the box-drawing output never crashes.

    On Windows with a legacy console code page (e.g. cp1252) printing the
    header box raises UnicodeEncodeError. Reconfiguring to UTF-8 keeps the
    output intact; a console without the glyphs shows replacements instead
    of the program dying. Streams that cannot be reconfigured are left
    alone.
    """
    stream = sys.stdout
    if stream is None:
        return
    try:
        stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError, ValueError):
        pass


def print_system_info(logo_os=None):
    _ensure_utf8_stdout()
    colorama.init()
    system_info = get_system_info()
    # --logo can force another platform's logo/colors (useful for testing)
    ui_os = _resolve_logo_os(logo_os) if logo_os else platform.system()
    
    # ANSI Color codes for different OS
    color = Fore.CYAN  # Default color
    if ui_os == "Windows":
        color = Fore.BLUE
    elif ui_os == "Linux":
        color = Fore.GREEN
    elif ui_os == "Darwin":
        color = Fore.WHITE
    
    # Fit everything into the current terminal width so nothing wraps
    cols = max(shutil.get_terminal_size().columns, 20)
    spacing = 4

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
        f"{color}CPU Current Freq:{Style.RESET_ALL} {system_info['cpu_freq']}",
        f"{color}CPU Cores:{Style.RESET_ALL} {system_info['cpu_cores']}",
        f"{color}CPU Usage:{Style.RESET_ALL} {system_info['cpu_usage']}",
    ]

    # One line per GPU, so multi-card machines stay readable
    gpus = system_info.get("gpus") or []
    for i, gpu in enumerate(gpus, 1):
        label = "GPU" if len(gpus) == 1 else f"GPU {i}"
        data_lines.append(f"{color}{label}:{Style.RESET_ALL} {gpu}")
    if not gpus:
        data_lines.append(f"{color}GPU:{Style.RESET_ALL} Not detected")

    data_lines += [
        f"{color}Memory:{Style.RESET_ALL} {system_info['memory']}",
        f"{color}Memory Slots:{Style.RESET_ALL} {system_info['memory_slots']}",
        f"{color}Memory Speed:{Style.RESET_ALL} {system_info['memory_speed']}",
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
    
    # Drop lines whose value needs root but was not available (e.g. SMBIOS)
    data_lines = [line for line in data_lines if "Unknown (needs root)" not in line]
    info_w = max(_visible_len(line) for line in data_lines)

    # Pick the largest logo that still leaves the info block fully visible
    ascii_logo = get_ascii_logo(ui_os, max_width=cols - info_w - spacing - 1)
    logo_width = max(len(line) for line in ascii_logo)
    side_by_side = cols >= logo_width + spacing + _MIN_INFO_WIDTH
    info_budget = max((cols - logo_width - spacing if side_by_side else cols) - 1, 8)

    # Header (box shrinks with the terminal)
    box_inner = max(min(65, cols) - 2, 4)
    title = _truncate_to_width("PySinfo: A Python Tool to Get System Infomation", box_inner - 2)
    pad = max(box_inner - _visible_len(title), 0)
    left = pad // 2
    right = pad - left
    print(f"\n{Style.BRIGHT}{Back.BLACK}{color}╒{'═' * box_inner}╕{Style.RESET_ALL}")
    print(f"{Style.BRIGHT}{Back.BLACK}{color}│{' ' * left}{title}{' ' * right}│{Style.RESET_ALL}")
    print(f"{Style.BRIGHT}{Back.BLACK}{color}╘{'═' * box_inner}╛{Style.RESET_ALL}\n")

    # Everything must fit the physical width; rows sharing a line with the logo
    # give up extra width, the rest of the block uses the full terminal width.
    logo_length = len(ascii_logo)
    data_lines = [_truncate_to_width(line, max(cols - 1, 8)) for line in data_lines]
    if side_by_side:
        for i in range(min(logo_length, len(data_lines))):
            data_lines[i] = _truncate_to_width(data_lines[i], info_budget)

    if not side_by_side:
        # Terminal too narrow for logo + info: stack the logo above the block
        for logo_line in ascii_logo:
            print(f"{color}{_truncate_to_width(logo_line, cols)}{Style.RESET_ALL}")
        print()
        for info_line in data_lines:
            print(info_line)
    else:
        # Info left-aligned, logo to the right of the OS block
        info_w = max(_visible_len(line) for line in data_lines)
        logo_col = max(min(info_w, cols - logo_width - spacing - 1), 0)
        for i, info_line in enumerate(data_lines):
            if i < logo_length:
                pad = " " * max(logo_col - _visible_len(info_line), 0)
                print(f"{info_line}{pad}{' ' * spacing}{color}{ascii_logo[i].ljust(logo_width)}{Style.RESET_ALL}")
            else:
                print(info_line)
    
    # Print color blocks across the full terminal width
    palette = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN, Fore.WHITE]
    n_blocks, remainder = divmod(cols, 6)
    bar = "".join(f"{palette[i % len(palette)]}██████{Style.RESET_ALL}" for i in range(max(n_blocks, 1)))
    if remainder and n_blocks:
        bar += f"{palette[n_blocks % len(palette)]}{'█' * remainder}{Style.RESET_ALL}"
    print("\n" + bar)
    
    # Footer
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    footer = _truncate_to_width(f"Report generated on: {current_time}", max(cols, 8))
    print(f"\n{Style.DIM}{footer}{Style.RESET_ALL}")

if __name__ == "__main__":
    print_system_info()