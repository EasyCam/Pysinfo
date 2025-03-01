// C_SysInfo - A simple system information tool written in C
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Platform-specific includes
#ifdef _WIN32
    #include <windows.h>
    #include <intrin.h>
    #include <powrprof.h>
    #include <winternl.h>
    #pragma comment(lib, "powrprof.lib")
    #pragma comment(lib, "ntdll.lib")
#else
    #include <unistd.h>
    #include <sys/utsname.h>
    #include <sys/sysinfo.h>
    #include <sys/statvfs.h>
    #include <pwd.h>
    #include <X11/Xlib.h>
#endif

#define ANSI_COLOR_RED     "\x1b[31m"
#define ANSI_COLOR_GREEN   "\x1b[32m"
#define ANSI_COLOR_YELLOW  "\x1b[33m"
#define ANSI_COLOR_BLUE    "\x1b[34m"
#define ANSI_COLOR_MAGENTA "\x1b[35m"
#define ANSI_COLOR_CYAN    "\x1b[36m"
#define ANSI_COLOR_RESET   "\x1b[0m"
#define ANSI_BOLD          "\x1b[1m"

#define BUFFER_SIZE 256

typedef struct {
    char username[BUFFER_SIZE];
    char hostname[BUFFER_SIZE];
    char os_name[BUFFER_SIZE];
    char kernel_version[BUFFER_SIZE];
    char uptime[64];
    char shell[BUFFER_SIZE];
    char resolution[64];
    char de[BUFFER_SIZE];
    char wm[BUFFER_SIZE];
    char cpu[BUFFER_SIZE];
    char gpu[BUFFER_SIZE];
    
    #ifdef _WIN32
        MEMORYSTATUSEX memory;
    #else
        unsigned long long total_mem;
        unsigned long long used_mem;
    #endif
    
    char disk_info[BUFFER_SIZE];
    
    #ifdef _WIN32
        SYSTEM_POWER_STATUS power_status;
    #else
        int battery_percentage;
        char battery_status[64];
    #endif
    
    char motherboard[BUFFER_SIZE];
    char bios_version[BUFFER_SIZE];
} SystemInfo;

// Forward declarations
void get_system_info(SystemInfo *info);
void display_system_info(SystemInfo *info);

// Helper function to execute a command and get output
char* execute_command(const char* cmd) {
    static char buffer[1024];
    FILE* pipe;
    
    #ifdef _WIN32
        pipe = _popen(cmd, "r");
    #else
        pipe = popen(cmd, "r");
    #endif
    
    if (!pipe) return NULL;
    
    buffer[0] = '\0';
    if (fgets(buffer, sizeof(buffer), pipe) != NULL) {
        // Remove trailing newline
        buffer[strcspn(buffer, "\r\n")] = 0;
    }
    
    #ifdef _WIN32
        _pclose(pipe);
    #else
        pclose(pipe);
    #endif
    
    return buffer;
}

// Read a file into a buffer (for Linux)
#ifndef _WIN32
char* read_file_content(const char* filename) {
    static char buffer[1024];
    FILE* file = fopen(filename, "r");
    if (!file) return NULL;
    
    buffer[0] = '\0';
    if (fgets(buffer, sizeof(buffer), file) != NULL) {
        buffer[strcspn(buffer, "\r\n")] = 0;
    }
    fclose(file);
    return buffer;
}
#endif

// Main function
int main() {
    #ifdef _WIN32
        // Enable ANSI escape sequences in Windows terminal
        HANDLE hOut = GetStdHandle(STD_OUTPUT_HANDLE);
        DWORD dwMode = 0;
        GetConsoleMode(hOut, &dwMode);
        dwMode |= 0x0004;
        SetConsoleMode(hOut, dwMode);
    #endif

    SystemInfo info;
    get_system_info(&info);
    display_system_info(&info);
    
    return 0;
}

#ifdef _WIN32
// Windows-specific system information gathering
// Get CPU info
void get_cpu_info(char* cpu_info, size_t max_len) {
    int cpu_info_array[4] = {-1};
    char cpu_brand[64];
    memset(cpu_brand, 0, sizeof(cpu_brand));

    __cpuid(cpu_info_array, 0x80000002);
    memcpy(cpu_brand, cpu_info_array, sizeof(cpu_info_array));

    __cpuid(cpu_info_array, 0x80000003);
    memcpy(cpu_brand + 16, cpu_info_array, sizeof(cpu_info_array));

    __cpuid(cpu_info_array, 0x80000004);
    memcpy(cpu_brand + 32, cpu_info_array, sizeof(cpu_info_array));

    // Get logical core count
    SYSTEM_INFO sysInfo;
    GetSystemInfo(&sysInfo);
    
    snprintf(cpu_info, max_len, "%s (%d cores)", cpu_brand, sysInfo.dwNumberOfProcessors);
}

// Get GPU info
void get_gpu_info(char* gpu_info, size_t max_len) {
    const char* cmd = "wmic path win32_VideoController get Name /value";
    FILE* pipe = _popen(cmd, "r");
    
    if (pipe) {
        char line[256];
        while (fgets(line, sizeof(line), pipe) != NULL) {
            if (strstr(line, "Name=")) {
                strncpy(gpu_info, line + 5, max_len - 1);
                gpu_info[strcspn(gpu_info, "\r\n")] = 0;
                break;
            }
        }
        _pclose(pipe);
    } else {
        strncpy(gpu_info, "Unknown GPU", max_len - 1);
    }
}

// Get motherboard info
void get_motherboard_info(char* motherboard, size_t max_len) {
    const char* cmd = "wmic baseboard get Manufacturer,Product /value";
    FILE* pipe = _popen(cmd, "r");
    char mfr[128] = "", product[128] = "";
    
    if (pipe) {
        char line[256];
        while (fgets(line, sizeof(line), pipe) != NULL) {
            line[strcspn(line, "\r\n")] = 0;
            if (strstr(line, "Manufacturer=")) {
                strncpy(mfr, line + 13, sizeof(mfr) - 1);
            }
            if (strstr(line, "Product=")) {
                strncpy(product, line + 8, sizeof(product) - 1);
            }
        }
        _pclose(pipe);
        snprintf(motherboard, max_len, "%s %s", mfr, product);
    } else {
        strncpy(motherboard, "Unknown", max_len - 1);
    }
}

// Get BIOS info
void get_bios_info(char* bios, size_t max_len) {
    const char* cmd = "wmic bios get Manufacturer,SMBIOSBIOSVersion /value";
    FILE* pipe = _popen(cmd, "r");
    char mfr[128] = "", version[128] = "";
    
    if (pipe) {
        char line[256];
        while (fgets(line, sizeof(line), pipe) != NULL) {
            line[strcspn(line, "\r\n")] = 0;
            if (strstr(line, "Manufacturer=")) {
                strncpy(mfr, line + 13, sizeof(mfr) - 1);
            }
            if (strstr(line, "SMBIOSBIOSVersion=")) {
                strncpy(version, line + 19, sizeof(version) - 1);
            }
        }
        _pclose(pipe);
        snprintf(bios, max_len, "%s %s", mfr, version);
    } else {
        strncpy(bios, "Unknown", max_len - 1);
    }
}

// Get disk information
void get_disk_info(char* disk_info, size_t max_len) {
    const char* cmd = "wmic logicaldisk where DeviceID='C:' get Size,FreeSpace /value";
    FILE* pipe = _popen(cmd, "r");
    char size_str[64] = "", free_str[64] = "";
    
    if (pipe) {
        char line[256];
        while (fgets(line, sizeof(line), pipe) != NULL) {
            line[strcspn(line, "\r\n")] = 0;
            if (strstr(line, "FreeSpace=")) {
                strncpy(free_str, line + 10, sizeof(free_str) - 1);
            }
            if (strstr(line, "Size=")) {
                strncpy(size_str, line + 5, sizeof(size_str) - 1);
            }
        }
        _pclose(pipe);
        
        if (strlen(size_str) > 0 && strlen(free_str) > 0) {
            unsigned long long total = strtoull(size_str, NULL, 10) / (1024 * 1024 * 1024);
            unsigned long long free = strtoull(free_str, NULL, 10) / (1024 * 1024 * 1024);
            unsigned long long used = total - free;
            snprintf(disk_info, max_len, "%lluGB / %lluGB (%llu%% used)", 
                     used, total, (used * 100) / total);
        } else {
            strncpy(disk_info, "Unknown", max_len - 1);
        }
    } else {
        strncpy(disk_info, "Unknown", max_len - 1);
    }
}

// Get system uptime
void get_uptime(char* uptime, size_t max_len) {
    DWORD tickCount = GetTickCount();
    DWORD seconds = tickCount / 1000;
    DWORD minutes = seconds / 60;
    DWORD hours = minutes / 60;
    DWORD days = hours / 24;
    
    hours %= 24;
    minutes %= 60;
    
    if (days > 0) {
        snprintf(uptime, max_len, "%d days, %d hours, %d mins", days, hours, minutes);
    } else {
        snprintf(uptime, max_len, "%d hours, %d mins", hours, minutes);
    }
}


// Windows-specific system information gathering
void get_system_info(SystemInfo *info) {
    // Username and hostname
    DWORD size = sizeof(info->username);
    GetUserName(info->username, &size);
    
    size = sizeof(info->hostname);
    GetComputerName(info->hostname, &size);
    
    // OS information
    OSVERSIONINFOEX osvi;
    ZeroMemory(&osvi, sizeof(OSVERSIONINFOEX));
    osvi.dwOSVersionInfoSize = sizeof(OSVERSIONINFOEX);
    
    // Using RtlGetVersion since GetVersionEx is deprecated
    typedef NTSTATUS (WINAPI* pRtlGetVersion)(PRTL_OSVERSIONINFOW);
    pRtlGetVersion RtlGetVersion;
    RtlGetVersion = (pRtlGetVersion)GetProcAddress(GetModuleHandle(TEXT("ntdll.dll")), "RtlGetVersion");
    if (RtlGetVersion) {
        RtlGetVersion((PRTL_OSVERSIONINFOW)&osvi);
    }
    
    // Determine Windows version
    if (osvi.dwMajorVersion == 10) {
        strcpy(info->os_name, "Windows 10/11");
    } else if (osvi.dwMajorVersion == 6) {
        if (osvi.dwMinorVersion == 3)
            strcpy(info->os_name, "Windows 8.1");
        else if (osvi.dwMinorVersion == 2)
            strcpy(info->os_name, "Windows 8");
        else if (osvi.dwMinorVersion == 1)
            strcpy(info->os_name, "Windows 7");
        else
            strcpy(info->os_name, "Windows Vista");
    } else {
        strcpy(info->os_name, "Windows");
    }
    
    // Architecture
    SYSTEM_INFO sysInfo;
    GetSystemInfo(&sysInfo);
    if (sysInfo.wProcessorArchitecture == PROCESSOR_ARCHITECTURE_AMD64) {
        strcat(info->os_name, " (x86_64)");
    } else {
        strcat(info->os_name, " (x86)");
    }
    
    // Kernel version
    snprintf(info->kernel_version, sizeof(info->kernel_version), "NT %d.%d.%d",
             osvi.dwMajorVersion, osvi.dwMinorVersion, osvi.dwBuildNumber);
    
    // Uptime
    get_uptime(info->uptime, sizeof(info->uptime));
    
    // Shell info - default to cmd for Windows
    strcpy(info->shell, "cmd.exe");
    
    // Desktop environment
    strcpy(info->de, "Windows Explorer");
    
    // Window manager
    strcpy(info->wm, "DWM");
        
    // CPU info
    get_cpu_info(info->cpu, sizeof(info->cpu));
    
    // GPU info
    get_gpu_info(info->gpu, sizeof(info->gpu));
    
    // Memory info
    info->memory.dwLength = sizeof(MEMORYSTATUSEX);
    GlobalMemoryStatusEx(&info->memory);
    
    // Disk info
    get_disk_info(info->disk_info, sizeof(info->disk_info));
    
    // Power status
    GetSystemPowerStatus(&info->power_status);
    
    // Motherboard and BIOS
    get_motherboard_info(info->motherboard, sizeof(info->motherboard));
    get_bios_info(info->bios_version, sizeof(info->bios_version));
}

#else
// Linux-specific system information gathering

// Get CPU info
void get_cpu_info(char* cpu_info, size_t max_len) {
    FILE* cpuinfo = fopen("/proc/cpuinfo", "r");
    if (!cpuinfo) {
        strncpy(cpu_info, "Unknown", max_len - 1);
        return;
    }
    
    char line[256];
    char model_name[256] = "";
    int cpu_count = 0;
    
    while (fgets(line, sizeof(line), cpuinfo)) {
        if (strstr(line, "model name")) {
            char* value = strchr(line, ':');
            if (value) {
                value++; // Skip the colon
                while (*value == ' ') value++; // Skip spaces
                strncpy(model_name, value, sizeof(model_name) - 1);
                model_name[strcspn(model_name, "\n")] = 0;
            }
        }
        if (strstr(line, "processor")) {
            cpu_count++;
        }
    }
    
    fclose(cpuinfo);
    snprintf(cpu_info, max_len, "%s (%d cores)", model_name, cpu_count);
}

// Get GPU info
void get_gpu_info(char* gpu_info, size_t max_len) {
    const char* cmd = "lspci | grep -i vga | cut -d: -f3";
    char* result = execute_command(cmd);
    
    if (result && strlen(result) > 0) {
        strncpy(gpu_info, result, max_len - 1);
    } else {
        strncpy(gpu_info, "Unknown", max_len - 1);
    }
}

// Get motherboard info
void get_motherboard_info(char* motherboard, size_t max_len) {
    char vendor[128] = "", name[128] = "";
    char* vendor_result = read_file_content("/sys/class/dmi/id/board_vendor");
    char* name_result = read_file_content("/sys/class/dmi/id/board_name");
    
    if (vendor_result) strncpy(vendor, vendor_result, sizeof(vendor) - 1);
    if (name_result) strncpy(name, name_result, sizeof(name) - 1);
    
    if (strlen(vendor) > 0 || strlen(name) > 0) {
        snprintf(motherboard, max_len, "%s %s", vendor, name);
    } else {
        strncpy(motherboard, "Unknown", max_len - 1);
    }
}

// Get BIOS info
void get_bios_info(char* bios, size_t max_len) {
    char vendor[128] = "", version[128] = "";
    char* vendor_result = read_file_content("/sys/class/dmi/id/bios_vendor");
    char* version_result = read_file_content("/sys/class/dmi/id/bios_version");
    
    if (vendor_result) strncpy(vendor, vendor_result, sizeof(vendor) - 1);
    if (version_result) strncpy(version, version_result, sizeof(version) - 1);
    
    if (strlen(vendor) > 0 || strlen(version) > 0) {
        snprintf(bios, max_len, "%s %s", vendor, version);
    } else {
        strncpy(bios, "Unknown", max_len - 1);
    }
}

// Get disk information
void get_disk_info(char* disk_info, size_t max_len) {
    struct statvfs fs_info;
    
    if (statvfs("/", &fs_info) == 0) {
        unsigned long long total = (fs_info.f_blocks * fs_info.f_frsize) / (1024 * 1024 * 1024);
        unsigned long long free = (fs_info.f_bfree * fs_info.f_frsize) / (1024 * 1024 * 1024);
        unsigned long long used = total - free;
        unsigned long long use_percent = (used * 100) / (used + free);
        
        snprintf(disk_info, max_len, "%lluGB / %lluGB (%llu%% used)", 
                used, total, use_percent);
    } else {
        strncpy(disk_info, "Unknown", max_len - 1);
    }
}

// Get system uptime
void get_uptime(char* uptime_str, size_t max_len) {
    struct sysinfo info;
    
    if (sysinfo(&info) == 0) {
        long uptime = info.uptime;
        int days = uptime / (60*60*24);
        int hours = (uptime % (60*60*24)) / (60*60);
        int mins = ((uptime % (60*60*24)) % (60*60)) / 60;
        
        if (days > 0) {
            snprintf(uptime_str, max_len, "%d days, %d hours, %d mins", days, hours, mins);
        } else {
            snprintf(uptime_str, max_len, "%d hours, %d mins", hours, mins);
        }
    } else {
        strncpy(uptime_str, "Unknown", max_len - 1);
    }
}


// Get desktop environment
void get_desktop_env(char* de, size_t max_len) {
    const char* xdg_desktop = getenv("XDG_CURRENT_DESKTOP");
    const char* desktop_session = getenv("DESKTOP_SESSION");
    
    if (xdg_desktop) {
        strncpy(de, xdg_desktop, max_len - 1);
    } else if (desktop_session) {
        strncpy(de, desktop_session, max_len - 1);
    } else {
        strncpy(de, "Unknown", max_len - 1);
    }
}

// Get window manager
void get_window_manager(char* wm, size_t max_len) {
    // Try to detect window manager - this is a simplified approach
    const char* cmd = "wmctrl -m 2>/dev/null | grep Name: | cut -d' ' -f2-";
    char* result = execute_command(cmd);
    
    if (result && strlen(result) > 0) {
        strncpy(wm, result, max_len - 1);
    } else {
        strncpy(wm, "Unknown", max_len - 1);
    }
}

// Get battery info
void get_battery_info(int* percentage, char* status, size_t max_len) {
    char* capacity = read_file_content("/sys/class/power_supply/BAT0/capacity");
    char* status_str = read_file_content("/sys/class/power_supply/BAT0/status");
    
    if (capacity) {
        *percentage = atoi(capacity);
    } else {
        *percentage = -1;
    }
    
    if (status_str) {
        strncpy(status, status_str, max_len - 1);
    } else {
        strncpy(status, "Unknown", max_len - 1);
    }
}

// Linux-specific system information gathering
void get_system_info(SystemInfo *info) {
    struct utsname system_info;
    
    // Username and hostname
    struct passwd *pw = getpwuid(getuid());
    if (pw) {
        strncpy(info->username, pw->pw_name, sizeof(info->username) - 1);
    } else {
        strcpy(info->username, "unknown");
    }
    
    if (gethostname(info->hostname, sizeof(info->hostname)) != 0) {
        strcpy(info->hostname, "unknown");
    }
    
    // OS information
    if (uname(&system_info) == 0) {
        // Read distribution name from /etc/os-release
        FILE* os_release = fopen("/etc/os-release", "r");
        if (os_release) {
            char line[256];
            while (fgets(line, sizeof(line), os_release)) {
                if (strncmp(line, "PRETTY_NAME=", 12) == 0) {
                    char* name = line + 12;
                    // Remove quotes if present
                    if (name[0] == '"') {
                        name++;
                        name[strcspn(name, "\"")] = 0;
                    }
                    name[strcspn(name, "\n")] = 0;
                    strncpy(info->os_name, name, sizeof(info->os_name) - 1);
                    break;
                }
            }
            fclose(os_release);
        } else {
            strncpy(info->os_name, system_info.sysname, sizeof(info->os_name) - 1);
        }
        
        // Add architecture
        if (strlen(info->os_name) > 0) {
            char arch[32];
            snprintf(arch, sizeof(arch), " (%s)", system_info.machine);
            strncat(info->os_name, arch, sizeof(info->os_name) - strlen(info->os_name) - 1);
        }
        
        // Kernel version
        snprintf(info->kernel_version, sizeof(info->kernel_version), "%s %s", 
                system_info.sysname, system_info.release);
    } else {
        strcpy(info->os_name, "Unknown Linux");
        strcpy(info->kernel_version, "Unknown");
    }
    
    // Uptime
    get_uptime(info->uptime, sizeof(info->uptime));
    
    // Shell info
    char* shell_env = getenv("SHELL");
    if (shell_env) {
        strcpy(info->shell, shell_env);
    } else {
        strcpy(info->shell, "/bin/bash");
    }
    
    // Desktop environment
    get_desktop_env(info->de, sizeof(info->de));
    
    // Window manager
    get_window_manager(info->wm, sizeof(info->wm));
    
    // CPU info
    get_cpu_info(info->cpu, sizeof(info->cpu));
    
    // GPU info
    get_gpu_info(info->gpu, sizeof(info->gpu));
    
    // Memory info
    struct sysinfo si;
    if (sysinfo(&si) == 0) {
        info->total_mem = si.totalram / (1024 * 1024);
        info->used_mem = (si.totalram - si.freeram - si.bufferram) / (1024 * 1024);
    } else {
        info->total_mem = 0;
        info->used_mem = 0;
    }
    
    // Disk info
    get_disk_info(info->disk_info, sizeof(info->disk_info));
    
    // Battery info
    get_battery_info(&info->battery_percentage, info->battery_status, sizeof(info->battery_status));
    
    // Motherboard and BIOS
    get_motherboard_info(info->motherboard, sizeof(info->motherboard));
    get_bios_info(info->bios_version, sizeof(info->bios_version));
}
#endif

// Display system information
void display_system_info(SystemInfo *info) {
    printf("%s@%s\n", info->username, info->hostname);
    printf("----------------\n");
    printf("    C_SysInfo   \n");
    printf("----------------\n");
    
    printf(ANSI_COLOR_RED ANSI_BOLD "OS: " ANSI_COLOR_RESET "%s\n", info->os_name);
    printf(ANSI_COLOR_RED ANSI_BOLD "Kernel: " ANSI_COLOR_RESET "%s\n", info->kernel_version);
    printf(ANSI_COLOR_RED ANSI_BOLD "Uptime: " ANSI_COLOR_RESET "%s\n", info->uptime);
    printf(ANSI_COLOR_RED ANSI_BOLD "Shell: " ANSI_COLOR_RESET "%s\n", info->shell);
    printf(ANSI_COLOR_RED ANSI_BOLD "DE: " ANSI_COLOR_RESET "%s\n", info->de);
    printf(ANSI_COLOR_RED ANSI_BOLD "WM: " ANSI_COLOR_RESET "%s\n", info->wm);
    printf(ANSI_COLOR_RED ANSI_BOLD "CPU: " ANSI_COLOR_RESET "%s\n", info->cpu);
    printf(ANSI_COLOR_RED ANSI_BOLD "GPU: " ANSI_COLOR_RESET "%s\n", info->gpu);

    // Memory
    #ifdef _WIN32
        DWORDLONG total_mem_mb = info->memory.ullTotalPhys / (1024 * 1024);
        DWORDLONG used_mem_mb = (info->memory.ullTotalPhys - info->memory.ullAvailPhys) / (1024 * 1024);
        DWORDLONG total_mem_gb = total_mem_mb / 1024;
        DWORDLONG used_mem_gb = used_mem_mb / 1024;

        printf(ANSI_COLOR_RED ANSI_BOLD "Memory: " ANSI_COLOR_RESET "%lld MB / %lld MB (%.1f GB / %.1f GB)\n",
               used_mem_mb, total_mem_mb, (float)used_mem_gb, (float)total_mem_gb);
    #else
        unsigned long long total_mem_mb = info->total_mem;
        unsigned long long used_mem_mb = info->used_mem;
        float total_mem_gb = (float)total_mem_mb / 1024;
        float used_mem_gb = (float)used_mem_mb / 1024;

        printf(ANSI_COLOR_RED ANSI_BOLD "Memory: " ANSI_COLOR_RESET "%llu MB / %llu MB (%.1f GB / %.1f GB)\n",
               used_mem_mb, total_mem_mb, used_mem_gb, total_mem_gb);
    #endif
    
    #ifdef _WIN32
        printf(ANSI_COLOR_RED ANSI_BOLD "Disk (C:): " ANSI_COLOR_RESET "%s\n", info->disk_info);
    #else
        printf(ANSI_COLOR_RED ANSI_BOLD "Disk (/): " ANSI_COLOR_RESET "%s\n", info->disk_info);
    #endif
    
    // Battery status
    #ifdef _WIN32
        if (info->power_status.BatteryFlag != 128) { // 128 means no battery
            int battery_percentage = info->power_status.BatteryLifePercent;
            const char* power_status = (info->power_status.ACLineStatus == 1) ? "Charging" : "Discharging";
            printf(ANSI_COLOR_RED ANSI_BOLD "Battery: " ANSI_COLOR_RESET "%d%% (%s)\n", 
                   battery_percentage, power_status);
        }
    #else
        if (info->battery_percentage >= 0) {
            printf(ANSI_COLOR_RED ANSI_BOLD "Battery: " ANSI_COLOR_RESET "%d%% (%s)\n", 
                   info->battery_percentage, info->battery_status);
        }
    #endif

    printf(ANSI_COLOR_RED ANSI_BOLD "Motherboard: " ANSI_COLOR_RESET "%s\n", info->motherboard);
    printf(ANSI_COLOR_RED ANSI_BOLD "BIOS: " ANSI_COLOR_RESET "%s\n", info->bios_version);
}