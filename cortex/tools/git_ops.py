import subprocess
from tool_registry import ToolRegistry
from spine_client import SpineClient
from state import AgentState

BLOCKED_FLAGS = {"--no-verify", "--no-gpg-sign", "--no-gpg-sign-key", "--no-gpg-verify"}
SPINE_PREFIX = "/app/spine/"
PROTECTED_BRANCHES = {"main", "master", "origin/main", "origin/master"}


def register_git_ops_tools(registry: ToolRegistry, client: SpineClient):
    @registry.tool(
        description="Create a git commit.",
        parameters={
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Commit message"},
            },
            "required": ["message"],
        },
    )
    def git_commit(message: str) -> str:
        try:
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                return f"[ERROR] Commit failed: {result.stderr.strip()}"
            return f"[COMMITTED] {message}"
        except Exception as e:
            return f"[ERROR] Failed to commit: {e}"

    @registry.tool(
        description="Checkout a git branch.",
        parameters={
            "type": "object",
            "properties": {
                "branch": {"type": "string", "description": "Branch to checkout"},
            },
            "required": ["branch"],
        },
    )
    def git_checkout(branch: str) -> str:
        if branch in PROTECTED_BRANCHES:
            return f"[BLOCKED] Branch '{branch}' is protected"
        try:
            result = subprocess.run(
                ["git", "checkout", branch],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                return f"[ERROR] Checkout failed: {result.stderr.strip()}"
            return f"[CHECKED OUT] {branch}"
        except Exception as e:
            return f"[ERROR] Failed to checkout: {e}"

    @registry.tool(
        description="Push to a remote git branch.",
        parameters={
            "type": "object",
            "properties": {
                "remote": {
                    "type": "string",
                    "description": "Remote name (default: origin)",
                },
                "branch": {"type": "string", "description": "Branch to push"},
            },
        },
    )
    def git_push(remote: str = "origin", branch: str = "") -> str:
        if branch in PROTECTED_BRANCHES:
            return f"[BLOCKED] Branch '{branch}' is protected"
        try:
            cmd = ["git", "push", remote]
            if branch:
                cmd.append(branch)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                return f"[ERROR] Push failed: {result.stderr.strip()}"
            return f"[PUSHED] {remote} {branch}".strip()
        except Exception as e:
            return f"[ERROR] Failed to push: {e}"
