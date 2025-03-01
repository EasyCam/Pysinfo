#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include <intrin.h>
#include <powrprof.h>
#include <winternl.h>

#pragma comment(lib, "powrprof.lib")
#pragma comment(lib, "ntdll.lib")

#define ANSI_COLOR_RED     "\x1b[31m"
#define ANSI_COLOR_GREEN   "\x1b[32m"
#define ANSI_COLOR_YELLOW  "\x1b[33m"
#define ANSI_COLOR_BLUE    "\x1b[34m"
#define ANSI_COLOR_MAGENTA "\x1b[35m"
#define ANSI_COLOR_CYAN    "\x1b[36m"
#define ANSI_COLOR_RESET   "\x1b[0m"
#define ANSI_BOLD          "\x1b[1m"

typedef struct {
    char username[256];
    char hostname[256];
    char os_name[256];
    char kernel_version[256];
    char uptime[64];
    char shell[256];
    char resolution[64];
    char de[256];
    char wm[256];
    char cpu[256];
    char gpu[256];
    MEMORYSTATUSEX memory;
    char disk_info[256];
    SYSTEM_POWER_STATUS power_status;
    char motherboard[256];
    char bios_version[256];
} SystemInfo;

// Forward declarations
void get_system_info(SystemInfo *info);
void display_ascii_art(SystemInfo *info);
void display_system_info(SystemInfo *info);

// Main function
int main() {
    // Enable ANSI escape sequences in Windows terminal
    HANDLE hOut = GetStdHandle(STD_OUTPUT_HANDLE);
    DWORD dwMode = 0;
    GetConsoleMode(hOut, &dwMode);
    dwMode |= 0x0004;
    SetConsoleMode(hOut, dwMode);

    SystemInfo info;
    get_system_info(&info);
    
    display_ascii_art(&info);
    display_system_info(&info);
    
    return 0;
}

// Helper function to execute a command and get output
char* execute_command(const char* cmd) {
    static char buffer[1024];
    FILE* pipe = _popen(cmd, "r");
    if (!pipe) return NULL;
    
    buffer[0] = '\0';
    if (fgets(buffer, sizeof(buffer), pipe) != NULL) {
        // Remove trailing newline
        buffer[strcspn(buffer, "\n")] = 0;
    }
    _pclose(pipe);
    return buffer;
}

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

// Get screen resolution
void get_resolution(char* resolution, size_t max_len) {
    int width = GetSystemMetrics(SM_CXSCREEN);
    int height = GetSystemMetrics(SM_CYSCREEN);
    snprintf(resolution, max_len, "%dx%d", width, height);
}

// Populate system information
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
    
    // Screen resolution
    get_resolution(info->resolution, sizeof(info->resolution));
    
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

// Display ASCII art logo
void display_ascii_art(SystemInfo *info) {
    printf(ANSI_COLOR_BLUE ANSI_BOLD);
    printf("                                  .\n");
    printf("                                  .\n");
    printf("         ,,,,,                    .\n");
    printf("        #######,                  .\n");
    printf("       ########'                  .       %s@%s\n", info->username, info->hostname);
    printf("      ########'                   .       %s\n", "----------------");
    printf("     ########'            #####   .       \n");
    printf("    ########'     #######         .       \n");
    printf("   ########'     #########        .       \n");
    printf("  ########'      ##########       .       \n");
    printf(" ########'       ###########      .       \n");
    printf("########'        ############     .       \n");
    printf("########         ############     .       \n");
    printf("########         ############     .       \n");
    printf("                                  .\n");
    printf(ANSI_COLOR_RESET "\n");
}

// Display system information
void display_system_info(SystemInfo *info) {
    printf(ANSI_COLOR_RED ANSI_BOLD "OS: " ANSI_COLOR_RESET "%s\n", info->os_name);
    printf(ANSI_COLOR_RED ANSI_BOLD "Kernel: " ANSI_COLOR_RESET "%s\n", info->kernel_version);
    printf(ANSI_COLOR_RED ANSI_BOLD "Uptime: " ANSI_COLOR_RESET "%s\n", info->uptime);
    printf(ANSI_COLOR_RED ANSI_BOLD "Shell: " ANSI_COLOR_RESET "%s\n", info->shell);
    printf(ANSI_COLOR_RED ANSI_BOLD "Resolution: " ANSI_COLOR_RESET "%s\n", info->resolution);
    printf(ANSI_COLOR_RED ANSI_BOLD "DE: " ANSI_COLOR_RESET "%s\n", info->de);
    printf(ANSI_COLOR_RED ANSI_BOLD "WM: " ANSI_COLOR_RESET "%s\n", info->wm);
    printf(ANSI_COLOR_RED ANSI_BOLD "CPU: " ANSI_COLOR_RESET "%s\n", info->cpu);
    printf(ANSI_COLOR_RED ANSI_BOLD "GPU: " ANSI_COLOR_RESET "%s\n", info->gpu);

    // Memory
    DWORDLONG total_mem_mb = info->memory.ullTotalPhys / (1024 * 1024);
    DWORDLONG used_mem_mb = (info->memory.ullTotalPhys - info->memory.ullAvailPhys) / (1024 * 1024);
    DWORDLONG total_mem_gb = total_mem_mb / 1024;
    DWORDLONG used_mem_gb = used_mem_mb / 1024;

    printf(ANSI_COLOR_RED ANSI_BOLD "Memory: " ANSI_COLOR_RESET "%lld MB / %lld MB (%.1f GB / %.1f GB)\n",
           used_mem_mb, total_mem_mb, (float)used_mem_gb, (float)total_mem_gb);
    
    printf(ANSI_COLOR_RED ANSI_BOLD "Disk (C:): " ANSI_COLOR_RESET "%s\n", info->disk_info);
    
    // Battery status
    if (info->power_status.BatteryFlag != 128) { // 128 means no battery
        int battery_percentage = info->power_status.BatteryLifePercent;
        const char* power_status = (info->power_status.ACLineStatus == 1) ? "Charging" : "Discharging";
        printf(ANSI_COLOR_RED ANSI_BOLD "Battery: " ANSI_COLOR_RESET "%d%% (%s)\n", 
               battery_percentage, power_status);
    }

    printf(ANSI_COLOR_RED ANSI_BOLD "Motherboard: " ANSI_COLOR_RESET "%s\n", info->motherboard);
    printf(ANSI_COLOR_RED ANSI_BOLD "BIOS: " ANSI_COLOR_RESET "%s\n", info->bios_version);

    // Color blocks
    printf("\n");
    printf(ANSI_COLOR_RED "███" ANSI_COLOR_GREEN "███" ANSI_COLOR_YELLOW "███" 
           ANSI_COLOR_BLUE "███" ANSI_COLOR_MAGENTA "███" ANSI_COLOR_CYAN "███" ANSI_COLOR_RESET "\n");
    printf(ANSI_COLOR_RED "███" ANSI_COLOR_GREEN "███" ANSI_COLOR_YELLOW "███" 
           ANSI_COLOR_BLUE "███" ANSI_COLOR_MAGENTA "███" ANSI_COLOR_CYAN "███" ANSI_COLOR_RESET "\n");
}