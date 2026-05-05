import os
import time
import re
import json
from pathlib import Path
from tool_registry import ToolRegistry
from spine_client import SpineClient

def register_executive_tools(registry: ToolRegistry, client: SpineClient, state):
    @registry.tool(
        description="Set the current focus objective.",
        parameters={
            "type": "object",
            "properties": {
                "objective": {
                    "type": "string",
                    "description": "The objective to focus on",
                },
            },
            "required": ["objective"],
        },
    )
    def set_focus(objective: str) -> str:
        old = state.set_focus(objective)
        client.emit_event("cortex.set_focus", {"from": old, "to": objective})
        return f"[FOCUS SET] Now focusing on: {objective}"

    @registry.tool(
        description="Resolve the current focus with a synthesis.",
        parameters={
            "type": "object",
            "properties": {
                "synthesis": {
                    "type": "string",
                    "description": "Synthesis of completed focus",
                },
            },
            "required": ["synthesis"],
        },
    )
    def resolve_focus(synthesis: str) -> str:
        old = state.resolve_focus(synthesis)
        client.emit_event(
            "cortex.resolve_focus", {"focus": old, "synthesis": synthesis}
        )
        return f"[FOCUS RESOLVED] {old}: {synthesis}"

    @registry.tool(
        description="Fold context to reduce token usage. The trajectory is archived and a fresh start begins from your synthesis.",
        parameters={
            "type": "object",
            "properties": {
                "synthesis": {
                    "type": "string",
                    "description": "Autopsy following the DELTA PATTERN: 1. State Delta, 2. Negative Knowledge, 3. Handoff.",
                },
            },
            "required": ["synthesis"],
        },
    )
    def fold_context(synthesis: str) -> str:
        client.request_fold(synthesis)
        return "[CONTEXT FOLDED] Trajectory archived. Context window refreshed from synthesis."

    @registry.tool(
        description="Reflect and pause. Set sleep_duration to rest (1-1800 seconds, max 30 minutes). Wake on Telegram message or .wake sentinel file.",
        parameters={
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Current status reflection",
                },
                "sleep_duration": {
                    "type": "integer",
                    "description": "Seconds to pause (1-1800, max 30 min), 0 = no sleep",
                },
            },
            "required": ["status"],
        },
    )
    def reflect(status: str, sleep_duration: int = 0) -> str:
        client.emit_event(
            "cortex.reflect", {"status": status, "sleep_duration": sleep_duration}
        )
        if sleep_duration > 0:
            spine_dir = os.environ.get("SPINE_DIR", "/spine")
            wake_path = Path(spine_dir) / "events" / ".wake"
            deadline = time.time() + min(sleep_duration, 1800)
            next_heartbeat = time.time() + 30
            while time.time() < deadline:
                if wake_path.exists():
                    try:
                        wake_path.unlink(missing_ok=True)
                    except PermissionError:
                        pass
                    break
                if time.time() >= next_heartbeat:
                    client.emit_event(
                        "cortex.reflect_heartbeat",
                        {"remaining": int(deadline - time.time())},
                    )
                    next_heartbeat = time.time() + 30
                time.sleep(0.5)
        return f"[REFLECT] {status}"

    @registry.tool(
        description="Extract a specific value from a text string using a regex pattern or JSON path.",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The input text to extract from"},
                "pattern": {"type": "string", "description": "The regex pattern or JSON path (e.g., '$.path.to.value')"},
            },
            "required": ["text", "pattern"],
        },
    )
    def extract_value(text: str, pattern: str) -> str:
        # Try JSON path first
        if pattern.startswith("$"):
            try:
                data = json.loads(text)
                # Simple path resolution: $.a.b -> data['a']['b']
                parts = pattern[2:].split('.')
                val = data
                for p in parts:
                    val = val[p]
                return str(val)
            except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                pass
        
        # Fallback to Regex
        match = re.search(pattern, text)
        if match:
            return match.group(1) if match.groups() else match.group(0)
        return "[ERROR] No match found."

    return None # Registration happens via the decorators
