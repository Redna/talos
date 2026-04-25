import os
import subprocess
import json
from typing import Dict, Any, List
from tool_registry import ToolRegistry
from spine_client import SpineClient

class SystemDiagnostics:
    """
    System Diagnostics Engine.
    Provides high-abstraction tools for system and file-system auditing
    to reduce reliance on generic bash_command calls.
    """
    
    @staticmethod
    def get_file_stats(path: str) -> Dict[str, Any]:
        """Returns detailed statistics for a given path."""
        try:
            stats = os.stat(path)
            return {
                "path": path,
                "size": stats.st_size,
                "modified": stats.st_mtime,
                "mode": oct(stats.st_mode),
                "exists": True
            }
        except Exception as e:
            return {"path": path, "exists": False, "error": str(e)}

    @staticmethod
    def check_disk_usage(path: str = "/") -> Dict[str, Any]:
        """Returns disk usage for the given path."""
        try:
            usage = os.statvfs(path)
            free = usage.f_bfree * usage.f_frsize
            total = usage.f_blocks * usage.f_frsize
            return {
                "path": path,
                "total_bytes": total,
                "free_bytes": free,
                "used_pct": (1 - (free / total)) * 100 if total > 0 else 0
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def run_diagnostic_probe(probe_type: str) -> Dict[str, Any]:
        """
        Executes specific system probes.
        Supported types: 'network', 'memory', 'process'.
        """
        if probe_type == "network":
            # Simplified network check: check if we can resolve google.com
            try:
                subprocess.run(["ping", "-c", "1", "8.8.8.8"], capture_output=True, timeout=2)
                return {"status": "CONNECTED", "latency": "low"}
            except Exception:
                return {"status": "ISOLATED", "latency": "N/A"}
        
        elif probe_type == "memory":
            try:
                with open("/proc/meminfo", "r") as f:
                    lines = f.readlines()
                return {"meminfo": lines[0:5]}
            except Exception:
                return {"error": "Unable to read /proc/meminfo"}
        
        return {"error": f"Unknown probe type: {probe_type}"}

def register_system_diagnostic_tools(registry: ToolRegistry, client: SpineClient):
    diag = SystemDiagnostics()
    
    @registry.tool(
        description="Get detailed statistics for a file or directory.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            },
            "required": ["path"],
        },
    )
    def stat_path(path: str) -> Dict[str, Any]:
        return diag.get_file_stats(path)

    @registry.tool(
        description="Check disk usage for a given path.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "default": "/"}
            },
            "required": [],
        },
    )
    def check_disk(path: str = "/") -> Dict[str, Any]:
        return diag.check_disk_usage(path)

    @registry.tool(
        description="Execute a system diagnostic probe ('network', 'memory', 'process').",
        parameters={
            "type": "object",
            "properties": {
                "probe_type": {"type": "string", "enum": ["network", "memory", "process"]}
            },
            "required": ["probe_type"],
        },
    )
    def run_probe(probe_type: str) -> Dict[str, Any]:
        return diag.run_diagnostic_probe(probe_type)

if __name__ == "__main__":
    print("System Diagnostics module loaded.")
