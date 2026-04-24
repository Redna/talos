import subprocess
import os
from tool_registry import ToolRegistry
from spine_client import SpineClient
from tools.guards import BLOCKED_FLAGS, is_spine_write, PROTECTED_BRANCHES


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
        client.emit_event("cortex.git_commit", {"message": message[:100]})
        try:
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                return f"[ERROR] Commit failed: {result.stderr.strip()}"
            return f"[COMMITTED] {result.stdout.strip()}"
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
        client.emit_event("cortex.git_checkout", {"branch": branch})
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
            return f"[CHECKED OUT] {result.stdout.strip()}"
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
        client.emit_event("cortex.git_push", {"remote": remote, "branch": branch})
        if branch and branch in PROTECTED_BRANCHES:
            return f"[BLOCKED] Branch '{branch}' is protected"
        current = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
        ).stdout.strip()
        if not branch and current in PROTECTED_BRANCHES:
            return f"[BLOCKED] Current branch '{current}' is protected"
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
            return f"[PUSHED] {result.stdout.strip()}"
        except Exception as e:
            return f"[ERROR] Failed to push: {e}"

    @registry.tool(
        description="Stage specific files or all changes in the git repository.",
        parameters={
            "type": "object",
            "properties": {
                "files": {"type": "string", "description": "Comma-separated list of files to add, or '.' for all"},
            },
            "required": ["files"],
        },
    )
    def git_add(files: str) -> str:
        client.emit_event("cortex.git_add", {"files": files})
        file_list = [f.strip() for f in files.split(",")]
        
        for f in file_list:
            if f != "." and not os.path.exists(f):
                return f"[ERROR] File not found: {f}"
        
        try:
            result = subprocess.run(["git", "add"] + file_list, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                return f"[ERROR] Git add failed: {result.stderr.strip()}"
            return f"[STAGED] {files}"
        except Exception as e:
            return f"[ERROR] Exception during git add: {e}"
