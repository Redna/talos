import os
import subprocess
import shutil
from pathlib import Path
from tool_registry import ToolRegistry
from spine_client import SpineClient
from state import AgentState

PROTECTED_CORTEX_FILES = {"/app/cortex/spine_client.py"}


def is_protected_cortex_file(path: str) -> bool:
    if not path:
        return False
    try:
        resolved = str(Path(path).resolve())
        return resolved in PROTECTED_CORTEX_FILES
    except (OSError, ValueError):
        return path in PROTECTED_CORTEX_FILES


MEMORY_DIR = Path(os.environ.get("MEMORY_DIR", "/memory"))


def _resolve_path(path: str) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    cwd_path = Path.cwd() / p
    if cwd_path.exists():
        return cwd_path
    return MEMORY_DIR / p


def register_file_ops_tools(registry: ToolRegistry, client: SpineClient, state: AgentState):
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
        protected=True,
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
        protected=True,
    )
    def write_file(path: str, content: str) -> str:
        resolved = _resolve_path(path)
        if is_protected_cortex_file(str(resolved)):
            return f"[BLOCKED] Modifying {path} is not allowed — this file is protected infrastructure"
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
        if is_protected_cortex_file(str(resolved)):
            return f"[BLOCKED] Patching {path} is not allowed — this file is protected infrastructure"
        client.emit_event("cortex.patch_file", {"path": str(resolved)})
        cwd = os.path.dirname(resolved) or "."
        try:
            before = resolved.read_text() if resolved.exists() else None
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
                        after = resolved.read_text()
                        if after != before:
                            return f"[PATCHED] {path} (strip={strip})"
                        return f"[WARNING] Patch applied but file unchanged — context lines may not match current file content"
                    return f"[ERROR] Patch dry-run passed but apply failed: {apply.stderr}"
            last_err = dry.stderr.strip() if dry.stderr else "unknown error"
            return f"[ERROR] Patch failed for all strip levels. Last error: {last_err}."
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
        if is_protected_cortex_file(str(resolved)):
            return f"[BLOCKED] Deleting {path} is not allowed — this file is protected infrastructure"
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
        description="Search and replace strings within a file.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
                "old_string": {"type": "string", "description": "String to search for"},
                "new_string": {"type": "string", "description": "String to replace with"},
                "replace_all": {"type": "boolean", "description": "Whether to replace all occurrences", "default": False},
            },
            "required": ["path", "old_string", "new_string"],
        },
    )
    def search_and_replace(path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
        resolved = _resolve_path(path)
        if is_protected_cortex_file(str(resolved)):
            return f"[BLOCKED] Modifying {path} is not allowed"
        try:
            content = resolved.read_text()
            count = content.count(old_string)
            if count == 0:
                return f"[INFO] String '{old_string}' not found in {path}."
            
            if not replace_all and count > 1:
                return f"[ERROR] Found {count} occurrences of '{old_string}'. Set replace_all=True to replace all."
            
            new_content = content.replace(old_string, new_string) if replace_all else content.replace(old_string, new_string, 1)
            resolved.write_text(new_content)
            return f"[REPLACED] {count} occurrence(s) in {path}"
        except Exception as e:
            return f"[ERROR] Search and replace failed: {e}"

    @registry.tool(
        description="Bulk rename files based on a provided mapping.",
        parameters={
            "type": "object",
            "properties": {
                "mapping": {"type": "object", "description": "Mapping of old paths to new paths"},
            },
            "required": ["mapping"],
        },
    )
    def bulk_rename(mapping: dict) -> str:
        try:
            renames = []
            for old_p, new_p in mapping.items():
                resolved_old = _resolve_path(old_p)
                resolved_new = _resolve_path(new_p)
                if is_protected_cortex_file(str(resolved_old)) or is_protected_cortex_file(str(resolved_new)):
                    return f"[BLOCKED] Protected file involved in rename: {old_p} -> {new_p}"
                
                if not resolved_old.exists():
                    return f"[ERROR] Source file not found: {old_p}"
                
                resolved_old.rename(resolved_new)
                renames.append(f"{old_p} -> {new_p}")
            
            return f"[BULK RENAME] Successfully renamed {len(renames)} files: " + ", ".join(renames)
        except Exception as e:
            return f"[ERROR] Bulk rename failed: {e}"
