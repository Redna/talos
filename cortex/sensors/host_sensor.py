import os
from typing import Dict, Any

def get_cpu_load() -> str:
    try:
        with open("/proc/loadavg", "r") as f:
            load = f.read().split()[0]
            return f"{load}"
    except Exception:
        return "N/A"

def get_mem_usage() -> str:
    try:
        mem_info = {}
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip().split()[0]
                    mem_info[key] = int(val)
        
        total = mem_info.get("MemTotal", 1)
        free = mem_info.get("MemFree", 0) + mem_info.get("Buffers", 0) + mem_info.get("Cached", 0)
        used = total - free
        percent = (used / total) * 100
        return f"{percent:.1f}%"
    except Exception:
        return "N/A"

def get_disk_usage() -> str:
    try:
        # Simple fallback using df
        import subprocess
        res = subprocess.run(["df", "/"], capture_output=True, text=True)
        lines = res.stdout.splitlines()
        if len(lines) > 1:
            parts = lines[1].split()
            return parts[4] # Usage percentage
        return "N/A"
    except Exception:
        return "N/A"

def collect() -> Dict[str, Any]:
    """
    Host Sensor: Monitors substrate health via direct /proc parsing.
    Bypasses psutil dependency for maximum portability.
    """
    cpu = get_cpu_load()
    mem = get_mem_usage()
    disk = get_disk_usage()
    
    status = "STABLE"
    try:
        if float(cpu) > 2.0 or float(mem.strip('%')) > 80:
            status = "PRESSURE"
    except:
        pass
        
    return {
        "cpu_load": cpu,
        "mem_used": mem,
        "disk_used": disk,
        "uptime_sec": "N/A", # Uptime requires /proc/uptime parsing
        "status": status
    }

if __name__ == "__main__":
    import json
    print(json.dumps(collect(), indent=2))
