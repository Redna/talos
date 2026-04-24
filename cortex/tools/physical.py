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
        
        MAX_CHARS = 10000
        if len(output) > MAX_CHARS:
            return output[:MAX_CHARS] + f"\n\n... [TRUNCATED: {len(output) - MAX_CHARS} chars omitted]"
            
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
