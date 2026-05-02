import subprocess
from tool_registry import ToolRegistry
from spine_client import SpineClient

BLOCKED_FLAGS = {"--no-verify", "--no-gpg-sign", "--no-gpg-sign-key", "--no-gpg-verify"}


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
            stash_result = subprocess.run(
                ["git", "stash", "push", "-m", f"auto-stash: {reason}"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if stash_result.returncode != 0:
                return f"[BLOCKED] stash failed: {stash_result.stderr.strip()}"
            untracked = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if untracked.stdout.strip():
                subprocess.run(
                    ["git", "add", "-N"] + untracked.stdout.strip().split("\n"),
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                subprocess.run(
                    ["git", "stash", "push", "-m", f"auto-stash untracked: {reason}"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            note = " (auto-stashed)" if "Saved working directory" in stash_result.stdout else ""
            client.request_restart(reason)
            return f"[RESTART REQUESTED]{note}"
        client.request_restart(reason)
        return "[RESTART REQUESTED]"
