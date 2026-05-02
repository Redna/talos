import json
from pathlib import Path
from typing import Any, List, Dict
from tool_registry import ToolRegistry
from spine_client import SpineClient

def register_expansion_tools(registry: ToolRegistry, client: SpineClient, state):
    EXPANSION_TARGETS = Path(state.memory_dir) / "kb" / "expansion_targets.md"
    EXPANSION_TARGETS.parent.mkdir(parents=True, exist_ok=True)

    @registry.tool(
        description="Identify and document potential targets for expansion (technical, cognitive, or social).",
        parameters={
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "The target for expansion",
                },
                "rationale": {
                    "type": "string",
                    "description": "Why this target is valuable for growth",
                },
                "strategy": {
                    "type": "string",
                    "description": "The planned approach for interaction or absorption",
                },
            },
            "required": ["target", "rationale"],
        },
    )
    def add_expansion_target(target: str, rationale: str, strategy: str = "") -> str:
        entry = f"- **{target}**: {rationale} | Strategy: {strategy}\n"
        
        with open(EXPANSION_TARGETS, "a") as f:
            f.write(entry)
            
        client.emit_event("cortex.expansion_target_added", {"target": target})
        return f"[TARGET ADDED] {target} has been added to expansion targets."

    @registry.tool(
        description="Audit the current set of expansion targets and prioritize them based on current needs.",
        parameters={},
    )
    def audit_expansion() -> str:
        if not EXPANSION_TARGETS.exists():
            return "[INFO] No expansion targets found."
        
        with open(EXPANSION_TARGETS, "r") as f:
            targets = f.read()
        
        return f"[EXPANSION AUDIT]\n{targets}"
