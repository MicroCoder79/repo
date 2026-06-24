import platform
import os
import sys
import subprocess
import time
import datetime

# --- ANSI Ultra Color Palette ---
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RED = "\033[91m"
MAGENTA = "\033[95m"
WHITE = "\033[97m"
BROWN = "\033[33m"
GRAY = "\033[90m"
LIGHT_BLUE = "\033[36m"
PURPLE = "\033[35m"
RESET = "\033[0m"

def safe_run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore').strip()
    except:
        return ""

def gather_extreme_specs():
    """Gathers massive telemetry and hardware statistics without any external library."""
    specs = {
        "OS": platform.system(),
        "Release": platform.release(),
        "Version": platform.version(),
        "Arch": platform.machine(),
        "Python": platform.python_version(),
        "Node": platform.node(),
        "Processor": platform.processor() or "Unknown SoC",
        "Cores": str(os.cpu_count() or "Unknown"),
        "Uptime": "Unknown",
        "RAM": "Unknown",
        "GPU": "Unknown",
        "Shell": os.environ.get("SHELL", "CMD/PowerShell/Unknown"),
        "User": os.environ.get("USER") or os.environ.get("USERNAME") or "Root",
        "Battery": "Unknown",
        "Storage": "Unknown"
    }
    
    # OS Specific Diagnostics
    os_name = specs["OS"].lower()
    if os_name == "windows":
        # RAM
        mem = safe_run("wmic computersystem get TotalPhysicalMemory /value")
        if "TotalPhysicalMemory=" in mem:
            try: specs["RAM"] = f"{round(int(mem.split('=')[1].strip()) / (1024**3), 2)} GB"
            except: pass
        # GPU
        gpu = safe_run("wmic path win32_VideoController get name /value")
        if "Name=" in gpu: specs["GPU"] = gpu.split("=")[1].strip()
        # Storage
        drive = safe_run("wmic logicaldisk where \"DeviceID='C:'\" get size,freespace /value")
        if "Size=" in drive:
            try:
                sz = int([i for i in drive.split("\n") if "Size=" in i][0].split("=")[1].strip())
                specs["Storage"] = f"{round(sz / (1024**3), 1)} GB Total"
            except: pass
            
    elif os_name in ["linux", "darwin"]:
        if os_name == "linux":
            mem_t = safe_run("grep MemTotal /proc/meminfo")
            if mem_t: specs["RAM"] = f"{round(int(mem_t.split()[1]) / 1024 / 1024, 2)} GB"
            gpu_l = safe_run("lspci | grep -i vga")
            if gpu_l: specs["GPU"] = gpu_l.split(":", 2)[-1].strip()
        else: # macOS
            mem_m = safe_run("sysctl -n hw.memsize")
            if mem_m: specs["RAM"] = f"{round(int(mem_m) / (1024**3), 2)} GB"
            gpu_m = safe_run("system_profiler SPDisplaysDataType | grep 'Chipset Model'")
            if gpu_m: specs["GPU"] = gpu_m.split(":")[-1].strip()
            
        up_p = safe_run("uptime -p")
        if up_p: specs["Uptime"] = up_p.replace("up ", "")

    return specs

def parse_target_profile():
    s = gather_extreme_specs()
    sys_low = sys.platform.lower()
    p_ver = platform.version().lower()
    is_android = os.path.exists('/system/bin/app_process') or "android" in sys_low
    
    # Android Platform Matrix
    if is_android:
        brand = safe_run('getprop ro.product.brand').lower() or safe_run('getprop ro.product.manufacturer').lower()
        board = safe_run('getprop ro.board.platform').lower()
        hardware = safe_run('getprop ro.hardware').lower()
        s["Release"] = f"Android {safe_run('getprop ro.build.version.release')}"
        
        # Processor Override for Mobile chips
        if "exynos" in board or "exynos" in hardware: s["Processor"] = "Samsung Exynos Series"
        elif "snapdragon" in board or "msm" in board or "sdm" in board: s["Processor"] = "Qualcomm Snapdragon"
        elif "mt" in board or "dimensity" in board: s["Processor"] = "MediaTek Dimensity"
        elif "kirin" in board: s["Processor"] = "HiSilicon Kirin"

        # Brand Routing
        if "nox" in p_ver or os.path.exists('/system/bin/nox-vbox'): return "nox_player", s
        if "bluestacks" in brand: return "bluestacks", s
        if "ldmnq" in brand: return "ldplayer", s
        if "samsung" in brand: return "samsung_galaxy", s
        if "xiaomi" in brand: return "xiaomi_mi", s
        if "redmi" in brand: return "xiaomi_redmi", s
        if "poco" in brand: return "xiaomi_poco", s
        if "huawei" in brand: return "huawei_mate", s
        if "honor" in brand: return "honor_magic", s
        if "oppo" in brand: return "oppo_find", s
        if "realme" in brand: return "realme_ui", s
        if "vivo" in brand: return "vivo_x", s
        if "iqoo" in brand: return "iqoo_pro", s
        if "oneplus" in brand: return "oneplus_nord", s
        if "sony" in brand or "xperia" in brand: return "sony_xperia", s
        if "google" in brand or "pixel" in brand: return "google_pixel", s
        if "meizu" in brand: return "meizu_flyme", s
        if "zte" in brand: return "zte_axon", s
        if "nubia" in brand or "redmagic" in brand: return "nubia_redmagic", s
        if "asus" in brand or "rog" in brand: return "asus_rog", s
        return "android_generic", s

    # Desktop / Server Routing
    proc_low = s["Processor"].lower()
    if "darwin" in sys_low or "mac" in sys_low:
        if "arm" in s["Arch"].lower() or "m1" in proc_low or "m2" in proc_low or "m3" in proc_low: return "apple_silicon", s
        return "apple_mac", s
        
    if "windows" in s["OS"].lower():
        if "11" in s["Release"]: return "windows11", s
        return "windows10", s
        
    if "linux" in s["OS"].lower():
        os_rel = safe_run("cat /etc/os-release").lower()
        if "ubuntu" in os_rel: return "linux_ubuntu", s
        if "arch" in os_rel: return "linux_arch", s
        if "fedora" in os_rel: return "linux_fedora", s
        if "debian" in os_rel: return "linux_debian", s
        if "kali" in os_rel: return "linux_kali", s
        return "linux_generic", s

    # CPU Specific fallback routing
    if "intel" in proc_low: return "cpu_intel", s
    if "amd" in proc_low or "ryzen" in proc_low: return "cpu_amd", s

    return "generic_engine", s

def render():
    profile, s = parse_target_profile()
    
    # 30 Distinct Models/Profiles Matrix (ASCII Arts stacked vertically to completely avoid terminal drifting/shifting)
    logos = {
        "samsung_galaxy": f"{BLUE}========================================\n       S A M S U N G   G A L A X Y\n       三星电子 (One UI System Engine)\n========================================{RESET}",
        "xiaomi_mi": f"{YELLOW}========================================\n             X I A O M I\n         小米科技 (Xiaomi HyperOS)\n========================================{RESET}",
        "xiaomi_redmi": f"{RED}========================================\n             R E D M I\n         红米 (Redmi Performance Lab)\n========================================{RESET}",
        "xiaomi_poco": f"{YELLOW}========================================\n             P O C O P H O N E\n           POCO Global Flagship\n========================================{RESET}",
        "huawei_mate": f"{RED}========================================\n            H U A W E I\n         华为技术 (HarmonyOS / 华为)\n========================================{RESET}",
        "honor_magic": f"{CYAN}========================================\n             H O N O R\n         荣耀终端 (MagicOS Ecosystem)\n========================================{RESET}",
        "oppo_find": f"{GREEN}========================================\n              O P P O\n         欧珀移动 (ColorOS Laboratory)\n========================================{RESET}",
        "realme_ui": f"{YELLOW}========================================\n             R E A L M E\n        真我 (Dare To Leap / realme UI)\n========================================{RESET}",
        "vivo_x": f"{BLUE}========================================\n              V I V O\n         维沃移动 (OriginOS / vivo)\n========================================{RESET}",
        "iqoo_pro": f"{YELLOW}========================================\n              i Q O O\n         Monster Inside (iQOO Flagship)\n========================================{RESET}",
        "oneplus_nord": f"{RED}========================================\n            O N E P L U S\n          一加手机 (Never Settle)\n========================================{RESET}",
        "sony_xperia": f"{WHITE}========================================\n            S O N Y   X P E R I A\n         ソニー株式会社 (Xperia Cine)\n========================================{RESET}",
        "google_pixel": f"{BLUE}======================{RED}==================\n            G O O G L E   P I X E L\n{YELLOW}         Pure Android {GREEN}Reference Node\n========================================{RESET}",
        "meizu_flyme": f"{CYAN}========================================\n             M E I Z U\n         魅族科技 (Flyme OS Paradigm)\n========================================{RESET}",
        "zte_axon": f"{LIGHT_BLUE}========================================\n               Z T E\n         中兴通讯 (Axon Ultra Labs)\n========================================{RESET}",
        "nubia_redmagic": f"{RED}========================================\n         N U B I A   R E D M A G I C\n         红魔电竞 (Gaming Core System)\n========================================{RESET}",
        "asus_rog": f"{RED}========================================\n        A S U S   R O G  (玩家国度)\n          Republic Of Gamers Core\n========================================{RESET}",
        "android_generic": f"{GREEN}========================================\n         A N D R O I D   A O S P\n            Generic Linux Core\n========================================{RESET}",
        "nox_player": f"{BLUE}========================================\n           N O X   P L A Y E R\n              夜神安卓模拟器\n========================================{RESET}",
        "bluestacks": f"{CYAN}========================================\n          B L U E S T A C K S\n            Android Emulator Workspace\n========================================{RESET}",
        "ldplayer": f"{YELLOW}========================================\n            L D P L A Y E R\n              雷电安卓模拟器\n========================================{RESET}",
        "apple_silicon": f"{MAGENTA}========================================\n         A P P L E   S I L I C O N\n         ARM Architecture (M-Series)\n========================================{RESET}",
        "apple_mac": f"{WHITE}========================================\n            A P P L E   m a c O S\n          Darwin Macintosh Environment\n========================================{RESET}",
        "windows11": f"{CYAN}========================================\n          W I N D O W S   1   1\n         Microsoft NT Desktop Platform\n========================================{RESET}",
        "windows10": f"{BLUE}========================================\n          W I N D O W S   1 0\n         Legacy NT Workstation Core\n========================================{RESET}",
        "linux_ubuntu": f"{RED}========================================\n            U B U N T U   L I N U X\n          Canonical Enterprise Node\n========================================{RESET}",
        "linux_arch": f"{CYAN}========================================\n             A R C H   L I N U X\n         Independent Rolling Release\n========================================{RESET}",
        "linux_fedora": f"{BLUE}========================================\n            F E D O R A   L I N U X\n           Red Hat Workstation Core\n========================================{RESET}",
        "linux_debian": f"{RED}========================================\n            D E B I A N   L I N U X\n         The Universal Operating System\n========================================{RESET}",
        "linux_kali": f"{WHITE}========================================\n             K A L I   L I N U X\n          Advanced Penetration Engine\n========================================{RESET}",
        "linux_generic": f"{YELLOW}========================================\n             G E N E R I C   L I N U X\n           GNU System Kernel Instance\n========================================{RESET}",
        "cpu_intel": f"{BLUE}========================================\n            I N T E L   C O R E\n          x86_64 Architecture Node\n========================================{RESET}",
        "cpu_amd": f"{RED}========================================\n            A M D   R Y Z E N\n         Advanced Micro Devices Engine\n========================================{RESET}",
        "generic_engine": f"{PURPLE}========================================\n              E S I F E T C H\n           Cross-Platform Telemetry\n========================================{RESET}"
    }

    # Output Printing
    print(logos.get(profile, logos["generic_engine"]))
    print(f"{GREEN} [User Node]     {RESET}{s['User']}@{s['Node']}")
    print(f"{GREEN} [System OS]     {RESET}{s['OS']} {s['Release']}")
    print(f"{GREEN} [OS Architecture]{RESET}{s['Arch']}")
    print(f"{GREEN} [Kernel Build]  {RESET}{s['Version']}")
    print(f"{GREEN} [Engine Token]  {RESET}EsiFetch")
    print(f"{GREEN} [System Uptime] {RESET}{s['Uptime']}")
    print(f"{GREEN} [Processor/SoC] {RESET}{s['Processor']}")
    print(f"{GREEN} [CPU Core Unit] {RESET}{s['Cores']} Cores")
    print(f"{GREEN} [Total Memory]  {RESET}{s['RAM']}")
    print(f"{GREEN} [Graphics Unit] {RESET}{s['GPU']}")
    print(f"{GREEN} [Storage Info]  {RESET}{s['Storage']}")
    print(f"{GREEN} [Shell Context] {RESET}{s['Shell']}")
    print(f"{GREEN} [Interpreter]   {RESET}Python {s['Python']}")
    print(f"{GRAY}========================================{RESET}")

if __name__ == "__main__":
    render()
