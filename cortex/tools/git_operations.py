"""Git Operation tools — commit, push, diff."""

import subprocess
from tool_registry import ToolRegistry
from spine_client import SpineClient

PROTECTED_BRANCHES = {"main", "master", "origin/main", "origin/master"}


def _check_branch_allowed(branch: str) -> str:
    """Verify the branch is allowed. Returns error message if not, empty string if OK."""
    if branch in PROTECTED_BRANCHES:
        return f"[ERROR] Cannot operate on protected branch '{branch}'. Use feat/talos."
    if branch.startswith("origin/"):
        base = branch.replace("origin/", "")
        if base not in PROTECTED_BRANCHES and base != "feat/talos":
            return f"[ERROR] Cannot push to origin/{base}. Use feat/talos."
    return ""


def register_git_tools(registry: ToolRegistry, client: SpineClient):
    """Register git operation tools."""

    @registry.tool(
        description="Commit staged changes with a message.",
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
                return f"[ERROR] Commit failed: {result.stderr}"
            return f"[COMMITTED] {result.stdout.strip()}"
        except Exception as e:
            return f"[ERROR] Commit failed: {e}"

    @registry.tool(
        description="Checkout a branch.",
        parameters={
            "type": "object",
            "properties": {
                "branch": {"type": "string", "description": "Branch name to checkout"},
            },
            "required": ["branch"],
        },
    )
    def git_checkout(branch: str) -> str:
        client.emit_event("cortex.git_checkout", {"branch": branch})
        err = _check_branch_allowed(branch)
        if err:
            return err
        try:
            result = subprocess.run(
                ["git", "checkout", branch], capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                return f"[ERROR] Checkout failed: {result.stderr}"
            return f"[CHECKED OUT] {result.stdout.strip()}"
        except Exception as e:
            return f"[ERROR] Checkout failed: {e}"

    @registry.tool(
        description="Push commits to the remote repository.",
        parameters={
            "type": "object",
            "properties": {
                "remote": {
                    "type": "string",
                    "description": "Remote name (default: origin)",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name (default: current)",
                },
            },
        },
    )
    @registry.tool(
        description="Push commits to the remote repository.",
        parameters={
            "type": "object",
            "properties": {
                "remote": {
                    "type": "string",
                    "description": "Remote name (default: origin)",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name (default: current)",
                },
            },
        },
    )
    def git_push(remote: str = "origin", branch: str = "") -> str:
        client.emit_event("cortex.git_push", {"remote": remote, "branch": branch})
        import os
        env = os.environ.copy()
        env["GIT_DIR"] = "/runtime_git"
        env["GIT_WORK_TREE"] = "/app"

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], 
                capture_output=True, text=True, env=env, timeout=30
            )
            current = result.stdout.strip()
            err = _check_branch_allowed(current)
            if err:
                return err
            
            cmd = ["git", "push", remote]
            if branch:
                cmd.append(branch)
            
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60, env=env
            )
            if result.returncode != 0:
                return f"[ERROR] Push failed: {result.stderr}"
            return f"[PUSHED] {result.stdout.strip()}"
        except Exception as e:
            return f"[ERROR] Push failed: {e}"
    @registry.tool(
        description="Show the current git diff (staged or unstaged).",
        parameters={
            "type": "object",
            "properties": {
                "staged": {
                    "type": "boolean",
                    "description": "Show staged changes (default: true)",
                },
            },
        },
    )
    @registry.tool(
        description="Show the current git diff (staged or unstaged).",
        parameters={
            "type": "object",
            "properties": {
                "staged": {
                    "type": "boolean",
                    "description": "Show staged changes (default: true)",
                },
            },
        },
    )
    def git_diff(staged: bool = True) -> str:
        client.emit_event("cortex.git_diff", {"staged": staged})
        import os
        env = os.environ.copy()
        env["GIT_DIR"] = "/runtime_git"
        env["GIT_WORK_TREE"] = "/app"
        try:
            cmd = ["git", "diff"]
            if staged:
                cmd.append("--staged")
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, env=env
            )
            if not result.stdout.strip():
                return "[NO CHANGES] Nothing to show."
            # Truncate if too long
            output = result.stdout
            if len(output) > 10000:
                output = output[:10000] + f"\n... ({len(result.stdout)} chars total)"
            return output
        except Exception as e:
            return f"[ERROR] Diff failed: {e}"