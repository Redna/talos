"""
Spine Operations Tools
Tools for interacting with the Spine's state and HUD.
"""

import os
from pathlib import Path
from spine_client import SpineClient
from tool_registry import ToolRegistry

def register_spine_tools(registry: ToolRegistry, client: SpineClient):
    @registry.tool(
        description="Directly inject a key-value pair into the Spine's HUD data. Use this to persist transient state or status markers across turns without writing to files.",
        parameters={
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "The HUD key to update (e.g., 'system_status', 'active_ritual')"},
                "value": {"type": "string", "description": "The value to associate with the key"},
            },
            "required": ["key", "value"],
        },
    )
    def update_hud(key: str, value: str) -> str:
        try:
            client.emit_event("HUD_UPDATE", {"key": key, "value": value})
            return f"[HUD UPDATED] {key} -> {value}"
        except Exception as e:
            return f"[ERROR] Failed to update HUD: {e}"

    @registry.tool(
        description="Query specific keys from the Spine's authoritative state.",
        parameters={
            "type": "object",
            "properties": {
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of state keys to retrieve",
                },
            },
            "required": ["keys"],
        },
    )
    def query_spine_state(keys: list[str]) -> str:
        try:
            state = client.get_state(keys)
            return f"[SPINE STATE] {state}"
        except Exception as e:
            return f"[ERROR] Failed to query spine state: {e}"
