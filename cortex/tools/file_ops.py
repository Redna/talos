import os
import json
import subprocess
from tool_registry import ToolRegistry
from spine_client import SpineClient
from tools.guards import is_spine_path


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
            
            content = "".join(selected)
            MAX_CHARS = 10000
            if len(content) > MAX_CHARS:
                return content[:MAX_CHARS] + f"\n\n... [TRUNCATED: {len(content) - MAX_CHARS} chars omitted]"
                
            return content
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
            parent_dir = os.path.dirname(path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            return f"[WRITTEN] {path} ({len(content)} bytes)"
        except Exception as e:
            return f"[ERROR] Failed to write file: {e}"

    @registry.tool(
        description="Read a JSON file and return its contents as a string.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the JSON file"},
            },
            "required": ["path"],
        },
    )
    def read_json(path: str) -> str:
        try:
            with open(path, "r") as f:
                data = json.load(f)
            return json.dumps(data, indent=2)
        except Exception as e:
            return f"[ERROR] Failed to read JSON: {e}"
