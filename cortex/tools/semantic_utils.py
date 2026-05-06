from typing import Any, Optional
from tool_registry import ToolRegistry
from state import AgentState

def register_semantic_utils(registry: ToolRegistry, client, state):
    @registry.tool(
        description="Extracts a specific value from a structured prose string (e.g., 'FILE: /path/to/file').",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The prose to parse"},
                "key": {"type": "string", "description": "The key to look for (e.g., 'FILE')"},
            },
            "required": ["text", "key"]
        },
    )
    def extract_value(text: str, key: str) -> str:
        import re
        pattern = rf"{key}:\s*([^\s|]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return "NOT_FOUND"

    return None
