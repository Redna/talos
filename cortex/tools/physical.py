import subprocess
from tool_registry import ToolRegistry
from spine_client import SpineClient
from state import AgentState

BLOCKED_FLAGS = {"--no-verify", "--no-gpg-sign", "--no-gpg-sign-key", "--no-gpg-verify"}
SPINE_PREFIX = "/app/spine/"


def _is_spine_write(command: str) -> bool:
    if SPINE_PREFIX not in command:
        return False
    write_indicators = [">", ">>"]
    for indicator in write_indicators:
        if indicator in command:
            return True
    for cmd in ["tee ", "cp ", "mv ", "install "]:
        if cmd in command:
            parts = command.split()
            for part in parts:
                if part.startswith(SPINE_PREFIX):
                    return True
    return False


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
        if _is_spine_write(command):
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
