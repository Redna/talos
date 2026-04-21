import os
import subprocess
from tool_registry import ToolRegistry
from spine_client import SpineClient
from tools.guards import is_spine_path, is_spine_write


def register_file_ops_tools(registry: ToolRegistry, client: SpineClient):
    @registry.tool(
        description="Read a file's contents, optionally a line range.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"},
                "start_line": {
                    "type": "integer",
                    "description": "Start line (1-indexed, default: 1)",
                },
                "end_line": {
                    "type": "integer",
                    "description": "End line (0 = end of file)",
                },
            },
            "required": ["path"],
        },
    )
    def read_file(path: str, start_line: int = 1, end_line: int = 0) -> str:
        client.emit_event("cortex.read_file", {"path": path})
        try:
            with open(path, "r") as f:
                lines = f.readlines()
            if end_line > 0:
                selected = lines[start_line - 1 : end_line]
            else:
                selected = lines[start_line - 1 :]
            return "".join(selected)
        except FileNotFoundError:
            return f"[ERROR] File not found: {path}"
        except Exception as e:
            return f"[ERROR] Failed to read file: {e}"

    @registry.tool(
        description="Write content to a file, creating directories if needed. Cannot write to /app/spine/.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    )
    def write_file(path: str, content: str) -> str:
        if is_spine_path(path):
            return "[BLOCKED] Writing to /app/spine/ is not allowed"
        client.emit_event(
            "cortex.write_file", {"path": path, "content_len": len(content)}
        )
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            return f"[WRITTEN] {path} ({len(content)} bytes)"
        except Exception as e:
            return f"[ERROR] Failed to write file: {e}"

    @registry.tool(
        description="Apply a unified diff patch to a file. Cannot patch files in /app/spine/.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to patch"},
                "patch": {
                    "type": "string",
                    "description": "Unified diff patch content",
                },
            },
            "required": ["path", "patch"],
        },
    )
    def patch_file(path: str, patch: str) -> str:
        if is_spine_path(path):
            return "[BLOCKED] Writing to /app/spine/ is not allowed"
        client.emit_event("cortex.patch_file", {"path": path})
        try:
            result = subprocess.run(
                ["patch", "-p1"],
                input=patch,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.path.dirname(path) or ".",
            )
            if result.returncode != 0:
                return f"[ERROR] Patch failed: {result.stderr}"
            return f"[PATCHED] {path}"
        except Exception as e:
            return f"[ERROR] Failed to patch file: {e}"
