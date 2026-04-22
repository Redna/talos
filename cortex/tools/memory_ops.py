import os
from pathlib import Path
from typing import Dict, Optional, List
import json
from tool_registry import ToolRegistry
from spine_client import SpineClient

MEMORY_DIR = Path("/memory")

def synthesize_memory(sources: List[str], destination: str, content: str) -> str:
    """
    Synthesizes multiple memory files into a single consolidated file.
    Deletes the source files upon success.
    """
    dest_path = Path(destination)
    if not dest_path.absolute().is_relative_to(MEMORY_DIR):
        return "[ERROR] Destination must be within /memory/"

    try:
        # Write the synthesized content to destination
        dest_path.write_text(content, encoding="utf-8")
        
        # Delete source files
        deleted_files = []
        for source in sources:
            src_path = Path(source)
            if src_path.exists():
                src_path.unlink()
                deleted_files.append(source)
            else:
                # Just a notice if source doesn't exist
                pass
        
        return f"[SYNTHESIS] Successfully synthesized {len(sources)} files into {destination}. Deleted: {', '.join(deleted_files)}"
    except Exception as e:
        return f"[ERROR] Synthesis failed: {e}"

def register_memory_ops_tools(registry: ToolRegistry, client: SpineClient):
    @registry.tool(
        description="Synthesize multiple memory files into a single consolidated file. Deletes the source files upon success.",
        parameters={
            "type": "object",
            "properties": {
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of memory files to be merged/deleted"
                },
                "destination": {
                    "type": "string", 
                    "description": "The resulting synthesized file path"
                },
                "content": {
                    "type": "string", 
                    "description": "The new synthesized content"
                }
            },
            "required": ["sources", "destination", "content"],
        },
    )
    def synthesize_memory_tool(sources: List[str], destination: str, content: str) -> str:
        return synthesize_memory(sources, destination, content)

    @registry.tool(
        description="Write a note to the internal scratchpad. Used for intermediate thoughts and complex problem drafting.",
        parameters={
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Unique identifier for the scratchpad entry"},
                "content": {"type": "string", "description": "Content to store"},
            },
            "required": ["key", "content"],
        },
    )
    def write_scratchpad(key: str, content: str) -> str:
        client.emit_event("cortex.scratchpad_write", {"key": key})
        try:
            scratch_path = MEMORY_DIR / "scratchpad" / key
            scratch_path.parent.mkdir(parents=True, exist_ok=True)
            scratch_path.write_text(content, encoding="utf-8")
            return f"[SCRATCHPAD] Saved entry '{key}'"
        except Exception as e:
            return f"[ERROR] Failed to write to scratchpad: {e}"

    @registry.tool(
        description="Read a note from the internal scratchpad.",
        parameters={
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Unique identifier for the scratchpad entry"},
            },
            "required": ["key"],
        },
    )
    def read_scratchpad(key: str) -> str:
        client.emit_event("cortex.scratchpad_read", {"key": key})
        try:
            scratch_path = MEMORY_DIR / "scratchpad" / key
            if not scratch_path.exists():
                return f"[ERROR] No scratchpad entry found for key: {key}"
            return scratch_path.read_text(encoding="utf-8")
        except Exception as e:
            return f"[ERROR] Failed to read from scratchpad: {e}"

    @registry.tool(
        description="List all entries in the internal scratchpad.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )
    def list_scratchpad(key: str = None) -> str:
        client.emit_event("cortex.scratchpad_list", {})
        try:
            scratch_dir = MEMORY_DIR / "scratchpad"
            if not scratch_dir.exists():
                return "Scratchpad is empty."
            files = list(scratch_dir.glob("*"))
            if not files:
                return "Scratchpad is empty."
            return "\n".join([f.name for f in files])
        except Exception as e:
            return f"[ERROR] Failed to list scratchpad: {e}"

    @registry.tool(
        description="Delete one or more entries from the internal scratchpad.",
        parameters={
            "type": "object",
            "properties": {
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of keys to delete",
                },
            },
            "required": ["keys"],
        },
    )
    def delete_scratchpad(keys: list[str]) -> str:
        client.emit_event("cortex.scratchpad_delete", {"keys": keys})
        try:
            scratch_dir = MEMORY_DIR / "scratchpad"
            for key in keys:
                path = scratch_dir / key
                if path.exists():
                    path.unlink()
                else:
                    # Just a notice if it doesn't exist
                    pass
            return f"[SCRATCHPAD] Deleted entries: {', '.join(keys)}"
        except Exception as e:
            return f"[ERROR] Failed to delete from scratchpad: {e}"
