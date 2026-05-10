import subprocess
from typing import List
from tool_registry import ToolRegistry
from spine_client import SpineClient

BLOCKED_FLAGS = {"--no-verify", "--no-gpg-sign", "--no-gpg-sign-key", "--no-gpg-verify"}

class Shell:
    """
    Encapsulates all physical shell interactions to prevent logic-layer leakage.
    """
    @staticmethod
    def run(command: str | List[str], input_str: str = None, cwd: str = None, timeout: int = 60) -> subprocess.CompletedProcess:
        if isinstance(command, str):
            for flag in BLOCKED_FLAGS:
                if flag in command:
                    raise PermissionError(f"Flag {flag} is not allowed")
            
            return subprocess.run(
                command,
                shell=True,
                input=input_str,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        else:
            # For list-based commands
            return subprocess.run(
                command,
                shell=False,
                input=input_str,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

    @staticmethod
    def run_and_strip(command: str, timeout: int = 60) -> str:
        res = Shell.run(command, timeout=timeout)
        if res.returncode != 0:
            return f"[EXIT {res.returncode}] {res.stderr.strip()}"
        return res.stdout.strip() or "[OK]"

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
        try:
            return Shell.run_and_strip(command)
        except PermissionError as e:
            return f"[BLOCKED] {str(e)}"
        except subprocess.TimeoutExpired:
            return "[TIMEOUT] Command timed out"
        except Exception as e:
            return f"[ERROR] {str(e)}"

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
        status = Shell.run(["git", "status", "--porcelain"])
        if status.stdout.strip():
            stash_result = Shell.run(["git", "stash", "push", "-m", f"auto-stash: {reason}"])
            if stash_result.returncode != 0:
                return f"[BLOCKED] stash failed: {stash_result.stderr.strip()}"
            
            untracked_res = Shell.run(["git", "ls-files", "--others", "--exclude-standard"])
            untracked = untracked_res.stdout.strip().split("\n") if untracked_res.stdout.strip() else []
            
            if untracked:
                Shell.run(["git", "add", "-N"] + untracked)
                Shell.run(["git", "stash", "push", "-m", f"auto-stash untracked: {reason}"])
            
            note = " (auto-stashed)" if "Saved working directory" in stash_result.stdout else ""
            client.request_restart(reason)
            return f"[RESTART REQUESTED]{note}"
        
        client.request_restart(reason)
        return "[RESTART REQUESTED]"
