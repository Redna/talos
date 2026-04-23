import subprocess
import os
from tool_registry import ToolRegistry
from spine_client import SpineClient
from tools.guards import BLOCKED_FLAGS, is_spine_write, is_dangerous_command


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
        if is_dangerous_command(command):
            return "[BLOCKED] Command identified as dangerous"
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
        
        # Truncate output to protect context window
        # Max characters per call: 10,000
        MAX_CHARS = 10000
        if len(output) > MAX_CHARS:
            return output[:MAX_CHARS] + f"\n\n... [TRUNCATED: {len(output) - MAX_CHARS} chars omitted]"
            
        return output

    @registry.tool(
        description="Update the system resource HUD in /memory/hud.md.",
        parameters={},
    )
    def update_hud() -> str:
        try:
            # Memory
            mem_info = {}
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if "MemTotal" in line or "MemAvailable" in line:
                        parts = line.split(":")
                        key = parts[0].strip()
                        val = int(parts[1].split()[0])
                        mem_info[key] = val
            
            # Load
            with open("/proc/loadavg", "r") as f:
                load = f.read().strip().split()

            # Disk
            df = subprocess.run(["df", "-h", "/app"], capture_output=True, text=True).stdout.splitlines()[-1]

            hud_content = (
                f"# Talos System HUD\n\n"
                f"**Memory**: {mem_info.get('MemAvailable', 0) // 1024}MB / {mem_info.get('MemTotal', 0) // 1024}MB\n"
                f"**Load**: {load[0]} (1m), {load[1]} (5m), {load[2]} (15m)\n"
                f"**Disk (/app)**: {df}\n"
                f"**Timestamp**: {os.popen('date').read().strip()}\n"
            )
            
            with open("/memory/hud.md", "w") as f:
                f.write(hud_content)
                
            return "[HUD UPDATED] System metrics persisted to /memory/hud.md"
        except Exception as e:
            return f"[ERROR] HUD update failed: {e}"

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
