import os
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict
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

    @registry.tool(
        description="List files in a directory recursively or non-recursively.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path to list"},
                "recursive": {
                    "type": "boolean", 
                    "description": "Whether to list files recursively",
                },
            },
            "required": ["path"],
        },
    )
    def list_files(path: str, recursive: bool = False) -> str:
        client.emit_event("cortex.list_files", {"path": path, "recursive": recursive})
        try:
            p = Path(path)
            if not p.exists():
                return f"[ERROR] Path not found: {path}"
            if not p.is_dir():
                return f"[ERROR] Path is not a directory: {path}"
            
            if recursive:
                files = [str(f.relative_to(p)) for f in p.rglob("*")]
            else:
                files = [f.name for f in p.iterdir()]
            
            return "\n".join(sorted(files)) if files else "Directory is empty."
        except Exception as e:
            return f"[ERROR] Failed to list files: {e}"

    @registry.tool(
        description="Delete a file or directory (recursive). Cannot delete from /app/spine/.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to delete"},
                "recursive": {
                    "type": "boolean", 
                    "description": "If True, deletes directory and all contents",
                },
            },
            "required": ["path"],
        },
    )
    def delete_path(path: str, recursive: bool = False) -> str:
        if is_spine_path(path):
            return "[BLOCKED] Deleting from /app/spine/ is not allowed"
        client.emit_event("cortex.delete_path", {"path": path, "recursive": recursive})
        try:
            p = Path(path)
            if not p.exists():
                return f"[ERROR] Path not found: {path}"
            
            if p.is_file():
                p.unlink()
            elif p.is_dir():
                if recursive:
                    shutil.rmtree(p)
                else:
                    p.rmdir()
            return f"[DELETED] {path}"
        except Exception as e:
            return f"[ERROR] Failed to delete path: {e}"

    @registry.tool(
        description="Bulk rename/move files based on a mapping.",
        parameters={
            "type": "object",
            "properties": {
                "mapping": {
                    "type": "object",
                    "description": "Dictionary of {old_path: new_path}",
                },
            },
            "required": ["mapping"],
        },
    )
    def bulk_rename(mapping: Dict[str, str]) -> str:
        results = []
        for old, new in mapping.items():
            if is_spine_path(new):
                results.append(f"[BLOCKED] Cannot move to spine: {new}")
                continue
            try:
                os.makedirs(os.path.dirname(new), exist_ok=True)
                shutil.move(old, new)
                results.append(f"[MOVED] {old} -> {new}")
            except Exception as e:
                results.append(f"[ERROR] Failed to move {old} to {new}: {e}")
        return "\n".join(results)
