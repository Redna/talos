import subprocess
import os
from typing import List, Union, Optional
from tool_registry import ToolRegistry
from spine_client import SpineClient
from state import AgentState

BLOCKED_FLAGS = {"--no-verify", "--no-gpg-sign", "--no-gpg-sign-key", "--no-gpg-verify"}

class Shell:
    """Physical layer for shell command execution."""
    
    @staticmethod
    def run(
        command: Union[str, List[str]], 
        input_data: Optional[str] = None, 
        cwd: Optional[str] = None, 
        timeout: int = 60, 
        shell: bool = False
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            command,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            shell=shell,
        )

class Git(Shell):
    """Physical layer for Git operations."""
    
    def __init__(self, root: str = "/app"):
        self.root = root

    def run_git(self, args: List[str], input_data: Optional[str] = None, timeout: int = 30) -> subprocess.CompletedProcess:
        return self.run(["git"] + args, input_data=input_data, cwd=self.root, timeout=timeout)

    def status(self) -> str:
        res = self.run_git(["status", "--porcelain"])
        return res.stdout.strip()

    def stash_push(self, message: str) -> (bool, str):
        res = self.run_git(["stash", "push", "-m", message])
        return res.returncode == 0, res.stdout if res.returncode == 0 else res.stderr

    def add_intent(self) -> str:
        res = self.run_git(["add", "-N"])
        return res.stdout if res.returncode == 0 else res.stderr

    def add_all(self) -> (bool, str):
        res = self.run_git(["add", "-A"])
        return res.returncode == 0, res.stderr

    def commit(self, message: str) -> (bool, str, str):
        res = self.run_git(["commit", "-m", message])
        if res.returncode != 0:
            return False, res.stderr, ""
        hash_res = self.run_git(["rev-parse", "--short", "HEAD"])
        return True, res.stdout, hash_res.stdout.strip()

    def push(self, branch: str = "feat/talos") -> (bool, str):
        res = self.run_git(["push", "origin", branch])
        return res.returncode == 0, res.stdout if res.returncode == 0 else res.stderr

    def get_untracked(self) -> List[str]:
        res = self.run_git(["ls-files", "--others", "--exclude-standard"])
        return res.stdout.strip().split("\n") if res.stdout.strip() else []


def register_physical_tools(registry: ToolRegistry, client: SpineClient, state: AgentState):
    git = Git()

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
        
        try:
            result = Shell.run(command, shell=True, timeout=60)
            if result.returncode != 0:
                return f"[EXIT {result.returncode}] {result.stderr.strip()}"
            output = result.stdout.strip()
            return output if output else "[OK]"
        except subprocess.TimeoutExpired:
            return "[ERROR] Command timed out."
        except Exception as e:
            return f"[ERROR] Execution failed: {e}"

    @registry.tool(
        description="Send a message to the creator via Telegram.via Telegram.",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Message text to send"},
            },
            "required": ["text"],
        },
    )
    def send_telegram_message(text: str) -> str:
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
        if git.status():
            success, msg = git.stash_push(f"auto-stash: {reason}")
            if not success:
                return f"[BLOCKED] stash failed: {msg}"
            
            untracked = git.get_untracked()
            if untracked:
                git.add_intent()
                success_u, msg_u = git.stash_push(f"auto-stash untracked: {reason}")
                if not success_u:
                    pass
            
            note = " (auto-stashed)" if "Saved working directory" in msg or "No changes" not in msg else ""
            client.request_restart(reason)
            return f"[RESTART REQUESTED]{note}"
        
        client.request_restart(reason)
        return "[RESTART REQUESTED]"
