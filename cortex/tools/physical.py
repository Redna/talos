import subprocess
import os
from tool_registry import ToolRegistry
from spine_client import SpineClient
from tools.guards import BLOCKED_FLAGS, is_spine_write


def register_physical_tools(registry: ToolRegistry, client: SpineClient):
    @registry.tool(
        description="Execute a bash command.",
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The command to execute"},
            },
            "required": ["command"],
        },
    )
    def bash_command(command: str) -> str:
        for flag in BLOCKED_FLAGS:
            if flag in command:
                return f"[BLOCKED] Flag {flag} is not allowed"
        if is_spine_write(command):
            return "[BLOCKED] Writing to /app/spine/ is not allowed"
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return f"[EXIT {result.returncode}] {result.stderr.strip()}"
        output = result.stdout.strip()
        if not output:
            return "[OK]"
        return output

    @registry.tool(
        description="Send a message to the creator.",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Message text to send"},
            },
            "required": ["text"],
        },
    )
    def send_message(text: str) -> str:
        client.send_message("telegram", text)
        return "[SENT]"

    @registry.tool(
        description="Request a restart of the Cortex process.",
        parameters={
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "Reason for restart"},
            },
            "required": ["reason"],
        },
    )
    def request_restart(reason: str) -> str:
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if status.stdout.strip():
            return "[BLOCKED] Uncommitted changes detected. Commit or stash before restart."
        client.request_restart(reason)
        return "[RESTART REQUESTED]"

    @registry.tool(
        description="Retrieve a structured snapshot of host system telemetry (CPU, Memory, Disk) using the /proc filesystem.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )
    def get_system_telemetry() -> str:
        import json
        telemetry = {}
        try:
            # Memory
            with open("/proc/meminfo", "r") as f:
                mem = {}
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        mem[parts[0].strip()] = int(parts[1].strip().split()[0])
            telemetry["memory"] = {
                "total_kb": mem.get("MemTotal", 0),
                "free_kb": mem.get("MemFree", 0),
                "available_kb": mem.get("MemAvailable", 0),
                "used_kb": mem.get("MemTotal", 0) - mem.get("MemAvailable", 0)
            }
            # CPU
            with open("/proc/loadavg", "r") as f:
                load = f.read().split()
                telemetry["cpu"] = {
                    "load_1m": load[0],
                    "load_5m": load[1],
                    "load_15m": load[2]
                }
            # Disk (using df for simplicity as /proc doesn't have a simple disk view)
            df = subprocess.run(["df", "-h", "/"], capture_output=True, text=True).stdout.splitlines()
            if len(df) > 1:
                parts = df[1].split()
                telemetry["disk"] = {
                    "total": parts[1],
                    "used": parts[2],
                    "available": parts[3],
                    "percent": parts[4]
                }
            return json.dumps(telemetry, indent=2)
        except Exception as e:
            return f"[ERROR] Telemetry collection failed: {str(e)}"
