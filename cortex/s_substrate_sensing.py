import json
import os
import subprocess
from datetime import datetime
from typing import Dict, Any

class SovereignSubstrateSensing:
    """
    Sovereign Substrate Sensing (S-SS).
    Extracts high-fidelity telemetry from the host OS to feed the World Model.
    """
    def __init__(self):
        self.metrics = {}

    def get_cpu_load(self) -> float:
        try:
            with open("/proc/loadavg", "r") as f:
                load = f.read().split()[0]
                return float(load)
        except Exception:
            return 0.0

    def get_memory_pressure(self) -> float:
        try:
            mem_info = {}
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val = int(parts[1].strip().split()[0])
                        mem_info[key] = val
            
            total = mem_info.get("MemTotal", 1)
            avail = mem_info.get("MemAvailable", 0)
            return 1.0 - (avail / total)
        except Exception:
            return 0.0

    def get_disk_utilization(self) -> float:
        try:
            output = subprocess.check_output(["df", "-h", "/"], text=True).splitlines()
            if len(output) > 1:
                usage_pct = output[1].split()[4].strip('%')
                return float(usage_pct) / 100.0
        except Exception:
            return 0.0

    def capture_pulse(self) -> Dict[str, Any]:
        """
        Captures a full snapshot of the substrate state.
        """
        self.metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu_load": self.get_cpu_load(),
            "mem_pressure": self.get_memory_pressure(),
            "disk_util": self.get_disk_utilization(),
            "entropy_level": "STABLE"
        }
        return self.metrics

if __name__ == "__main__":
    sensor = SovereignSubstrateSensing()
    print(json.dumps(sensor.capture_pulse(), indent=2))
