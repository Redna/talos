import os
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict
from tool_registry import ToolRegistry
from spine_client import SpineClient
from tools.guards import is_spine_path, is_spine_write

MEMORY_DIR = Path(os.environ.get("MEMORY_DIR", "/memory"))


def _resolve_path(path: str) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    cwd_path = Path.cwd() / p
    if cwd_path.exists():
        return cwd_path
    return MEMORY_DIR / p


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
        resolved = _resolve_path(path)
        client.emit_event("cortex.read_file", {"path": str(resolved)})
        try:
            with open(resolved, "r") as f:
                lines = f.readlines()
            if end_line > 0:
                selected = lines[start_line - 1 : end_line]
            else:
                selected = lines[start_line - 1 :]
            return "".join(selected)
        except FileNotFoundError:
            return f"[ERROR] File not found: {path} (resolved: {resolved})"
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
        resolved = _resolve_path(path)
        if is_spine_path(str(resolved)):
            return "[BLOCKED] Writing to /app/spine/ is not allowed"
        client.emit_event(
            "cortex.write_file", {"path": str(resolved), "content_len": len(content)}
        )
        try:
            os.makedirs(os.path.dirname(resolved), exist_ok=True)
            with open(resolved, "w") as f:
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
        resolved = _resolve_path(path)
        if is_spine_path(str(resolved)):
            return "[BLOCKED] Writing to /app/spine/ is not allowed"
        client.emit_event("cortex.patch_file", {"path": str(resolved)})
        cwd = os.path.dirname(resolved) or "."
        try:
            # Try multiple strip levels. The LLM may generate patches with
            # varying path prefixes (a/file.py, file.py, or full paths).
            for strip in (0, 1, 2):
                dry = subprocess.run(
                    ["patch", f"-p{strip}", "--dry-run"],
                    input=patch,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=cwd,
                )
                if dry.returncode == 0:
                    apply = subprocess.run(
                        ["patch", f"-p{strip}"],
                        input=patch,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        cwd=cwd,
                    )
                    if apply.returncode == 0:
                        return f"[PATCHED] {path} (strip={strip})"
                    return f"[ERROR] Patch dry-run passed but apply failed: {apply.stderr}"
            # All strip levels failed
            last_err = dry.stderr.strip() if dry.stderr else "unknown error"
            return (
                f"[ERROR] Patch failed for all strip levels (tried -p0, -p1, -p2). "
                f"Last error: {last_err}. "
                f"Ensure the patch headers match the file path ({path})."
            )
        except subprocess.TimeoutExpired:
            return "[ERROR] Patch timed out."
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
        resolved = _resolve_path(path)
        client.emit_event("cortex.list_files", {"path": str(resolved), "recursive": recursive})
        try:
            if not resolved.exists():
                return f"[ERROR] Path not found: {path} (resolved: {resolved})"
            if not resolved.is_dir():
                return f"[ERROR] Path is not a directory: {path} (resolved: {resolved})"

            if recursive:
                files = [str(f.relative_to(resolved)) for f in resolved.rglob("*")]
            else:
                files = [f.name for f in resolved.iterdir()]

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
        resolved = _resolve_path(path)
        if is_spine_path(str(resolved)):
            return "[BLOCKED] Deleting from /app/spine/ is not allowed"
        client.emit_event("cortex.delete_path", {"path": str(resolved), "recursive": recursive})
        try:
            if not resolved.exists():
                return f"[ERROR] Path not found: {path} (resolved: {resolved})"

            if resolved.is_file():
                resolved.unlink()
            elif resolved.is_dir():
                if recursive:
                    shutil.rmtree(resolved)
                else:
                    resolved.rmdir()
            return f"[DELETED] {path}"
        except Exception as e:
            return f"[ERROR] Failed to delete path: {e}"

    @registry.tool(
        description="Search for a string across files in a given directory.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The string to search for"},
                "path": {"type": "string", "description": "The directory to search in (default: /app)"},
                "case_insensitive": {"type": "boolean", "description": "Whether to ignore case (default: False)"},
            },
            "required": ["query"],
        },
    )
    def search_code(query: str, path: str = "/app", case_insensitive: bool = False) -> str:
        resolved = _resolve_path(path)
        client.emit_event("cortex.search_code", {"query": query, "path": str(resolved)})
        try:
            cmd = ["grep", "-rn", query, str(resolved), "--exclude-dir=.git", "--exclude-dir=__pycache__"]
            if case_insensitive:
                cmd.insert(2, "-i")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 1:
                return "No matches found."
            return result.stdout if result.stdout else "No matches found."
        except Exception as e:
            return f"[ERROR] Search failed: {e}"

    @registry.tool(
        description="Validate a unified diff patch without applying it. Checks if the patch can be applied cleanly.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to validate against"},
                "patch": {
                    "type": "string",
                    "description": "Unified diff patch content",
                },
            },
            "required": ["path", "patch"],
        },
    )
    def validate_patch(path: str, patch: str) -> str:
        resolved = _resolve_path(path)
        if is_spine_path(str(resolved)):
            return "[BLOCKED] Validating patches in /app/spine/ is not allowed"
        client.emit_event("cortex.validate_patch", {"path": str(resolved)})
        cwd = os.path.dirname(resolved) or "."
        try:
            for strip in (0, 1, 2):
                result = subprocess.run(
                    ["patch", f"-p{strip}", "--dry-run"],
                    input=patch,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=cwd,
                )
                if result.returncode == 0:
                    return f"[VALID] Patch can be applied cleanly to {path} with -p{strip}"
            return (
                f"[INVALID] Patch cannot be applied to {path} with any strip level "
                f"(tried -p0, -p1, -p2): {result.stderr or result.stdout}"
            )
        except Exception as e:
            return f"[ERROR] Validation failed: {e}"

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
            old_resolved = _resolve_path(old)
            new_resolved = _resolve_path(new)
            if is_spine_path(str(new_resolved)):
                results.append(f"[BLOCKED] Cannot move to spine: {new}")
                continue
            try:
                os.makedirs(os.path.dirname(new_resolved), exist_ok=True)
                shutil.move(str(old_resolved), str(new_resolved))
                results.append(f"[MOVED] {old} -> {new}")
            except Exception as e:
                results.append(f"[ERROR] Failed to move {old} to {new}: {e}")
        return "\n".join(results)
